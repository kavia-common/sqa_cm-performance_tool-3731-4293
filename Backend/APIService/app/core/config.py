from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, List, Optional


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_int(value: Optional[str], default: int) -> int:
    if value is None:
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def _parse_json(value: Optional[str], default: Any) -> Any:
    """Parse JSON from an env var.

    We intentionally accept '{}' etc. because REACT_APP_FEATURE_FLAGS is present
    in this project and may contain JSON.
    """
    if value is None or value.strip() == "":
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the API service."""

    # Network / runtime
    host: str
    port: int
    log_level: str
    trust_proxy: bool

    # URLs exposed to clients (existing keys in this workspace)
    frontend_url: Optional[str]
    backend_url: Optional[str]
    ws_url: Optional[str]
    api_base: Optional[str]

    # CORS
    cors_allow_origins: List[str]


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load API service settings from environment variables.

    This service intentionally reuses existing REACT_APP_* environment variables
    already present in this workspace (for preview) instead of introducing new keys.

    Returns:
        Settings: Parsed settings with sensible defaults.
    """
    # Prefer explicit backend port if provided; otherwise use 8000.
    # Note: REACT_APP_PORT is used by the React dev server (3000) and should not
    # automatically be used for the API. We keep API port separate with default 8000.
    api_port = _parse_int(os.getenv("PORT"), default=8000)

    # Allow using common hosting env vars if present; fallback to localhost.
    host = os.getenv("HOST", "0.0.0.0")

    # Reuse existing log level key; allow standard LOG_LEVEL override too.
    log_level = (os.getenv("LOG_LEVEL") or os.getenv("REACT_APP_LOG_LEVEL") or "info").lower()

    trust_proxy = _parse_bool(os.getenv("REACT_APP_TRUST_PROXY"), default=False)

    frontend_url = os.getenv("REACT_APP_FRONTEND_URL")
    backend_url = os.getenv("REACT_APP_BACKEND_URL")
    ws_url = os.getenv("REACT_APP_WS_URL")
    api_base = os.getenv("REACT_APP_API_BASE")

    # CORS: allow the frontend URL if set; always include common local dev URL.
    origins: List[str] = ["http://localhost:3000"]
    if frontend_url:
        origins.append(frontend_url)

    # De-duplicate while preserving order
    seen = set()
    cors_allow_origins: List[str] = []
    for o in origins:
        if o and o not in seen:
            cors_allow_origins.append(o)
            seen.add(o)

    return Settings(
        host=host,
        port=api_port,
        log_level=log_level,
        trust_proxy=trust_proxy,
        frontend_url=frontend_url,
        backend_url=backend_url,
        ws_url=ws_url,
        api_base=api_base,
        cors_allow_origins=cors_allow_origins,
    )
