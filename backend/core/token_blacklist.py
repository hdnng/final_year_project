"""
In-memory token blacklist for logout support.

Note: In production, replace with Redis-backed storage for
persistence across restarts and horizontal scaling.
"""

from datetime import datetime, timezone


class TokenBlacklist:
    """Track revoked JWT tokens until their natural expiry."""

    _blacklist: set[str] = set()
    _expiry_times: dict[str, datetime] = {}

    @classmethod
    def add(cls, token: str, expires_at: datetime) -> None:
        """Add a token to the blacklist with its expiry timestamp."""
        cls._blacklist.add(token)
        cls._expiry_times[token] = expires_at

    @classmethod
    def is_blacklisted(cls, token: str) -> bool:
        """Check whether a token has been revoked."""
        if token not in cls._blacklist:
            return False

        # Auto-cleanup if token has expired naturally
        expiry = cls._expiry_times.get(token)
        if expiry and datetime.now(timezone.utc) > expiry:
            cls._blacklist.discard(token)
            cls._expiry_times.pop(token, None)
            return False

        return True

    @classmethod
    def clear_expired(cls) -> None:
        """Remove all naturally expired tokens from the blacklist."""
        now = datetime.now(timezone.utc)
        expired = [t for t, exp in cls._expiry_times.items() if now > exp]
        for token in expired:
            cls._blacklist.discard(token)
            cls._expiry_times.pop(token, None)
