import requests

BASE_URL = "http://127.0.0.1:8000"

def update_user(name, email, token):
    url = f"{BASE_URL}/update"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    data = {
        "name": name,
        "email": email
    }

    response = requests.put(url, json=data, headers=headers)

    if response.status_code == 200:
        return True, response.json()
    else:
        return False, response.text
    

def get_user(token):
    url = f"{BASE_URL}/profile"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        res = requests.get(url, headers=headers)

        if res.status_code == 200:
            return res.json()
        else:
            print("GET USER ERROR:", res.status_code, res.text)
            return None

    except Exception as e:
        print("EXCEPTION get_user:", e)
        return None
    

def change_password(old_password, new_password, token):
    try:
        res = requests.put(
            f"{BASE_URL}/change-password",
            json={
                "old_password": old_password,
                "new_password": new_password
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        if res.status_code == 200:
            return True, res.json()
        else:
            return False, res.json().get("detail", "Lỗi server")

    except Exception as e:
        return False, str(e)
    


