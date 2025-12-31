from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from app.clients.xena_client import DeviceCountersSnapshot, XenaClient
from app.repositories.metrics_repository import MetricsRepository
from app.schemas.metrics import CurrentMetrics, PerStreamMetrics, SeriesSample
from app.services.observability import Observability

logger = logging.getLogger("app.metrics")


@dataclass
class _LastState:
    snapshot: DeviceCountersSnapshot
    sequence: int


class MetricsPipeline:
    """Background metrics poller + aggregator.

    - Polls raw counters from a Xena client at a configured interval
    - Aggregates into rx_gbps/tx_gbps/loss_pct plus per-stream breakdown
    - Applies compensation when gaps detected (hold-last)
    - Persists current snapshot + rolling series samples via repository
    """

    def __init__(
        self,
        repo: MetricsRepository,
        client: XenaClient,
        poll_interval_ms: int,
        max_streams: int,
        obs: Observability,
    ) -> None:
        self._repo = repo
        self._client = client
        self._poll_interval_s = max(0.2, poll_interval_ms / 1000.0)
        self._max_streams = max(1, max_streams)
        self._obs = obs

        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._last: Optional[_LastState] = None

    # PUBLIC_INTERFACE
    async def start(self) -> None:
        """Start the background polling task."""
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop(), name="metrics-poll-loop")

    # PUBLIC_INTERFACE
    async def stop(self) -> None:
        """Stop the background polling task."""
        self._stop_event.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            started = datetime.utcnow()
            try:
                self._poll_once()
                self._obs.incr("polls_total", 1)
            except Exception:
                self._obs.incr("polls_failed_total", 1)
                logger.exception("metrics poll failed")
            elapsed = (datetime.utcnow() - started).total_seconds()
            sleep_for = max(0.0, self._poll_interval_s - elapsed)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=sleep_for)
            except asyncio.TimeoutError:
                pass

    def _poll_once(self) -> None:
        raw = self._client.fetch_counters(max_streams=self._max_streams)

        compensated = False
        reason: Optional[str] = None

        if self._last is None:
            # First snapshot: cannot compute deltas; treat as 0 but store as baseline.
            seq = 1
            current = CurrentMetrics(
                ts=raw.ts,
                rx_gbps=0.0,
                tx_gbps=0.0,
                loss_pct=0.0,
                error_counters={},
                per_stream=[],
                sequence=seq,
                compensated=False,
                reason=None,
            )
            self._repo.set_current(current)
            self._repo.append_sample(
                SeriesSample(ts=current.ts, rx_gbps=current.rx_gbps, tx_gbps=current.tx_gbps, loss_pct=current.loss_pct, compensated=False, reason=None)
            )
            self._last = _LastState(snapshot=raw, sequence=seq)
            self._obs.set_gauge("current_rx_gbps", current.rx_gbps)
            self._obs.set_gauge("current_tx_gbps", current.tx_gbps)
            self._obs.set_gauge("current_loss_pct", current.loss_pct)
            self._obs.log_json(logger, "metrics_poll", {"sequence": seq, "compensated": False, "rx_gbps": 0.0, "tx_gbps": 0.0, "loss_pct": 0.0})
            return

        prev_raw = self._last.snapshot
        prev_seq = self._last.sequence

        dt = (raw.ts - prev_raw.ts).total_seconds()
        if dt <= 0.0:
            # Clock went backwards or duplicate timestamp: compensate (hold-last).
            compensated = True
            reason = "non_monotonic_timestamp"
        elif dt > (self._poll_interval_s * 1.8):
            # Detected a gap: compensate (hold-last).
            compensated = True
            reason = f"gap_detected_dt={dt:.3f}s"

        latest_current = self._repo.get_current()

        if compensated and latest_current is not None:
            seq = prev_seq + 1
            current = CurrentMetrics(
                ts=raw.ts,
                rx_gbps=latest_current.rx_gbps,
                tx_gbps=latest_current.tx_gbps,
                loss_pct=latest_current.loss_pct,
                error_counters=latest_current.error_counters,
                per_stream=latest_current.per_stream,
                sequence=seq,
                compensated=True,
                reason=reason,
            )
            self._repo.set_current(current)
            self._repo.append_sample(
                SeriesSample(ts=current.ts, rx_gbps=current.rx_gbps, tx_gbps=current.tx_gbps, loss_pct=current.loss_pct, compensated=True, reason=reason)
            )
            self._last = _LastState(snapshot=raw, sequence=seq)
            self._obs.incr("polls_compensated_total", 1)
            self._obs.set_gauge("current_rx_gbps", current.rx_gbps)
            self._obs.set_gauge("current_tx_gbps", current.tx_gbps)
            self._obs.set_gauge("current_loss_pct", current.loss_pct)
            self._obs.log_json(
                logger,
                "metrics_poll",
                {"sequence": seq, "compensated": True, "reason": reason, "rx_gbps": current.rx_gbps, "tx_gbps": current.tx_gbps, "loss_pct": current.loss_pct},
            )
            return

        # Normal delta aggregation
        per_stream = []
        total_rx_bps = 0.0
        total_tx_bps = 0.0
        total_rx_frames = 0
        total_tx_frames = 0
        error_counters: Dict[str, float] = {}

        # Index prev streams by id for stable deltas
        prev_by_id = {s.stream_id: s for s in prev_raw.streams}

        for s in raw.streams:
            prev_s = prev_by_id.get(s.stream_id)
            if prev_s is None:
                continue

            rx_bytes_delta = max(0, s.rx_bytes_total - prev_s.rx_bytes_total)
            tx_bytes_delta = max(0, s.tx_bytes_total - prev_s.tx_bytes_total)
            rx_frames_delta = max(0, s.rx_frames_total - prev_s.rx_frames_total)
            tx_frames_delta = max(0, s.tx_frames_total - prev_s.tx_frames_total)

            rx_bps = (rx_bytes_delta * 8.0) / dt
            tx_bps = (tx_bytes_delta * 8.0) / dt

            total_rx_bps += rx_bps
            total_tx_bps += tx_bps
            total_rx_frames += rx_frames_delta
            total_tx_frames += tx_frames_delta

            per_stream.append(
                PerStreamMetrics(
                    stream_id=s.stream_id,
                    rx_gbps=rx_bps / 1e9,
                    tx_gbps=tx_bps / 1e9,
                    frame_size=s.frame_size,
                )
            )

            # Accumulate error counters as rates/s for now (float)
            for k, v in s.error_counters_total.items():
                # In sim client these are per-poll bumps; treat as total events in this interval.
                error_counters[k] = error_counters.get(k, 0.0) + float(v)

        loss_pct = 0.0
        if total_tx_frames > 0:
            lost = max(0, total_tx_frames - total_rx_frames)
            loss_pct = (lost / total_tx_frames) * 100.0

        seq = prev_seq + 1
        current = CurrentMetrics(
            ts=raw.ts,
            rx_gbps=total_rx_bps / 1e9,
            tx_gbps=total_tx_bps / 1e9,
            loss_pct=loss_pct,
            error_counters=error_counters,
            per_stream=per_stream,
            sequence=seq,
            compensated=False,
            reason=None,
        )

        self._repo.set_current(current)
        self._repo.append_sample(
            SeriesSample(ts=current.ts, rx_gbps=current.rx_gbps, tx_gbps=current.tx_gbps, loss_pct=current.loss_pct, compensated=False, reason=None)
        )
        self._last = _LastState(snapshot=raw, sequence=seq)

        self._obs.set_gauge("current_rx_gbps", current.rx_gbps)
        self._obs.set_gauge("current_tx_gbps", current.tx_gbps)
        self._obs.set_gauge("current_loss_pct", current.loss_pct)

        self._obs.log_json(
            logger,
            "metrics_poll",
            {
                "sequence": seq,
                "compensated": False,
                "rx_gbps": round(current.rx_gbps, 4),
                "tx_gbps": round(current.tx_gbps, 4),
                "loss_pct": round(current.loss_pct, 4),
                "streams": len(per_stream),
            },
        )
