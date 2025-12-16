# frontend/utils.py
import streamlit as st
import requests

API_BASE = "http://api:8000/api/v1"

def is_authenticated() -> bool:
    return bool(st.session_state.get("jwt_token"))

def fetch_api(endpoint: str, *, method: str = "GET", params: dict | None = None, payload: dict | None = None, timeout: int = 15):
    url = f"{API_BASE}{endpoint}"
    headers = {}
    token = st.session_state.get("jwt_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    print(f"[DEBUG] Calling {method} {url} with payload={payload} and headers={headers}")
    resp = requests.request(method, url, params=params, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json() if resp.content else None
