from __future__ import annotations

from datetime import timedelta
from typing import Optional
from uuid import UUID, uuid4

from app.schemas.envelopes import now_utc
from app.schemas.tests import TestStartAccepted, TestStartRequest, TestStatus, TestStopAccepted, TestStopRequest
from app.repositories.tests_repository import TestsRepository


class TestsService:
    """Service for test lifecycle control (in-memory simulation)."""

    def __init__(self, repo: TestsRepository) -> None:
        self._repo = repo

    def _get_or_404(self, test_run_id: UUID) -> Optional[TestStatus]:
        return self._repo.get(test_run_id)

    # PUBLIC_INTERFACE
    def start(self, req: TestStartRequest) -> TestStartAccepted:
        """Start a new test run and return an accepted response."""
        _ = req  # scenario validation could be wired later (TODO)

        test_run_id = uuid4()
        status = TestStatus(
            id=test_run_id,
            status="pending",
            started_at=now_utc(),
            completed_at=None,
            reason=None,
        )
        self._repo.create(status)

        # Simulation: immediately flip to "running" so UI/clients see progression without background tasks.
        self._repo.update(
            test_run_id,
            TestStatus(
                id=test_run_id,
                status="running",
                started_at=status.started_at,
                completed_at=None,
                reason=None,
            ),
        )

        return TestStartAccepted(test_run_id=test_run_id, state="starting")

    # PUBLIC_INTERFACE
    def stop(self, req: TestStopRequest) -> TestStopAccepted:
        """Request stopping an existing test run and return accepted response."""
        existing = self._repo.get(req.test_run_id)
        if existing is None:
            raise KeyError("test_run_not_found")

        # Simulation: mark as completed shortly after stop is requested.
        completed_at = now_utc()
        self._repo.update(
            req.test_run_id,
            TestStatus(
                id=req.test_run_id,
                status="completed" if existing.status != "failed" else "failed",
                started_at=existing.started_at,
                completed_at=completed_at,
                reason=existing.reason,
            ),
        )
        return TestStopAccepted(test_run_id=req.test_run_id, state="stopping")

    # PUBLIC_INTERFACE
    def get_status(self, test_run_id: UUID) -> TestStatus:
        """Return current status for a test run (with small simulated completion if stale)."""
        status = self._repo.get(test_run_id)
        if status is None:
            raise KeyError("test_run_not_found")

        # Optional simulation: if running for > 60s, mark completed.
        if status.status == "running":
            if (now_utc() - status.started_at) > timedelta(seconds=60):
                status = TestStatus(
                    id=status.id,
                    status="completed",
                    started_at=status.started_at,
                    completed_at=now_utc(),
                    reason=None,
                )
                self._repo.update(test_run_id, status)

        return status
