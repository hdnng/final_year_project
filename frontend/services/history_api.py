import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"


def get_headers():
    token = st.session_state.get("access_token_value")
    return {"Authorization": f"Bearer {token}"} if token else {}


def delete_session(session_id):
    try:
        return requests.delete(
            f"{API_URL}/history/session/{session_id}",
            headers=get_headers()
        )
    except:
        return None