"""
Token Blacklist System - Để logout và quản lý token
"""
from datetime import datetime, timedelta
from typing import Set

class TokenBlacklist:
    """In-memory token blacklist (nên dùng Redis ở production)"""
    _blacklist: Set[str] = set()
    _expiry_times: dict = {}

    @classmethod
    def add(cls, token: str, expires_at: datetime):
        """Add token to blacklist"""
        cls._blacklist.add(token)
        cls._expiry_times[token] = expires_at

    @classmethod
    def is_blacklisted(cls, token: str) -> bool:
        """Check if token is blacklisted"""
        if token not in cls._blacklist:
            return False

        # Clean up expired tokens
        if datetime.utcnow() > cls._expiry_times.get(token, datetime.utcnow()):
            cls._blacklist.discard(token)
            cls._expiry_times.pop(token, None)
            return False

        return True

    @classmethod
    def clear_expired(cls):
        """Remove expired tokens from blacklist"""
        now = datetime.utcnow()
        expired = [t for t, exp in cls._expiry_times.items() if now > exp]
        for token in expired:
            cls._blacklist.discard(token)
            cls._expiry_times.pop(token, None)
