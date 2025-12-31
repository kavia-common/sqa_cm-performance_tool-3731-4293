from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.clients.xena_client import SimulatedXenaClient
from app.core.config import get_settings
from app.repositories.metrics_repository import InMemoryMetricsRepository
from app.repositories.reports_repository import InMemoryReportsRepository
from app.repositories.scenarios_repository import InMemoryScenariosRepository
from app.repositories.tests_repository import InMemoryTestsRepository
from app.routers.health import router as health_router
from app.routers.metrics import router as metrics_router, set_metrics_service
from app.routers.reports import router as reports_router, set_reports_service
from app.routers.scenarios import router as scenarios_router, set_scenarios_service
from app.routers.tests import router as tests_router, set_tests_service
from app.services.metrics_pipeline import MetricsPipeline
from app.services.metrics_service import MetricsService
from app.services.observability import Observability, write_prometheus_response
from app.services.reports_service import ReportsService
from app.services.scenarios_service import ScenariosService
from app.services.tests_service import TestsService

openapi_tags = [
    {"name": "Metrics", "description": "Metrics access endpoints."},
    {"name": "Health", "description": "Operational health and readiness endpoints."},
    {"name": "Tests", "description": "Test lifecycle control endpoints."},
    {"name": "Scenarios", "description": "Scenario CRUD and versioning endpoints."},
    {"name": "Reports", "description": "Report metadata and export endpoints."},
]

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan manager.

    Starts the background metrics polling pipeline on startup and stops it on shutdown.
    Also wires in-memory repositories/services for tests/scenarios/reports for bootstrapping.
    """
    settings = get_settings()

    # Observability and pipeline components
    obs = Observability()
    repo = InMemoryMetricsRepository(cache_hours=settings.metrics_cache_hours)
    client = SimulatedXenaClient(seed=1337)

    pipeline = MetricsPipeline(
        repo=repo,
        client=client,
        poll_interval_ms=settings.metrics_poll_interval_ms,
        max_streams=settings.metrics_max_streams,
        obs=obs,
    )

    # In-memory control-plane repos/services (bootstrap)
    tests_repo = InMemoryTestsRepository()
    scenarios_repo = InMemoryScenariosRepository()
    reports_repo = InMemoryReportsRepository()

    tests_service = TestsService(tests_repo)
    scenarios_service = ScenariosService(scenarios_repo)
    reports_service = ReportsService(reports_repo)

    # Attach to app state for access by routes / other components if needed.
    app.state.metrics_repo = repo
    app.state.metrics_pipeline = pipeline
    app.state.metrics_obs = obs
    app.state.tests_repo = tests_repo
    app.state.scenarios_repo = scenarios_repo
    app.state.reports_repo = reports_repo

    # Router singleton wiring
    set_metrics_service(MetricsService(repo))
    set_tests_service(tests_service)
    set_scenarios_service(scenarios_service)
    set_reports_service(reports_service)

    await pipeline.start()
    logger.info("metrics pipeline started")
    try:
        yield
    finally:
        await pipeline.stop()
        logger.info("metrics pipeline stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()

    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    app = FastAPI(
        title="SQA_CM Performance Tool - REST API v1",
        description=(
            "Versioned REST API for metrics access, health/readiness, test lifecycle control, "
            "scenario management, and report export.\n\n"
            "This bootstrap implements: metrics, health/readiness, tests, scenarios, reports."
        ),
        version="1.0.0",
        openapi_tags=openapi_tags,
        lifespan=lifespan,
    )

    # CORS for React dev/preview frontend.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount all v1 routes under /v1.
    v1 = FastAPI(
        title=app.title,
        description=app.description,
        version=app.version,
        openapi_tags=openapi_tags,
    )
    v1.include_router(metrics_router)
    v1.include_router(health_router)
    v1.include_router(tests_router)
    v1.include_router(scenarios_router)
    v1.include_router(reports_router)

    # Reuse the main app for everything; mount v1 as a sub-app.
    app.mount("/v1", v1)

    @app.get(
        "/metrics",
        tags=["Health"],
        operation_id="getPrometheusMetrics",
        summary="Prometheus metrics scrape",
        description="Prometheus-ready text endpoint for basic pipeline counters/gauges (lightweight, in-process).",
    )
    def prometheus_metrics():
        """Expose basic pipeline stats for Prometheus scraping."""
        obs: Observability = app.state.metrics_obs
        return write_prometheus_response(obs)

    @app.get(
        "/",
        tags=["Health"],
        operation_id="rootHelp",
        summary="API usage help",
        description="Basic pointer to versioned endpoints and docs.",
    )
    def root_help() -> dict:
        """Provide a simple index with API discovery information."""
        return {
            "service": "Backend/APIService",
            "api_base": "/v1",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "endpoints": {
                "health": "/v1/health",
                "ready": "/v1/ready",
                "current_metrics": "/v1/metrics/current",
                "tests_start": "/v1/tests/start",
                "tests_stop": "/v1/tests/stop",
                "tests_status": "/v1/tests/{id}",
                "scenarios": "/v1/scenarios",
                "reports_latest": "/v1/reports/latest?testRunId=...",
                "reports_export": "/v1/reports/export",
                "prometheus_metrics": "/metrics",
            },
        }

    return app


app = create_app()
