import requests

API_URL = "http://127.0.0.1:8000"

def login(session, email, password):
    return session.post(
        f"{API_URL}/login",
        json={
            "email": email,
            "password": password
        }
    )

def register(full_name, email, password):
    return requests.post(f"{API_URL}/register", json={
        "email": email,
        "password": password,
        "full_name": full_name
    })