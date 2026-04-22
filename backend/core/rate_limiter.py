"""
IP-based rate limiter for brute-force prevention.

Uses a sliding-window algorithm with per-IP attempt tracking.
Thread-safe singleton for use across async workers.
"""

import threading
from datetime import datetime, timedelta, timezone

from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Rate limiter with configurable window and threshold.

    Singleton — all access goes through the same instance.
    """

    _instance = None
    _lock = threading.Lock()

    MAX_ATTEMPTS: int = settings.RATE_LIMIT_MAX_ATTEMPTS
    TIME_WINDOW: timedelta = timedelta(minutes=settings.RATE_LIMIT_WINDOW_MINUTES)

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._attempts: dict[str, list[datetime]] = {}
        return cls._instance

    # ── Internal ────────────────────────────────────────────

    def _clean_expired(self, ip: str) -> None:
        """Evict attempts older than TIME_WINDOW for *ip*."""
        if ip not in self._attempts:
            return

        cutoff = datetime.now(timezone.utc) - self.TIME_WINDOW
        self._attempts[ip] = [t for t in self._attempts[ip] if t > cutoff]

        if not self._attempts[ip]:
            del self._attempts[ip]

    # ── Public API ──────────────────────────────────────────

    def is_rate_limited(self, ip: str) -> bool:
        """Return True if *ip* has exhausted its allowed attempts."""
        self._clean_expired(ip)
        return len(self._attempts.get(ip, [])) >= self.MAX_ATTEMPTS

    def record_attempt(self, ip: str) -> None:
        """Record a failed attempt for *ip*."""
        self._attempts.setdefault(ip, []).append(datetime.now(timezone.utc))
        logger.debug(
            f"Rate-limit: attempt recorded for {ip} "
            f"({len(self._attempts[ip])}/{self.MAX_ATTEMPTS})"
        )

    def get_remaining_attempts(self, ip: str) -> int:
        """Return how many attempts *ip* has left."""
        self._clean_expired(ip)
        return max(0, self.MAX_ATTEMPTS - len(self._attempts.get(ip, [])))

    def get_reset_time(self, ip: str) -> datetime:
        """Return when the rate-limit window resets for *ip*."""
        attempts = self._attempts.get(ip, [])
        if not attempts:
            return datetime.now(timezone.utc)
        return min(attempts) + self.TIME_WINDOW

    def reset_for_ip(self, ip: str) -> None:
        """Clear all tracked attempts for *ip*."""
        if self._attempts.pop(ip, None):
            logger.info(f"Rate-limit reset for IP: {ip}")

    def reset_all(self) -> None:
        """Clear all rate-limit tracking data."""
        self._attempts.clear()
        logger.info("All rate limits reset")

    def get_stats(self) -> dict:
        """Return diagnostic statistics."""
        return {
            "tracked_ips": len(self._attempts),
            "total_attempts": sum(len(v) for v in self._attempts.values()),
            "max_attempts": self.MAX_ATTEMPTS,
            "time_window_minutes": int(self.TIME_WINDOW.total_seconds() / 60),
        }
