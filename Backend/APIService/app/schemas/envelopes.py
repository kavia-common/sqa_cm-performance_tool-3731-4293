from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.metrics import CurrentMetrics
from app.schemas.tests import TestStartAccepted, TestStopAccepted, TestStatus
from app.schemas.scenarios import Scenario, ScenarioVersion
from app.schemas.reports import ReportMeta, Accepted


class Error(BaseModel):
    """Error payload per OpenAPI spec."""

    code: str = Field(..., description="Stable error code identifier.")
    message: str = Field(..., description="Human-readable error message.")
    details: Optional[Any] = Field(
        default=None,
        description="Optional error details: object, array, or null.",
    )


class EnvelopeOk(BaseModel):
    """OK envelope per OpenAPI spec."""

    status: Literal["ok"] = Field("ok", description="Envelope status discriminator.")
    data: Optional[Any] = Field(default=None, description="Payload data (nullable).")

    model_config = {"extra": "forbid"}


class EnvelopeError(BaseModel):
    """Error envelope per OpenAPI spec."""

    status: Literal["error"] = Field("error", description="Envelope status discriminator.")
    error: Error = Field(..., description="Error payload.")

    model_config = {"extra": "forbid"}


class HealthData(BaseModel):
    """Health payload per OpenAPI spec."""

    uptime_s: float = Field(..., description="Service uptime in seconds.")
    version: str = Field(..., description="Service version string.")
    db: Literal["ok", "degraded", "down"] = Field(..., description="Database health.")
    xena: Literal["ok", "degraded", "down"] = Field(..., description="Xena health.")


class ReadyData(BaseModel):
    """Readiness payload per OpenAPI spec."""

    ready: bool = Field(..., description="Whether the service is ready to serve traffic.")


class EnvelopeCurrentMetrics(EnvelopeOk):
    """EnvelopeOk specialized for CurrentMetrics."""

    data: CurrentMetrics = Field(..., description="Current metrics payload.")


class EnvelopeHealth(EnvelopeOk):
    """EnvelopeOk specialized for health response."""

    data: HealthData = Field(..., description="Health status payload.")


class EnvelopeReady(EnvelopeOk):
    """EnvelopeOk specialized for readiness response."""

    data: ReadyData = Field(..., description="Readiness status payload.")


class EnvelopeTestStartAccepted(EnvelopeOk):
    """EnvelopeOk specialized for TestStartAccepted."""

    data: TestStartAccepted = Field(..., description="Accepted test start payload.")


class EnvelopeTestStopAccepted(EnvelopeOk):
    """EnvelopeOk specialized for TestStopAccepted."""

    data: TestStopAccepted = Field(..., description="Accepted test stop payload.")


class EnvelopeTestStatus(EnvelopeOk):
    """EnvelopeOk specialized for TestStatus."""

    data: TestStatus = Field(..., description="Test run status payload.")


class EnvelopeScenarioList(EnvelopeOk):
    """EnvelopeOk specialized for listing scenarios."""

    data: List[Scenario] = Field(..., description="List of scenarios.")


class EnvelopeScenario(EnvelopeOk):
    """EnvelopeOk specialized for a single scenario."""

    data: Scenario = Field(..., description="Scenario payload.")


class EnvelopeScenarioVersion(EnvelopeOk):
    """EnvelopeOk specialized for scenario version response (PATCH)."""

    data: ScenarioVersion = Field(..., description="Scenario id and updated version.")


class EnvelopeReportMeta(EnvelopeOk):
    """EnvelopeOk specialized for report metadata."""

    data: ReportMeta = Field(..., description="Report metadata payload.")


class EnvelopeAccepted(EnvelopeOk):
    """EnvelopeOk specialized for Accepted."""

    data: Accepted = Field(..., description="Accepted queued job payload.")


# PUBLIC_INTERFACE
def now_utc() -> datetime:
    """Utility for generating RFC3339 timestamps in UTC."""
    return datetime.now(timezone.utc)
