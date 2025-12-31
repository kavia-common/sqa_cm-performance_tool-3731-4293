from __future__ import annotations

import hashlib
from uuid import UUID, uuid4

from app.schemas.envelopes import now_utc
from app.schemas.reports import Accepted, ReportExportRequest, ReportMeta
from app.repositories.reports_repository import ReportsRepository


class ReportsService:
    """Service for report latest lookup and export queue simulation."""

    def __init__(self, repo: ReportsRepository) -> None:
        self._repo = repo

    def _fake_checksum(self, report_id: UUID) -> str:
        return hashlib.sha256(str(report_id).encode("utf-8")).hexdigest()

    # PUBLIC_INTERFACE
    def get_latest(self, test_run_id: UUID) -> ReportMeta:
        """Get latest report for a test run."""
        report = self._repo.get_latest(test_run_id)
        if report is None:
            raise KeyError("report_not_found")
        return report

    # PUBLIC_INTERFACE
    def export(self, req: ReportExportRequest) -> Accepted:
        """Queue a report export job and create 'latest report' metadata."""
        export_id = uuid4()
        self._repo.create_export_job(export_id=export_id, test_run_id=req.test_run_id)

        # Simulation: immediately create "latest report" metadata for the first requested format.
        chosen_format = req.formats[0] if req.formats else "json"
        report_id = uuid4()
        report = ReportMeta(
            id=report_id,
            test_run_id=req.test_run_id,
            generated_at=now_utc(),
            format=chosen_format,
            download_url=f"/v1/reports/download/{report_id}",
            checksum=self._fake_checksum(report_id),
        )
        self._repo.set_latest(req.test_run_id, report)

        return Accepted(export_id=export_id, state="queued")
