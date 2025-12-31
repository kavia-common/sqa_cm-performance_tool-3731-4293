from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TestStartRequest(BaseModel):
    """Request body for starting a test run."""

    scenario_id: str = Field(..., description="Scenario id to execute.")
    overrides: Optional[Dict[str, Any]] = Field(default=None, description="Optional parameter overrides.")
    ports: Optional[Dict[str, Any]] = Field(default=None, description="Optional port mapping/config.")
    labels: Optional[Dict[str, Any]] = Field(default=None, description="Optional labels for the run.")

    model_config = {"extra": "forbid"}


class TestStartAccepted(BaseModel):
    """Response payload acknowledging test start was accepted."""

    test_run_id: UUID = Field(..., description="Created test run ID.")
    state: Literal["starting"] = Field("starting", description="Lifecycle state (starting).")

    model_config = {"extra": "forbid"}


class TestStopRequest(BaseModel):
    """Request body for stopping a test run."""

    test_run_id: UUID = Field(..., description="Test run ID to stop.")

    model_config = {"extra": "forbid"}


class TestStopAccepted(BaseModel):
    """Response payload acknowledging test stop was accepted."""

    test_run_id: UUID = Field(..., description="Test run ID to stop.")
    state: Literal["stopping"] = Field("stopping", description="Lifecycle state (stopping).")

    model_config = {"extra": "forbid"}


class TestStatus(BaseModel):
    """Status model for a test run."""

    id: UUID = Field(..., description="Test run id.")
    status: Literal["pending", "running", "completed", "failed"] = Field(..., description="Current state.")
    started_at: datetime = Field(..., description="Start timestamp (RFC3339).")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp (RFC3339) if finished.")
    reason: Optional[str] = Field(default=None, description="Optional reason if failed or stopped.")

    model_config = {"extra": "forbid"}
