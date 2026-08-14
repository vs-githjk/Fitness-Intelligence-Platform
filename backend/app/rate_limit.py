"""In-process sliding-window rate limiting for abuse-sensitive endpoints (Part 64).

Pure and testable (inject a clock). IMPORTANT operational note: this counter lives in the
process, so a multi-instance deployment allows roughly ``limit x instances`` before any one
process rejects. That is acceptable as a first line against brute force / accidental floods;
a shared store (e.g. Redis) is the documented follow-up for a true global limit, recorded on
the Security/Trust page. It fails open (never blocks legitimate traffic on limiter error).
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable
from threading import Lock


class RateLimiter:
    def __init__(
        self, *, limit: int, window_seconds: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.limit = limit
        self.window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> tuple[bool, int]:
        """Record a hit for ``key``. Returns (allowed, retry_after_seconds).

        retry_after is 0 when allowed, else a positive whole-second hint until the oldest
        hit in the window expires.
        """
        now = self._clock()
        cutoff = now - self.window
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self.limit:
                return False, max(1, int(self.window - (now - hits[0])) + 1)
            hits.append(now)
            return True, 0
