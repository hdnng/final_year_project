from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import datetime

import schemas.schemas as schemas
import crud.user_crud as user_crud
from database.database import get_db
from core.security import hash_password, verify_password, get_cookie_settings
from core.auth import create_access_token, create_refresh_token, verify_token
from core.dependencies import get_current_user, get_client_ip
from core.logger import get_logger
from core.exceptions import ValidationError, AuthenticationError, ConflictError
from core.token_blacklist import TokenBlacklist
from core.rate_limiter import RateLimiter
from models.user import User

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, request: Request, db: Session = Depends(get_db)):
    """
    Đăng ký người dùng mới

    - **email**: Email duy nhất
    - **password**: Tối thiểu 6 ký tự, phải có chữ hoa và số
    - **full_name**: Tên đầy đủ (3-100 ký tự)
    """
    try:
        client_ip = get_client_ip(request)
        rate_limiter = RateLimiter()

        # Rate limit registration attempts (max 10 per hour per IP)
        # Use a separate key to distinguish from login attempts
        reg_key = f"reg:{client_ip}"

        # Check rate limit
        if rate_limiter.is_rate_limited(reg_key):
            reset_time = rate_limiter.get_reset_time(reg_key)
            minutes_remaining = int((reset_time - datetime.utcnow()).total_seconds() / 60)
            logger.warning(f"🔒 Registration rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail=f"Too many registration attempts. Try again in {minutes_remaining} minutes."
            )

        # Kiểm tra email đã tồn tại
        existing_user = user_crud.get_user_by_email(db, user.email)
        if existing_user:
            rate_limiter.record_attempt(reg_key)
            logger.warning(f"❌ Registration attempt with existing email: {user.email}")
            raise ConflictError(detail="Email already exists")

        logger.info(f"📝 Registering new user: {user.email} from {client_ip}")
        created_user = user_crud.create_user(db, user)

        # ✅ Successful registration - reset rate limit for this IP
        rate_limiter.reset_for_ip(reg_key)

        logger.info(f"✅ User registered successfully: {user.email}")

        return created_user

    except IntegrityError as e:
        db.rollback()
        logger.error(f"❌ Database integrity error: {str(e)}", exc_info=True)
        raise ConflictError(detail="Failed to create user - duplicate email")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Registration error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login")
def login(user: schemas.UserLogin, response: Response, request: Request, db: Session = Depends(get_db)):
    """
    Đăng nhập người dùng

    Returns: JWT tokens được lưu trong cookie
    """
    try:
        client_ip = get_client_ip(request)
        rate_limiter = RateLimiter()

        # Check rate limit
        if rate_limiter.is_rate_limited(client_ip):
            reset_time = rate_limiter.get_reset_time(client_ip)
            minutes_remaining = int((reset_time - datetime.utcnow()).total_seconds() / 60)
            logger.warning(f"🔒 Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail=f"Too many login attempts. Try again in {minutes_remaining} minutes."
            )

        logger.info(f"🔐 Login attempt for: {user.email} from {client_ip}")

        db_user = user_crud.get_user_by_email(db, user.email)

        if not db_user:
            rate_limiter.record_attempt(client_ip)
            remaining = rate_limiter.get_remaining_attempts(client_ip)
            logger.warning(f"❌ Login failed - user not found: {user.email} from {client_ip}")
            raise AuthenticationError(detail="Invalid email or password")

        if not verify_password(user.password, db_user.password):
            rate_limiter.record_attempt(client_ip)
            remaining = rate_limiter.get_remaining_attempts(client_ip)
            logger.warning(f"❌ Login failed - wrong password: {user.email} from {client_ip}")
            raise AuthenticationError(detail="Invalid email or password")

        # ✅ Successful login - reset rate limit for this IP
        rate_limiter.reset_for_ip(client_ip)

        # Create access and refresh tokens
        access_token, access_exp = create_access_token(data={"user_id": db_user.user_id})
        refresh_token, refresh_exp = create_refresh_token(data={"user_id": db_user.user_id})

        # Set cookies with dynamic settings
        cookie_settings = get_cookie_settings()

        response.set_cookie(
            key="access_token",
            value=access_token,
            **cookie_settings
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            secure=cookie_settings.get("secure", False),
            samesite="lax"
        )

        logger.info(f"✅ Login successful: {user.email} from {client_ip}")
        return {
            "message": "Login successful",
            "user_id": db_user.user_id,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/profile", response_model=schemas.User)
def get_profile(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin profile người dùng hiện tại

    Requires: Authentication token
    """
    try:
        user = user_crud.get_user_by_id(db, user_id)

        if not user:
            logger.warning(f"⚠️ Profile request - user not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        logger.debug(f"📋 Profile retrieved for user: {user_id}")
        return user

    except Exception as e:
        logger.error(f"❌ Profile retrieval error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve profile")


@router.put("/update", response_model=schemas.User)
def update_user(
    data: schemas.UserUpdate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cập nhật thông tin người dùng hiện tại

    Requires: Authentication token
    """
    try:
        logger.info(f"✏️ Updating user info: {user_id}")

        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            logger.warning(f"⚠️ Update failed - user not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        user.full_name = data.full_name
        user.email = data.email

        db.commit()
        db.refresh(user)

        logger.info(f"✅ User info updated: {user_id}")
        return user

    except IntegrityError as e:
        db.rollback()
        logger.error(f"❌ Email already in use: {str(e)}", exc_info=True)
        raise ConflictError(detail="Email already in use")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Update error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Update failed")


@router.put("/change-password")
def change_password(
    data: schemas.ChangePassword,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Đổi mật khẩu người dùng hiện tại

    Requires: Authentication token
    """
    try:
        logger.info(f"🔑 Password change requested for user: {user_id}")

        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            logger.warning(f"⚠️ Password change - user not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        # Verify old password
        if not verify_password(data.old_password, user.password):
            logger.warning(f"❌ Password change failed - wrong old password: {user_id}")
            raise ValidationError(detail="Old password is incorrect")

        # Update new password
        user.password = hash_password(data.new_password)
        db.commit()

        logger.info(f"✅ Password changed successfully: {user_id}")
        return {"message": "Password changed successfully"}

    except ValidationError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Password change error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Password change failed")


@router.post("/logout")
def logout(
    response: Response,
    user_id: int = Depends(get_current_user),
    access_token: str = Cookie(None),
    refresh_token: str = Cookie(None)
):
    """
    Đăng xuất người dùng - thêm token vào blacklist

    Requires: Authentication token
    """
    try:
        logger.info(f"🚪 Logout requested for user: {user_id}")

        # Add access token to blacklist
        if access_token:
            try:
                payload = verify_token(access_token, token_type="access")
                if payload:
                    exp_timestamp = payload.get("exp")
                    if exp_timestamp:
                        exp_datetime = datetime.fromtimestamp(exp_timestamp)
                        TokenBlacklist.add(access_token, exp_datetime)
                        logger.debug(f"✅ Access token added to blacklist for user: {user_id}")
            except Exception as e:
                logger.debug(f"⚠️ Could not blacklist access token: {str(e)}")

        # Add refresh token to blacklist
        if refresh_token:
            try:
                payload = verify_token(refresh_token, token_type="refresh")
                if payload:
                    exp_timestamp = payload.get("exp")
                    if exp_timestamp:
                        exp_datetime = datetime.fromtimestamp(exp_timestamp)
                        TokenBlacklist.add(refresh_token, exp_datetime)
                        logger.debug(f"✅ Refresh token added to blacklist for user: {user_id}")
            except Exception as e:
                logger.debug(f"⚠️ Could not blacklist refresh token: {str(e)}")

        # Clear cookies with matching parameters
        cookie_settings = get_cookie_settings()
        response.delete_cookie(
            key="access_token",
            path="/",
            httponly=cookie_settings.get("httponly", True),
            secure=cookie_settings.get("secure", False),
            samesite=cookie_settings.get("samesite", "lax")
        )
        response.delete_cookie(
            key="refresh_token",
            path="/",
            httponly=True,
            secure=cookie_settings.get("secure", False),
            samesite="lax"
        )

        logger.info(f"✅ Logout successful: {user_id}")
        return {"message": "Logout successful"}

    except Exception as e:
        logger.error(f"❌ Logout error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Logout failed")


@router.post("/refresh")
def refresh_access_token(
    response: Response,
    refresh_token: str = Cookie(None)
):
    """
    Tạo access token mới từ refresh token

    Requires: Valid refresh token in cookie
    """
    try:
        if not refresh_token:
            logger.warning("❌ Refresh attempt - no refresh token provided")
            raise HTTPException(status_code=401, detail="Refresh token not provided")

        # Check if token is blacklisted
        if TokenBlacklist.is_blacklisted(refresh_token):
            logger.warning("❌ Refresh attempt - refresh token is blacklisted")
            raise HTTPException(status_code=401, detail="Refresh token has been revoked")

        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            logger.warning("❌ Refresh attempt - invalid refresh token")
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user_id = payload.get("user_id")
        if not user_id:
            logger.warning("❌ Refresh attempt - no user_id in token")
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Create new access token
        access_token, access_exp = create_access_token(data={"user_id": user_id})

        # Set new access token in cookie
        cookie_settings = get_cookie_settings()
        response.set_cookie(
            key="access_token",
            value=access_token,
            **cookie_settings
        )

        logger.info(f"✅ Access token refreshed for user: {user_id}")
        return {
            "message": "Token refreshed successfully",
            "access_token": access_token,
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"❌ Token refresh error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Token refresh failed")

