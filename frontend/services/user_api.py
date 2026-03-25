import requests

BASE_URL = "http://127.0.0.1:8000"


# ===== GET USER =====
def get_user(session):
    try:
        res = session.get(f"{BASE_URL}/profile")

        if res.status_code == 200:
            return res.json()
        else:
            print("GET USER ERROR:", res.status_code, res.text)
            return None

    except Exception as e:
        print("EXCEPTION get_user:", e)
        return None


# ===== UPDATE USER =====
def update_user(session, full_name, email):
    try:
        res = session.put(
            f"{BASE_URL}/update",
            json={
                "full_name": full_name,
                "email": email
            }
        )

        if res.status_code == 200:
            return True, res.json()
        else:
            return False, res.text

    except Exception as e:
        return False, str(e)


# ===== CHANGE PASSWORD =====
def change_password(session, old_password, new_password):
    try:
        res = session.put(
            f"{BASE_URL}/change-password",
            json={
                "old_password": old_password,
                "new_password": new_password
            }
        )

        if res.status_code == 200:
            return True, res.json()
        else:
            try:
                return False, res.json().get("detail", "Lỗi server")
            except:
                return False, res.text

    except Exception as e:
        return False, str(e)