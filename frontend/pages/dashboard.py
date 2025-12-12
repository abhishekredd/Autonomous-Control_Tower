import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta


st.set_page_config(
    page_title="Control Tower Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------- GLOBAL CSS -----------------------
st.markdown(
    """
    <style>

    .metric-box {
        flex: 1 1 0;
        padding: 14px;
        border-radius: 12px;
        color: white;
        box-shadow: 0 8px 30px rgba(2,6,23,0.10);
        min-height: 78px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .metric-title {
        font-size: 0.85rem;
        font-weight: 700;
        opacity: 0.95;
    }

    .metric-value {
        font-size: 1.2rem;
        font-weight: 800;
    }

    .metric-delta {
        font-size: 0.78rem;
        opacity: 0.92;
        font-weight: 700;
        margin-top: 3px;
    }

    .m-purple { background: linear-gradient(135deg,#6D28D9,#7C3AED); }
    .m-blue   { background: linear-gradient(135deg,#0EA5E9,#2DD4BF); }
    .m-amber  { background: linear-gradient(135deg,#F59E0B,#F97316); }
    .m-green  { background: linear-gradient(135deg,#10B981,#34D399); }

    table.premium-table {
        border-collapse: collapse;
        width: 100%;
        border-radius: 10px;
        font-size: 0.95rem;
        overflow: hidden;
        box-shadow: 0 8px 30px rgba(2,6,23,0.04);
    }
    table.premium-table thead tr th {
        background: linear-gradient(90deg,#6D28D9,#8B5CF6);
        color: white;
        padding: 12px;
        font-weight: 700;
        text-align: left;
    }
    table.premium-table tbody tr:nth-child(even) {
        background: #F7F5FF;
    }
    table.premium-table tbody tr:hover {
        background: #EFE9FF;
    }
    table.premium-table td {
        padding: 10px 14px;
        border-bottom: 1px solid #EEE;
        color: #111827;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------- TABLE HELPER -------------------------
def premium_table_html(df: pd.DataFrame, table_id: str = None) -> str:
    html = df.to_html(classes="premium-table", border=0, index=False, escape=False)
    if table_id:
        html = html.replace('class="premium-table"', f'class="premium-table" id="{table_id}"')
    return html


# --------------------------- SAMPLE DATA ----------------------------
status_data = pd.DataFrame({
    "Status": ["In Transit", "Delayed", "At Risk", "Completed", "Pending"],
    "Count": [89, 18, 24, 45, 12]
})

risk_data = pd.DataFrame({
    "Type": ["Port Congestion", "Customs Delay", "Quality Hold", "Weather Impact", "Equipment Failure", "Other"],
    "Count": [8, 6, 4, 3, 2, 1],
    "Severity": ["High", "High", "Medium", "Medium", "Low", "Low"]
})

activity_data = pd.DataFrame({
    "Time": ["10:30", "10:25", "10:20", "10:15", "10:10", "10:05", "10:00"],
    "Shipment": ["SH-001", "SH-045", "SH-089", "SH-112", "SH-156", "SH-201", "SH-234"],
    "Activity": [
        "Rerouted via alternative port",
        "Customs clearance expedited",
        "Risk detected: Port congestion",
        "Mode switched to air freight",
        "Stakeholders notified of delay",
        "Quality inspection completed",
        "Shipment departed origin"
    ],
    "Agent": ["Route Optimizer", "Action Executor", "Risk Detector",
              "Action Executor", "Stakeholder Comms", "Quality Agent", "System"]
})

map_data = pd.DataFrame({
    "lat": [31.2304, 51.9244, 1.3521, 34.0522, 53.5511, 35.6762, 22.3193],
    "lon": [121.4737, 4.4777, 103.8198, -118.2437, 9.9937, 139.6503, 114.1694],
    "shipment": ["SH-001", "SH-002", "SH-003", "SH-004", "SH-005", "SH-006", "SH-007"],
    "status": ["In Transit", "Delayed", "In Transit", "In Transit", "At Risk", "In Transit", "Delayed"],
    "size": [20, 25, 15, 20, 30, 18, 22]
})


# --------------------------- HEADER ---------------------------
st.title("📊 Control Tower Dashboard")
st.markdown("---")

# ---------------------------- SIDEBAR -------------------------
with st.sidebar:
    st.header("Filters")
    st.date_input("Date Range", (datetime.now() - timedelta(days=7), datetime.now()))
    st.multiselect("Status", ["All", "In Transit", "Delayed", "At Risk", "Completed"], default=["In Transit", "Delayed"])
    st.multiselect("Risk Level", ["All", "Low", "Medium", "High", "Critical"], default=["High", "Critical"])
    st.button("🔄 Refresh Data", use_container_width=True)


# ------------------------ METRIC CARDS ------------------------
col1, col2, col3, col4 = st.columns(4, gap="small")

with col1:
    st.markdown("""
    <div class="metric-box m-purple">
        <div class="metric-title">Active Shipments</div>
        <div class="metric-value">142</div>
        <div class="metric-delta">+12</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-box m-amber">
        <div class="metric-title">At Risk</div>
        <div class="metric-value">24</div>
        <div class="metric-delta">▲ +3</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-box m-blue">
        <div class="metric-title">Delayed</div>
        <div class="metric-value">18</div>
        <div class="metric-delta">▼ -2</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-box m-green">
        <div class="metric-title">On-Time %</div>
        <div class="metric-value">87%</div>
        <div class="metric-delta">▲ +2%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")


# ---------------------- MAP + RISK CHART -----------------------
c1, c2 = st.columns([1, 1], gap="large")

with c1:
    st.subheader("🌍 Global Shipment Tracking")
    fig_map = px.scatter_mapbox(
        map_data,
        lat="lat",
        lon="lon",
        hover_name="shipment",
        hover_data=["status"],
        size="size",
        color="status",
        color_discrete_map={
            "In Transit": "#2E86AB",
            "Delayed": "#E76F51",
            "At Risk": "#F4A261"
        },
        zoom=1,
        height=550
    )
    fig_map.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    st.plotly_chart(fig_map, use_container_width=True)

with c2:
    st.subheader("⚠️ Risks by Type")
    fig_risk = px.bar(
        risk_data,
        x="Type",
        y="Count",
        color="Severity",
        color_discrete_map={
            "High": "#E63946",
            "Medium": "#F4A261",
            "Low": "#2A9D8F"
        }
    )
    fig_risk.update_layout(height=360)
    st.plotly_chart(fig_risk, use_container_width=True)

st.markdown("---")


# ---------------------- RECENT ACTIVITY (ONLY ONCE) ----------------------
st.subheader("🔄 Recent Activity")
st.markdown(premium_table_html(activity_data), unsafe_allow_html=True)

st.markdown("---")


# ---------------------- FOOTER ----------------------
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("Dashboard UI upgraded — Map style: open-street-map")