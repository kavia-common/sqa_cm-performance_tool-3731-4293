from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import Response


@dataclass
class PipelineStats:
    """In-process counters/gauges for the metrics pipeline (Prometheus-ready text format)."""

    polls_total: int = 0
    polls_failed_total: int = 0
    polls_compensated_total: int = 0
    current_rx_gbps: float = 0.0
    current_tx_gbps: float = 0.0
    current_loss_pct: float = 0.0


class Observability:
    """Observability helper: structured logs and a minimal Prometheus scrape output."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stats = PipelineStats()

    def incr(self, field: str, by: int = 1) -> None:
        with self._lock:
            setattr(self._stats, field, getattr(self._stats, field) + by)

    def set_gauge(self, field: str, value: float) -> None:
        with self._lock:
            setattr(self._stats, field, value)

    def snapshot(self) -> PipelineStats:
        with self._lock:
            return PipelineStats(**self._stats.__dict__)

    # PUBLIC_INTERFACE
    def render_prometheus_text(self) -> str:
        """Render pipeline stats in Prometheus text exposition format."""
        s = self.snapshot()
        lines = [
            "# HELP metrics_polls_total Total poll cycles executed.",
            "# TYPE metrics_polls_total counter",
            f"metrics_polls_total {s.polls_total}",
            "# HELP metrics_polls_failed_total Total poll cycles that failed.",
            "# TYPE metrics_polls_failed_total counter",
            f"metrics_polls_failed_total {s.polls_failed_total}",
            "# HELP metrics_polls_compensated_total Total poll cycles where compensation was applied.",
            "# TYPE metrics_polls_compensated_total counter",
            f"metrics_polls_compensated_total {s.polls_compensated_total}",
            "# HELP metrics_current_rx_gbps Current rx throughput in Gbps.",
            "# TYPE metrics_current_rx_gbps gauge",
            f"metrics_current_rx_gbps {s.current_rx_gbps}",
            "# HELP metrics_current_tx_gbps Current tx throughput in Gbps.",
            "# TYPE metrics_current_tx_gbps gauge",
            f"metrics_current_tx_gbps {s.current_tx_gbps}",
            "# HELP metrics_current_loss_pct Current loss percent.",
            "# TYPE metrics_current_loss_pct gauge",
            f"metrics_current_loss_pct {s.current_loss_pct}",
        ]
        return "\n".join(lines) + "\n"

    # PUBLIC_INTERFACE
    def log_json(self, logger, event: str, fields: Dict) -> None:
        """Emit a structured JSON log event."""
        payload = {"event": event, **fields}
        logger.info(json.dumps(payload, default=str))


# PUBLIC_INTERFACE
def write_prometheus_response(obs: Observability) -> Response:
    """Create a FastAPI response containing Prometheus text metrics."""
    return Response(content=obs.render_prometheus_text(), media_type="text/plain; version=0.0.4")
