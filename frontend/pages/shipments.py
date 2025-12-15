# frontend/pages/shipments.py
import streamlit as st
import pandas as pd
import html
from datetime import datetime, timedelta
from utils import fetch_api, is_authenticated   # ✅ use helpers

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Autonomous Control Tower - Shipments",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

def styled_table_html(df: pd.DataFrame, table_id: str = None):
    html_table = df.to_html(classes="premium-table", index=False, justify="left", border=0, escape=True)
    if table_id:
        html_table = html_table.replace('class="premium-table"', f'class="premium-table" id="{table_id}"')
    wrapper = f'<div class="premium-table-wrapper">{html_table}</div>'
    return wrapper
# ---------------- FETCH SHIPMENTS ----------------
shipments = fetch_api("/shipments") if is_authenticated() else None
if shipments:
    df_shipments = pd.DataFrame(shipments)
    st.session_state.shipments = df_shipments
else:
    st.session_state.shipments = pd.DataFrame()

# ---------------- HEADER ----------------
st.markdown("<h1 style='margin-bottom:6px;'>🚢 Autonomous Control Tower — Shipments</h1>", unsafe_allow_html=True)
st.markdown("<div style='height:6px; width:220px; border-radius:6px; background: linear-gradient(90deg,#6D28D9,#8B5CF6); margin-bottom:16px;'></div>", unsafe_allow_html=True)

tabs = st.tabs(["All Shipments", "Create Shipment", "Shipment Details"])
# ---------------- TAB 1: ALL SHIPMENTS ----------------
with tabs[0]:
    st.subheader("All Shipments")
    if st.session_state.shipments.empty:
        st.info("No shipments available.")
    else:
        df_all = st.session_state.shipments.copy()
        st.markdown(styled_table_html(df_all, table_id="all-shipments"), unsafe_allow_html=True)

        # KPI metrics
        total = len(df_all)
        at_risk = len(df_all[df_all['is_at_risk'] == True])
        delayed = len(df_all[df_all['status'] == 'delayed'])
        arrived = len(df_all[df_all['status'] == 'arrived'])

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
                    background: linear-gradient(135deg, #6D28D9, #8B5CF6);
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

# ---------------- TAB 2: CREATE SHIPMENT ----------------
with tabs[1]:
    st.subheader("Create New Shipment")
    with st.form("create_shipment_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            tracking = st.text_input("Tracking Number")
            sid = st.text_input("Reference Number")
            origin = st.text_input("Origin")
            destination = st.text_input("Destination")
            mode = st.selectbox("Mode", ["air", "sea", "rail", "multimodal"])
        with c2:
            status = st.selectbox("Status", ["pending", "in_transit", "delayed", "arrived"])
            eta = st.date_input("ETA", datetime.now() + timedelta(days=10))
            value = st.text_input("Value", "100000")
        submitted = st.form_submit_button("Create Shipment", use_container_width=True)

    if submitted and is_authenticated():
        # Validate required fields
        missing = []
        for name, val in [("tracking_number", tracking), ("origin", origin), ("destination", destination), ("mode", mode)]:
            if not val:
                missing.append(name)

        if missing:
            st.error(f"Missing required fields: {', '.join(missing)}")
        else:
            # build a naive datetime for estimated_arrival (no tzinfo) to match backend DB expectations
            try:
                _dt = datetime
                est_dt = _dt.combine(eta, _dt.utcnow().time())
            except Exception:
                est_dt = None

            try:
                parsed_value = float(value.replace("$", "").replace("K", "000"))
            except Exception:
                parsed_value = None

            payload = {
                "tracking_number": tracking,
                "reference_number": sid or None,
                "origin": origin,
                "destination": destination,
                "mode": mode,
                # backend sets status itself; sending status is optional and ignored by Pydantic
                "status": status,
                "estimated_arrival": est_dt.isoformat() if est_dt is not None else None,
                "value": parsed_value
            }
        resp = fetch_api("/shipments", method="POST", payload=payload)
        if resp:
            st.success(f"Shipment {resp['id']} created successfully.")
    elif submitted:
        st.warning("Please sign in to create shipments")
# ---------------- TAB 3: SHIPMENT DETAILS ----------------
with tabs[2]:
    st.subheader("Shipment Details")
    if st.session_state.shipments.empty:
        st.info("No shipments available. Create one in the 'Create Shipment' tab.")
    else:
        sel_id = st.selectbox("Select Shipment ID", st.session_state.shipments["id"].tolist(), index=0)
        shipment = fetch_api(f"/shipments/{sel_id}") if is_authenticated() else None
        if shipment:
            # Gradient card with core shipment info
            st.markdown(
                f"""
                <div class="shipment-detail-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                        <div style="min-width:220px;">
                            <div class="shipment-detail-title">Shipment {html.escape(str(shipment['id']))}</div>
                            <div class="shipment-detail-meta">{html.escape(shipment['origin'])} → {html.escape(shipment['destination'])}</div>
                            <div style="margin-top:8px;">
                                <span class="shipment-metric">Status: {html.escape(shipment['status'])}</span>
                                <span class="shipment-metric">Mode: {html.escape(shipment['mode'])}</span>
                                <span class="shipment-metric">ETA: {html.escape(str(shipment.get('estimated_arrival','N/A')))}</span>
                            </div>
                        </div>
                        <div style="min-width:240px;text-align:right;">
                            <div style="font-weight:800;font-size:1.0rem;">Risk Score</div>
                            <div style="margin-top:8px;font-weight:800;font-size:1.6rem;">{html.escape(str(shipment.get('risk_score','0.0')))}</div>
                            <div style="margin-top:8px;font-size:0.9rem;opacity:0.95;">Tracking: {html.escape(shipment['tracking_number'])}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Risks
            if shipment.get("risks"):
                st.markdown("<h4 style='margin-top:6px;'>⚠️ Risk Summary</h4>", unsafe_allow_html=True)
                risk_df = pd.DataFrame(shipment["risks"])
                st.markdown(styled_table_html(risk_df, table_id="risk-table"), unsafe_allow_html=True)

            # Simulations
            if is_authenticated():
                simulations = fetch_api(f"/simulations/shipment/{sel_id}")
                if simulations:
                    st.markdown("<h4 style='margin-top:6px;'>🔮 Simulations</h4>", unsafe_allow_html=True)
                    for sim in simulations:
                        st.markdown(f"**Simulation:** {sim['simulation_type']} — {sim['status']}")
                        if sim.get("results"):
                            results_df = pd.DataFrame(sim["results"])
                            st.markdown(styled_table_html(results_df, table_id=f"sim-{sim['id']}"), unsafe_allow_html=True)

            # Action buttons
            ab1, ab2 = st.columns(2)
            with ab1:
                if st.button("🔄 Trigger Risk Check", use_container_width=True):
                    if is_authenticated():
                        payload = {
                            "shipment_id": sel_id,
                            "simulation_type": "mitigation_analysis",   # ✅ valid enum
                            "parameters": {"shipment_id": sel_id, "source": "frontend", "risk_type": "CUSTOMS_DELAY"},
                            "scenario_description": f"Risk check for shipment {sel_id}"
                        }
                        resp = fetch_api("/simulations/", method="POST", payload=payload)
                        if resp:
                            st.success(f"Risk check simulation created (id={resp.get('id')})")
                    else:
                        st.warning("Please sign in to trigger risk checks")
            with ab2:
                if st.button("📊 Run Mitigation Simulation", use_container_width=True):
                    if is_authenticated():
                        payload = {"shipment_id": sel_id, "risk_data": {"risk_type": "PORT_CONGESTION"}}
                        resp = fetch_api("/simulations/mitigation/run", method="POST", payload=payload)
                        if resp:
                            st.success(f"Simulation started: ID {resp['simulation_id']}")
                    else:
                        st.warning("Please sign in to run simulations")
# ---------------- FOOTER ----------------
st.markdown("<hr/>", unsafe_allow_html=True)
st.caption(f"Autonomous Control Tower — Shipments Module • Last updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
