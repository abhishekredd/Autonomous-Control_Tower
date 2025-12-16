# frontend/pages/dashboard.py
import streamlit as st
import pandas as pd
import html
from datetime import datetime
from utils import fetch_api, is_authenticated   # ✅ use helpers

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Autonomous Control Tower - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

def styled_table_html(df: pd.DataFrame, table_id: str = None):
    html_table = df.to_html(classes="premium-table", index=False, justify="left", border=0, escape=True)
    if table_id:
        html_table = html_table.replace('class="premium-table"', f'class="premium-table" id="{table_id}"')
    wrapper = f'<div class="premium-table-wrapper">{html_table}</div>'
    return wrapper

# ---------------- FETCH DASHBOARD DATA ----------------
shipments = fetch_api("/shipments") if is_authenticated() else None
risks = fetch_api("/risks") if is_authenticated() else None

# ✅ simulations must be fetched per shipment, not globally
simulations = None
if is_authenticated() and shipments:
    # take the first shipment for dashboard context
    first_id = shipments[0]["id"]
    simulations = fetch_api(f"/simulations/shipment/{first_id}")

# ---------------- HEADER ----------------
st.markdown("<h1 style='margin-bottom:6px;'>📊 Autonomous Control Tower — Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<div style='height:6px; width:220px; border-radius:6px; background: linear-gradient(90deg,#2563EB,#3B82F6); margin-bottom:16px;'></div>", unsafe_allow_html=True)

tabs = st.tabs(["Overview", "Risks", "Simulations"])
# ---------------- TAB 1: OVERVIEW ----------------
with tabs[0]:
    st.subheader("Overview")

    if not is_authenticated():
        st.info("Sign in to view dashboard data")
    else:
        if shipments:
            df_shipments = pd.DataFrame(shipments)
            total = len(df_shipments)
            at_risk = len(df_shipments[df_shipments['is_at_risk'] == True])
            delayed = len(df_shipments[df_shipments['status'] == 'delayed'])
            arrived = len(df_shipments[df_shipments['status'] == 'arrived'])

            cols = st.columns(4)
            metrics = [
                ("Total Shipments", total, "Total rows returned"),
                ("At Risk", at_risk, "High / Critical risk"),
                ("Delayed", delayed, "Status = Delayed"),
                ("Arrived", arrived, "Status = Arrived")
            ]

            for col, (title, value, sub) in zip(cols, metrics):
                col.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #2563EB, #3B82F6);
                        border-radius: 12px;
                        padding: 16px;
                        color: white;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                        text-align: center;
                        margin-bottom: 12px;
                    ">
                        <div style="font-size:14px; font-weight:600; margin-bottom:6px;">{html.escape(title)}</div>
                        <div style="font-size:28px; font-weight:700; margin-bottom:4px;">{html.escape(str(value))}</div>
                        <div style="font-size:12px; opacity:0.9;">{html.escape(sub)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        if shipments:
            st.markdown("<h4 style='margin-top:10px;'>🚢 Shipments</h4>", unsafe_allow_html=True)
            st.markdown(styled_table_html(pd.DataFrame(shipments), table_id="dashboard-shipments"), unsafe_allow_html=True)

# ---------------- TAB 2: RISKS ----------------
with tabs[1]:
    st.subheader("Risks")

    if not is_authenticated():
        st.info("Sign in to view risks")
    else:
        if risks:
            df_risks = pd.DataFrame(risks)
            st.markdown(styled_table_html(df_risks, table_id="dashboard-risks"), unsafe_allow_html=True)
        else:
            st.info("No risks data available.")

# ---------------- TAB 3: SIMULATIONS ----------------
with tabs[2]:
    st.subheader("Simulations")

    if not is_authenticated():
        st.info("Sign in to view simulations")
    else:
        if simulations:
            df_sims = pd.DataFrame(simulations)
            st.markdown(styled_table_html(df_sims, table_id="dashboard-simulations"), unsafe_allow_html=True)
        else:
            st.info("No simulations data available.")

# ---------------- FOOTER ----------------
st.markdown("<hr/>", unsafe_allow_html=True)
st.caption(f"Autonomous Control Tower — Dashboard Module • Last updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
