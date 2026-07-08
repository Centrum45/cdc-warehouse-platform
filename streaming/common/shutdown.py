from __future__ import annotations

"""
Graceful shutdown handler for long-running pipeline processes.

Usage:
    from streaming.common.shutdown import GracefulShutdown

    shutdown = GracefulShutdown()

    while shutdown.running:
        process_batch()
        shutdown.sleep(interval_seconds)

On SIGTERM/SIGINT, shutdown.running becomes False after the current
iteration completes.
"""

import signal
import time
from typing import Callable


class GracefulShutdown:
    """Signal-aware loop controller."""

    def __init__(self, on_shutdown: Callable[[], None] | None = None) -> None:
        self._running = True
        self._on_shutdown = on_shutdown

        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum: int, frame) -> None:
        name = signal.Signals(signum).name
        print(f"[shutdown] received {name}, draining current batch...")
        self._running = False
        if self._on_shutdown:
            try:
                self._on_shutdown()
            except Exception as exc:
                print(f"[shutdown] on_shutdown hook failed: {exc}")

    @property
    def running(self) -> bool:
        return self._running

    def sleep(self, seconds: float) -> None:
        """Sleep in small chunks so signals are handled promptly."""
        deadline = time.monotonic() + seconds
        while self._running and time.monotonic() < deadline:
            time.sleep(min(0.5, max(0.1, deadline - time.monotonic())))
