from __future__ import annotations

import threading
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Deque, List, Optional

from app.schemas.metrics import CurrentMetrics, SeriesSample


class MetricsRepository:
    """Repository abstraction for metrics persistence.

    This interface is intentionally small so it can later be backed by PostgreSQL/TimescaleDB.
    """

    # PUBLIC_INTERFACE
    def get_current(self) -> Optional[CurrentMetrics]:
        """Get the latest current metrics snapshot."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def set_current(self, snapshot: CurrentMetrics) -> None:
        """Set (overwrite) the latest current metrics snapshot."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def append_sample(self, sample: SeriesSample) -> None:
        """Append a sample to the rolling time series cache."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def get_samples_since(self, since: datetime) -> List[SeriesSample]:
        """Return cached samples newer than `since`."""
        raise NotImplementedError


class InMemoryMetricsRepository(MetricsRepository):
    """Thread-safe in-memory metrics store with a rolling 24h ring buffer.

    Note: this is designed to be swapped for DB persistence later without changing callers.
    """

    def __init__(self, cache_hours: int = 24) -> None:
        self._lock = threading.Lock()
        self._current: Optional[CurrentMetrics] = None
        self._samples: Deque[SeriesSample] = deque()
        self._cache_window = timedelta(hours=max(1, cache_hours))

    def _prune_locked(self, now: datetime) -> None:
        cutoff = now - self._cache_window
        while self._samples and self._samples[0].ts < cutoff:
            self._samples.popleft()

    # PUBLIC_INTERFACE
    def get_current(self) -> Optional[CurrentMetrics]:
        """Get the latest current metrics snapshot."""
        with self._lock:
            return self._current

    # PUBLIC_INTERFACE
    def set_current(self, snapshot: CurrentMetrics) -> None:
        """Set (overwrite) the latest current metrics snapshot."""
        with self._lock:
            self._current = snapshot

    # PUBLIC_INTERFACE
    def append_sample(self, sample: SeriesSample) -> None:
        """Append a sample to the rolling time series cache."""
        with self._lock:
            self._samples.append(sample)
            now = datetime.now(timezone.utc)
            self._prune_locked(now)

    # PUBLIC_INTERFACE
    def get_samples_since(self, since: datetime) -> List[SeriesSample]:
        """Return cached samples newer than `since`."""
        with self._lock:
            return [s for s in self._samples if s.ts >= since]
