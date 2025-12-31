from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Protocol


@dataclass(frozen=True)
class StreamCounters:
    """Raw counters for a single stream."""
    stream_id: str
    frame_size: int
    rx_bytes_total: int
    tx_bytes_total: int
    rx_frames_total: int
    tx_frames_total: int
    error_counters_total: Dict[str, int]


@dataclass(frozen=True)
class DeviceCountersSnapshot:
    """Raw counters snapshot from a device.

    The aggregator will compute rates (Gbps) based on deltas between snapshots.
    """
    ts: datetime
    streams: List[StreamCounters]


class XenaClient(Protocol):
    """Abstract interface for retrieving counters from Xena.

    Swap this implementation with a real vendor SDK/client later.
    """

    # PUBLIC_INTERFACE
    def fetch_counters(self, max_streams: int) -> DeviceCountersSnapshot:
        """Fetch raw cumulative counters for up to `max_streams` streams."""
        raise NotImplementedError


class SimulatedXenaClient:
    """Deterministic pseudo-random counter generator.

    Provides realistic, changing data while remaining reproducible. Also simulates
    occasional dropped polls (returns previous snapshot) so compensation logic
    can be observed.
    """

    def __init__(self, seed: int = 1337) -> None:
        self._rnd = random.Random(seed)
        self._t = 0
        self._rx_bytes: List[int] = []
        self._tx_bytes: List[int] = []
        self._rx_frames: List[int] = []
        self._tx_frames: List[int] = []

    def _ensure_streams(self, n: int) -> None:
        while len(self._rx_bytes) < n:
            self._rx_bytes.append(0)
            self._tx_bytes.append(0)
            self._rx_frames.append(0)
            self._tx_frames.append(0)

    # PUBLIC_INTERFACE
    def fetch_counters(self, max_streams: int) -> DeviceCountersSnapshot:
        """Fetch simulated raw counters for up to `max_streams` streams."""
        self._t += 1
        n = max(1, max_streams)

        # Simulate a dropped poll ~every 37 ticks by not advancing counters.
        dropped = (self._t % 37) == 0

        self._ensure_streams(n)
        streams: List[StreamCounters] = []
        now = datetime.now(timezone.utc)

        for i in range(n):
            frame_size = 64 + (i * 128) % 1500
            # Create smoothly varying tx base rate in bytes/s (approx).
            base_bps = 5e9 + 1e9 * math.sin((self._t + i) / 10.0)  # bits/s
            base_Bps = base_bps / 8.0

            # Convert to per-second increments (we assume poll interval ~1s).
            # Add small deterministic noise.
            noise = self._rnd.uniform(-0.08, 0.08)
            tx_inc_bytes = int(max(0.0, base_Bps * (1.0 + noise)))

            # RX slightly below TX to create some loss.
            loss_factor = 0.002 + 0.002 * abs(math.sin((self._t + i) / 17.0))  # 0.2%..0.4%
            rx_inc_bytes = int(tx_inc_bytes * (1.0 - loss_factor))

            tx_inc_frames = max(1, tx_inc_bytes // max(64, frame_size))
            rx_inc_frames = max(0, rx_inc_bytes // max(64, frame_size))

            if not dropped:
                self._tx_bytes[i] += tx_inc_bytes
                self._rx_bytes[i] += rx_inc_bytes
                self._tx_frames[i] += tx_inc_frames
                self._rx_frames[i] += rx_inc_frames

            # Create occasional error bumps
            crc = 0
            undersize = 0
            if (self._t + i) % 53 == 0 and not dropped:
                crc = self._rnd.randint(1, 5)
            if (self._t + i) % 79 == 0 and not dropped:
                undersize = self._rnd.randint(1, 3)

            streams.append(
                StreamCounters(
                    stream_id=f"stream-{i+1}",
                    frame_size=frame_size,
                    rx_bytes_total=self._rx_bytes[i],
                    tx_bytes_total=self._tx_bytes[i],
                    rx_frames_total=self._rx_frames[i],
                    tx_frames_total=self._tx_frames[i],
                    error_counters_total={"crc": crc, "undersize": undersize},
                )
            )

        return DeviceCountersSnapshot(ts=now, streams=streams)
