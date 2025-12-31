from __future__ import annotations

from typing import Optional
from uuid import UUID

from app.repositories.metrics_repository import MetricsRepository
from app.schemas.metrics import CurrentMetrics
from app.schemas.envelopes import now_utc


class MetricsService:
    """Service responsible for serving aggregated metrics snapshots from storage."""

    def __init__(self, repo: MetricsRepository) -> None:
        self._repo = repo

    # PUBLIC_INTERFACE
    def get_current_metrics(self, test_run_id: Optional[UUID], include_per_stream: bool) -> CurrentMetrics:
        """Return the latest computed metrics snapshot.

        Args:
            test_run_id: Optional test run to scope metrics for (currently unused).
            include_per_stream: Whether to include per-stream breakdown.

        Returns:
            CurrentMetrics: latest snapshot; if unavailable yet, returns a safe zero snapshot.
        """
        _ = test_run_id  # reserved for future scoping when test runs are implemented

        current = self._repo.get_current()
        if current is None:
            return CurrentMetrics(
                ts=now_utc(),
                rx_gbps=0.0,
                tx_gbps=0.0,
                loss_pct=0.0,
                error_counters={},
                per_stream=[] if include_per_stream else None,
                sequence=0,
                compensated=False,
                reason="no_samples_yet",
            )

        if include_per_stream:
            return current

        # Return a copy without per-stream details to reduce payload size.
        return CurrentMetrics(
            ts=current.ts,
            rx_gbps=current.rx_gbps,
            tx_gbps=current.tx_gbps,
            loss_pct=current.loss_pct,
            error_counters=current.error_counters,
            per_stream=None,
            sequence=current.sequence,
            compensated=current.compensated,
            reason=current.reason,
        )
