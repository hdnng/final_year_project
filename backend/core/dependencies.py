from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from core.auth import SECRET_KEY, ALGORITHM
from core.token_blacklist import TokenBlacklist
from core.logger import get_logger

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    Handles X-Forwarded-For header for proxied requests and direct client connections.
    """
    # Check X-Forwarded-For header (for proxies like nginx, cloudflare)
    if "x-forwarded-for" in request.headers:
        # Take the first IP if multiple are listed
        return request.headers["x-forwarded-for"].split(",")[0].strip()

    # Check X-Real-IP header (alternative proxy header)
    if "x-real-ip" in request.headers:
        return request.headers["x-real-ip"]

    # Fall back to direct client connection
    return request.client.host if request.client else "unknown"


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Extract and validate JWT token từ cookie hoặc Authorization header
    Check token blacklist (logout prevention)
    """
    token = None

    # ✅ Ưu tiên cookie
    if "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    # ✅ Fallback sang header
    elif credentials:
        token = credentials.credentials

    if not token:
        logger.warning("❌ Unauthorized: No token provided")
        raise HTTPException(status_code=401, detail="Not authenticated")

    # ✅ Check token blacklist (logout)
    if TokenBlacklist.is_blacklisted(token):
        logger.warning("❌ Unauthorized: Token is blacklisted (logged out)")
        raise HTTPException(status_code=401, detail="Token has been revoked")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id = payload.get("user_id")

        if user_id is None:
            logger.warning("❌ Unauthorized: Invalid token - no user_id")
            raise HTTPException(status_code=401, detail="Invalid token")

        logger.debug(f"✅ User authenticated: {user_id}")
        return user_id

    except JWTError as e:
        logger.warning(f"❌ Unauthorized: JWT validation failed - {str(e)}")
        raise HTTPException(status_code=401, detail="Token invalid")
    except Exception as e:
        logger.error(f"❌ Auth error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Authentication failed")
