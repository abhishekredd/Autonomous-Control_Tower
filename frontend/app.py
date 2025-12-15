import streamlit as st
import requests
from utils import is_authenticated

API_BASE = "http://api:8000/api/v1"

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Autonomous Control Tower",
    page_icon="🛰️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------- GLOBAL STYLES ----------------
st.markdown(
    """
    <style>
        .login-card {
            background: #ffffff;
            padding: 32px;
            border-radius: 16px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.10);
            width: 360px;
            text-align: center;
        }
        .login-subtle {
            font-size: 14px;
            opacity: 0.6;
            margin-bottom: 18px;
        }
        .image-card {
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 10px 28px rgba(0,0,0,0.16);
            max-width: 620px;
            margin: 0 auto;
        }
        .nav-hint {
            text-align: center;
            margin-top: 20px;
            opacity: 0.75;
            font-size: 14px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- HEADER ----------------
st.markdown(
    """
    <h1 style='text-align:center;'>🛰️ Autonomous Control Tower</h1>
    <div style='height:6px; width:260px; border-radius:6px;
                background: linear-gradient(90deg,#2563EB,#3B82F6);
                margin:14px auto 30px auto;'></div>
    """,
    unsafe_allow_html=True,
)

# ---------------- AUTH FLOW ----------------
if not is_authenticated():
    st.markdown(
        """
        <div style="
            display:flex;
            justify-content:center;
            align-items:center;
            min-height:50vh;
        ">
            <div class="login-card">
                <h3>Sign in</h3>
                <div class="login-subtle">
                    Secure access to your control tower
                </div>
        """,
        unsafe_allow_html=True,
    )

    username = st.text_input("Username", value="admin", key="login_user")
    password = st.text_input("Password", type="password", value="admin", key="login_pass")

    if st.button("Sign in", use_container_width=True):
        try:
            resp = requests.post(
                f"{API_BASE}/auth/login",
                json={"username": username, "password": password},
                timeout=10,
            )
            resp.raise_for_status()
            token = resp.json().get("access_token")
            if token:
                st.session_state["jwt_token"] = token
                st.experimental_rerun()
            else:
                st.error("No access_token in response")
        except Exception as e:
            st.error(f"Login failed: {e}")

    st.markdown("</div></div>", unsafe_allow_html=True)

# ---------------- SIGNED-IN VIEW ----------------
else:
    st.markdown(
        """
        <div class="image-card">
        """,
        unsafe_allow_html=True,
    )

    st.image(
        "https://images.unsplash.com/photo-1578575437130-527eed3abbec",
        use_column_width=True,
        caption="Autonomous Supply Chain Control Tower",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="nav-hint">
            Please navigate to <b>Dashboard</b> or <b>Shipments</b> from the side panel
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    if st.button("Sign out", use_container_width=True):
        st.session_state.pop("jwt_token", None)
        st.experimental_rerun()
