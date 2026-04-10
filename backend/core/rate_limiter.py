"""
Rate limiting system to prevent brute force attacks.
Tracks login attempts per IP address with time-based bucket reset.
"""

import threading
from datetime import datetime, timedelta
from typing import Dict, Tuple
from core.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Rate limiter for login attempts.
    Max 5 attempts per 15 minutes per IP address.
    Singleton pattern with thread-safe locking.
    """

    _instance = None
    _lock = threading.Lock()

    # Configuration
    MAX_ATTEMPTS = 5
    TIME_WINDOW = timedelta(minutes=15)

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._attempts: Dict[str, list] = {}
        return cls._instance

    def _clean_expired_attempts(self, ip: str):
        """Remove attempts older than TIME_WINDOW."""
        if ip not in self._attempts:
            return

        now = datetime.utcnow()
        cutoff = now - self.TIME_WINDOW

        # Keep only recent attempts
        self._attempts[ip] = [
            attempt_time for attempt_time in self._attempts[ip]
            if attempt_time > cutoff
        ]

        # Remove IP if no attempts left
        if not self._attempts[ip]:
            del self._attempts[ip]

    def is_rate_limited(self, ip: str) -> bool:
        """
        Check if IP address has exceeded rate limit.

        Returns:
            True if rate limited (too many attempts)
            False if allowed
        """
        self._clean_expired_attempts(ip)

        if ip not in self._attempts:
            return False

        return len(self._attempts[ip]) >= self.MAX_ATTEMPTS

    def record_attempt(self, ip: str):
        """Record a login attempt for given IP address."""
        if ip not in self._attempts:
            self._attempts[ip] = []

        self._attempts[ip].append(datetime.utcnow())
        logger.debug(f"🔒 Login attempt recorded for IP: {ip} (attempts: {len(self._attempts[ip])})")

    def get_remaining_attempts(self, ip: str) -> int:
        """Get number of attempts remaining before rate limit."""
        self._clean_expired_attempts(ip)

        if ip not in self._attempts:
            return self.MAX_ATTEMPTS

        return max(0, self.MAX_ATTEMPTS - len(self._attempts[ip]))

    def get_reset_time(self, ip: str) -> datetime:
        """Get when rate limit will reset for this IP."""
        if ip not in self._attempts or not self._attempts[ip]:
            return datetime.utcnow()

        oldest_attempt = min(self._attempts[ip])
        return oldest_attempt + self.TIME_WINDOW

    def reset_for_ip(self, ip: str):
        """Manually reset attempts for an IP (admin function)."""
        if ip in self._attempts:
            del self._attempts[ip]
            logger.info(f"🔓 Rate limit reset for IP: {ip}")

    def reset_all(self):
        """Reset all rate limit tracking (admin function)."""
        self._attempts.clear()
        logger.info("🔓 All rate limits reset")

    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        self._clean_expired_attempts("__temp__")  # Cleanup old entries

        return {
            "tracked_ips": len(self._attempts),
            "total_attempts": sum(len(attempts) for attempts in self._attempts.values()),
            "max_attempts": self.MAX_ATTEMPTS,
            "time_window_minutes": int(self.TIME_WINDOW.total_seconds() / 60)
        }
