from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


ScenarioType = Literal["constant", "burst", "multi_stream", "mtu_variation"]


class Scenario(BaseModel):
    """Scenario definition."""

    id: UUID = Field(..., description="Scenario id.")
    name: str = Field(..., description="Scenario name.")
    version: int = Field(..., description="Scenario version (monotonic).")
    type: ScenarioType = Field(..., description="Scenario type discriminator.")
    params: Dict[str, Any] = Field(..., description="Scenario parameter object.")
    tags: Optional[List[str]] = Field(default=None, description="Optional tags.")
    description: Optional[str] = Field(default=None, description="Optional description.")
    created_at: datetime = Field(..., description="Creation timestamp (RFC3339).")

    model_config = {"extra": "forbid"}


class ScenarioCreateRequest(BaseModel):
    """Request body to create a scenario."""

    name: str = Field(..., description="Scenario name.")
    type: ScenarioType = Field(..., description="Scenario type discriminator.")
    params: Dict[str, Any] = Field(..., description="Scenario parameter object.")
    tags: Optional[List[str]] = Field(default=None, description="Optional tags.")
    description: Optional[str] = Field(default=None, description="Optional description.")

    model_config = {"extra": "forbid"}


class ScenarioUpdateRequest(BaseModel):
    """Partial update request for a scenario.

    PATCH is treated as a versioned update: it creates a new version.
    """

    name: Optional[str] = Field(default=None, description="Optional updated name.")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Optional updated parameters.")
    tags: Optional[List[str]] = Field(default=None, description="Optional updated tags.")

    model_config = {"extra": "forbid"}


class ScenarioVersion(BaseModel):
    """Response payload containing new version info after update."""

    id: UUID = Field(..., description="Scenario id.")
    version: int = Field(..., description="New scenario version.")

    model_config = {"extra": "forbid"}
