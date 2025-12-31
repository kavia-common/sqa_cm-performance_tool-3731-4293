from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from app.schemas.tests import TestStatus


@dataclass
class _TestRunRecord:
    status: TestStatus


class TestsRepository:
    """Repository abstraction for test runs."""

    # PUBLIC_INTERFACE
    def create(self, status: TestStatus) -> None:
        """Create a new test run status record."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def get(self, test_run_id: UUID) -> Optional[TestStatus]:
        """Get test run status by id."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def update(self, test_run_id: UUID, status: TestStatus) -> None:
        """Update an existing test run status."""
        raise NotImplementedError


class InMemoryTestsRepository(TestsRepository):
    """Thread-safe in-memory store for test runs."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runs: Dict[UUID, _TestRunRecord] = {}

    # PUBLIC_INTERFACE
    def create(self, status: TestStatus) -> None:
        """Create a new test run status record."""
        with self._lock:
            self._runs[status.id] = _TestRunRecord(status=status)

    # PUBLIC_INTERFACE
    def get(self, test_run_id: UUID) -> Optional[TestStatus]:
        """Get test run status by id."""
        with self._lock:
            rec = self._runs.get(test_run_id)
            return rec.status if rec else None

    # PUBLIC_INTERFACE
    def update(self, test_run_id: UUID, status: TestStatus) -> None:
        """Update an existing test run status."""
        with self._lock:
            if test_run_id not in self._runs:
                # Maintain repo invariants; callers should check existence.
                self._runs[test_run_id] = _TestRunRecord(status=status)
            else:
                self._runs[test_run_id].status = status
