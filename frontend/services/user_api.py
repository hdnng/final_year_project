import requests
import streamlit as st

BASE_URL = "http://127.0.0.1:8000"


def get_auth_headers():
    """Get authorization headers if token exists"""
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# ===== GET USER =====
def get_user(session):
    """Lấy thông tin người dùng hiện tại"""
    try:
        headers = get_auth_headers()
        res = session.get(f"{BASE_URL}/users/profile", headers=headers)

        if res.status_code == 200:
            return res.json()
        elif res.status_code == 401:
            print("Token expired or invalid")
            return None
        else:
            print(f"GET USER ERROR: {res.status_code} - {res.text}")
            return None

    except Exception as e:
        print(f"EXCEPTION get_user: {e}")
        return None


# ===== UPDATE USER =====
def update_user(session, full_name, email):
    """Cập nhật thông tin người dùng"""
    try:
        headers = get_auth_headers()
        res = session.put(
            f"{BASE_URL}/users/update",
            json={
                "full_name": full_name,
                "email": email
            },
            headers=headers
        )

        if res.status_code == 200:
            return True, res.json()
        elif res.status_code == 401:
            return False, "Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại"
        elif res.status_code == 409:
            return False, "Email này đã được sử dụng"
        else:
            try:
                return False, res.json().get("detail", "Lỗi server")
            except Exception:
                return False, res.text

    except Exception as e:
        return False, f"Lỗi kết nối: {str(e)}"


# ===== CHANGE PASSWORD =====
def change_password(session, old_password, new_password):
    """Đổi mật khẩu"""
    try:
        headers = get_auth_headers()
        res = session.put(
            f"{BASE_URL}/users/change-password",
            json={
                "old_password": old_password,
                "new_password": new_password
            },
            headers=headers
        )

        if res.status_code == 200:
            return True, res.json()
        elif res.status_code == 401:
            return False, "Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại"
        elif res.status_code == 422:
            try:
                return False, res.json().get("detail", "Mật khẩu cũ không chính xác")
            except Exception:
                return False, "Mật khẩu cũ không chính xác"
        else:
            try:
                return False, res.json().get("detail", "Lỗi server")
            except Exception:
                return False, res.text

    except Exception as e:
        return False, f"Lỗi kết nối: {str(e)}"