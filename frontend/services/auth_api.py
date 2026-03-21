import requests

API_URL = "http://127.0.0.1:8000"

def login(email, password):
    return requests.post(f"{API_URL}/login", json={
        "email": email,
        "password": password
    })

def register(name, email, password):
    return requests.post(f"{API_URL}/register", json={
        "name": name,
        "email": email,
        "password": password
    })