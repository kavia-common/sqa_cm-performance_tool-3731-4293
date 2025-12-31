from __future__ import annotations

from typing import Optional
from uuid import UUID

from app.schemas.envelopes import CurrentMetrics, now_utc


class MetricsService:
    """Service responsible for providing metrics data.

    This is placeholder logic; it will be replaced by Xena polling + aggregation.
    """

    # PUBLIC_INTERFACE
    def get_current_metrics(self, test_run_id: Optional[UUID], include_per_stream: bool) -> CurrentMetrics:
        """Return current aggregated metrics.

        Args:
            test_run_id: Optional test run to scope metrics for.
            include_per_stream: Whether to include per-stream breakdown.

        Returns:
            CurrentMetrics: placeholder metrics snapshot aligned with OpenAPI schema.
        """
        # Placeholder values; future implementation will query cache/collector.
        metrics = CurrentMetrics(
            ts=now_utc(),
            rx_gbps=0.0,
            tx_gbps=0.0,
            loss_pct=0.0,
            error_counters={},
            sequence=1,
            per_stream=[] if include_per_stream else None,
        )
        return metrics
