from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from app.schemas.scenarios import Scenario


@dataclass
class _ScenarioRecord:
    scenario: Scenario


class ScenariosRepository:
    """Repository abstraction for scenarios."""

    # PUBLIC_INTERFACE
    def list(self) -> List[Scenario]:
        """List all scenarios."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def create(self, scenario: Scenario) -> None:
        """Create a scenario."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def get(self, scenario_id: UUID) -> Optional[Scenario]:
        """Get a scenario by id."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def update(self, scenario_id: UUID, scenario: Scenario) -> None:
        """Update an existing scenario."""
        raise NotImplementedError


class InMemoryScenariosRepository(ScenariosRepository):
    """Thread-safe in-memory scenario storage."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: Dict[UUID, _ScenarioRecord] = {}

    # PUBLIC_INTERFACE
    def list(self) -> List[Scenario]:
        """List all scenarios."""
        with self._lock:
            items = [rec.scenario for rec in self._items.values()]
        # Stable sort for deterministic docs/UX: created_at desc then name
        items.sort(key=lambda s: (s.created_at, s.name), reverse=True)
        return items

    # PUBLIC_INTERFACE
    def create(self, scenario: Scenario) -> None:
        """Create a scenario."""
        with self._lock:
            self._items[scenario.id] = _ScenarioRecord(scenario=scenario)

    # PUBLIC_INTERFACE
    def get(self, scenario_id: UUID) -> Optional[Scenario]:
        """Get a scenario by id."""
        with self._lock:
            rec = self._items.get(scenario_id)
            return rec.scenario if rec else None

    # PUBLIC_INTERFACE
    def update(self, scenario_id: UUID, scenario: Scenario) -> None:
        """Update an existing scenario."""
        with self._lock:
            self._items[scenario_id] = _ScenarioRecord(scenario=scenario)
