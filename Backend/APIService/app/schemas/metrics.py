from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PerStreamMetrics(BaseModel):
    """Per-stream breakdown item aligned with the OpenAPI spec."""

    stream_id: str = Field(..., description="Unique stream identifier.")
    rx_gbps: float = Field(..., description="Receive throughput for this stream (Gbps).")
    tx_gbps: float = Field(..., description="Transmit throughput for this stream (Gbps).")
    frame_size: int = Field(..., description="Frame size (bytes) for this stream.")


class SeriesSample(BaseModel):
    """Time series sample aligned with the OpenAPI spec.

    This model is kept minimal and stable so it can later map to a DB table row.
    """

    ts: datetime = Field(..., description="Sample timestamp (RFC3339).")
    rx_gbps: float = Field(..., description="Receive throughput in Gbps.")
    tx_gbps: float = Field(..., description="Transmit throughput in Gbps.")
    loss_pct: float = Field(..., description="Packet loss percentage.")
    compensated: bool = Field(..., description="True if value was gap-compensated (hold-last).")
    reason: Optional[str] = Field(default=None, description="Optional compensation reason (nullable).")


class CurrentMetrics(BaseModel):
    """Current aggregated metrics snapshot aligned with the OpenAPI spec + compensation hints."""

    ts: datetime = Field(..., description="Sample timestamp (RFC3339).")
    rx_gbps: float = Field(..., description="Receive throughput in Gbps.")
    tx_gbps: float = Field(..., description="Transmit throughput in Gbps.")
    loss_pct: float = Field(..., description="Packet loss percentage.")
    error_counters: Dict[str, float] = Field(..., description="Error counters keyed by error type/name.")
    per_stream: Optional[List[PerStreamMetrics]] = Field(
        default=None,
        description="Optional per-stream breakdown.",
    )
    sequence: int = Field(..., description="Monotonically increasing sequence number.")

    # Not required by existing OpenAPI snippet, but requested for real pipeline behavior.
    compensated: bool = Field(False, description="True if snapshot was gap-compensated (hold-last).")
    reason: Optional[str] = Field(default=None, description="Optional compensation reason (nullable).")

    model_config = {"extra": "forbid"}
