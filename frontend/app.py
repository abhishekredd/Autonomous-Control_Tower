# frontend/app.py
import streamlit as st
import requests
from utils import is_authenticated   # ✅ import helper

API_BASE = "http://api:8000/api/v1"

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Autonomous Control Tower",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ---------------- SIDEBAR AUTH ----------------
with st.sidebar:
    st.markdown("### Auth")
    if not is_authenticated():
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="admin")
        if st.button("Sign in"):
            try:
                resp = requests.post(f"{API_BASE}/auth/login", json={"username": username, "password": password}, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                token = data.get("access_token")
                if token:
                    st.session_state["jwt_token"] = token
                    st.success("Signed in")
                else:
                    st.error("No access_token in response")
            except Exception as e:
                st.error(f"Login failed: {e}")
    else:
        st.success("Signed in")
        if st.button("Sign out"):
            st.session_state.pop("jwt_token", None)
            st.experimental_rerun()

# ---------------- MAIN APP ----------------
st.markdown("<h1>🛰️ Autonomous Control Tower</h1>", unsafe_allow_html=True)
st.write("Use the sidebar to navigate to Dashboard or Shipments.")
