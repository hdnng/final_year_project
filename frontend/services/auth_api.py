import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

def get_auth_headers():
    """Get authorization headers if token exists"""
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def login(session, email, password):
    """Đăng nhập - returns response object"""
    response = session.post(
        f"{API_URL}/users/login",
        json={
            "email": email,
            "password": password
        }
    )

    # Extract and return token if available
    if response.status_code == 200:
        try:
            response.token = response.json().get("access_token")
        except Exception:
            response.token = None

    return response

def register(session, full_name, email, password):
    """Đăng ký - returns response object"""
    return session.post(
        f"{API_URL}/users/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name
        }
    )

def logout(session):
    """Đăng xuất - blacklist token và xóa session"""
    try:
        headers = get_auth_headers()
        response = session.post(f"{API_URL}/users/logout", headers=headers)
        return response
    except Exception as e:
        print(f"Logout error: {e}")
        return None

def refresh_token(session):
    """Refresh access token using refresh token"""
    try:
        headers = get_auth_headers()
        response = session.post(f"{API_URL}/users/refresh", headers=headers)
        return response
    except Exception as e:
        print(f"Refresh error: {e}")
        return None
