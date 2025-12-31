from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Dict, Optional
from uuid import UUID

from app.schemas.reports import ReportMeta


@dataclass
class _ExportJob:
    test_run_id: UUID


class ReportsRepository:
    """Repository abstraction for reports metadata and export jobs."""

    # PUBLIC_INTERFACE
    def get_latest(self, test_run_id: UUID) -> Optional[ReportMeta]:
        """Get latest report metadata for a test run."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def set_latest(self, test_run_id: UUID, report: ReportMeta) -> None:
        """Set latest report metadata for a test run."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def create_export_job(self, export_id: UUID, test_run_id: UUID) -> None:
        """Create an export job record."""
        raise NotImplementedError


class InMemoryReportsRepository(ReportsRepository):
    """Thread-safe in-memory store for report metadata and export jobs."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latest_by_run: Dict[UUID, ReportMeta] = {}
        self._exports: Dict[UUID, _ExportJob] = {}

    # PUBLIC_INTERFACE
    def get_latest(self, test_run_id: UUID) -> Optional[ReportMeta]:
        """Get latest report metadata for a test run."""
        with self._lock:
            return self._latest_by_run.get(test_run_id)

    # PUBLIC_INTERFACE
    def set_latest(self, test_run_id: UUID, report: ReportMeta) -> None:
        """Set latest report metadata for a test run."""
        with self._lock:
            self._latest_by_run[test_run_id] = report

    # PUBLIC_INTERFACE
    def create_export_job(self, export_id: UUID, test_run_id: UUID) -> None:
        """Create an export job record."""
        with self._lock:
            self._exports[export_id] = _ExportJob(test_run_id=test_run_id)
