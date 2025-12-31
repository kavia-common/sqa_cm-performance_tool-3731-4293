from __future__ import annotations

from datetime import datetime
from typing import List, Literal
from uuid import UUID

from pydantic import BaseModel, Field


ReportFormat = Literal["csv", "json", "pdf"]


class ReportMeta(BaseModel):
    """Report metadata."""

    id: UUID = Field(..., description="Report id.")
    test_run_id: UUID = Field(..., description="Test run id.")
    generated_at: datetime = Field(..., description="Generated timestamp (RFC3339).")
    format: ReportFormat = Field(..., description="Export format.")
    download_url: str = Field(..., description="URL to download the report.", pattern=r"^https?://|^/")
    checksum: str = Field(..., description="Checksum string (opaque).")

    model_config = {"extra": "forbid"}


class ReportExportRequest(BaseModel):
    """Request to export reports for a test run in one or more formats."""

    test_run_id: UUID = Field(..., description="Test run id.")
    formats: List[ReportFormat] = Field(..., description="One or more formats to export.")

    model_config = {"extra": "forbid"}


class Accepted(BaseModel):
    """Generic accepted payload for queued async work."""

    export_id: UUID = Field(..., description="Export job id.")
    state: Literal["queued"] = Field("queued", description="Queue state.")

    model_config = {"extra": "forbid"}
