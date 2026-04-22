"""
FastAPI dependencies for authentication and request metadata.
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from core.config import settings
from core.logger import get_logger
from core.token_blacklist import TokenBlacklist

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


def get_client_ip(request: Request) -> str:
    """
    Extract the client IP address from the request.

    Checks proxy headers (X-Forwarded-For, X-Real-IP) before falling
    back to the direct client connection.
    """
    if forwarded := request.headers.get("x-forwarded-for"):
        return forwarded.split(",")[0].strip()

    if real_ip := request.headers.get("x-real-ip"):
        return real_ip

    return request.client.host if request.client else "unknown"


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """
    Authenticate the current user via JWT.

    Token resolution order:
      1. ``access_token`` cookie
      2. ``Authorization: Bearer <token>`` header

    Returns:
        The authenticated user's ID.

    Raises:
        HTTPException 401: If token is missing, blacklisted, or invalid.
    """
    # Resolve token: cookie first, then header
    token = request.cookies.get("access_token")
    if not token and credentials:
        token = credentials.credentials

    if not token:
        logger.warning("Unauthorized: no token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Check blacklist (logged-out tokens)
    if TokenBlacklist.is_blacklisted(token):
        logger.warning("Unauthorized: token is blacklisted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: int | None = payload.get("user_id")

        if user_id is None:
            logger.warning("Unauthorized: token missing user_id")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        logger.debug(f"User authenticated: {user_id}")
        return user_id

    except JWTError as exc:
        logger.warning(f"Unauthorized: JWT validation failed — {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid",
        )
