from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers.health import router as health_router
from app.routers.metrics import router as metrics_router

openapi_tags = [
    {"name": "Metrics", "description": "Metrics access endpoints."},
    {"name": "Health", "description": "Operational health and readiness endpoints."},
]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title="SQA_CM Performance Tool - REST API v1",
        description=(
            "Versioned REST API for metrics access, health/readiness, test lifecycle control, "
            "scenario management, and report export.\n\n"
            "This bootstrap implements: GET /v1/metrics/current, GET /v1/health, GET /v1/ready."
        ),
        version="1.0.0",
        openapi_tags=openapi_tags,
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

    # Reuse the main app for everything; mount v1 as a sub-app.
    app.mount("/v1", v1)

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
            },
        }

    return app


app = create_app()
