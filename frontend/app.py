
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import html
import time

st.set_page_config(
    page_title="Autonomous Control Tower",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)


def styled_table(df, table_id=None):
    """Return HTML for a DataFrame with premium-table class (no index)."""

    html_table = df.to_html(classes="premium-table", border=0, index=False, escape=False)

    if table_id:
        html_table = html_table.replace('class="premium-table"', f'class="premium-table" id="{table_id}"')
    return html_table


st.markdown(
    """
    <style>



    /* Title + underline */
    .premium-header { 
        font-size: 1.9rem; 
        font-weight:700; 
        color:#111827; 
        margin:0 0 6px 0; 
    }
    .premium-underline { 
        width:160px; height:5px; border-radius:6px;
        background: linear-gradient(90deg,#6D28D9,#8B5CF6); 
        margin-bottom:18px; 
    }

    /* Remove sidebar padding */
    .sidebar .block-container {
        padding-top: 0rem !important;
    }
    .alert-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 14px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    border-left: 6px solid #8B5CF6;
}

.alert-title {
    font-size: 1rem;
    font-weight: 700;
    color: #111827;
}

.alert-desc {
    font-size: 0.9rem;
    color: #4B5563;
    margin-top: 4px;
}

.alert-location {
    display: inline-block;
    background: #F3F4F6;
    padding: 4px 10px;
    border-radius: 8px;
    margin-top: 6px;
    font-size: 0.8rem;
    color: #374151;
}

.alert-severity {
    font-weight: 700;
    font-size: 0.9rem;
    padding: 6px 12px;
    border-radius: 8px;
}

.alert-high { background:#FEE2E2; color:#B91C1C; }
.alert-medium { background:#FEF3C7; color:#B45309; }
.alert-critical { background:#FECACA; color:#7F1D1D; }

.alert-time {
    font-size: 0.8rem;
    color: #6B7280;
    margin-top: 6px;
}

.alert-btn {
    display:inline-block;
    background: linear-gradient(90deg,#6D28D9,#8B5CF6);
    padding: 8px 16px;
    border-radius:8px;
    color:white !important;
    font-weight:600;
    text-align:center;
    margin-right:10px;
    cursor:pointer;
}
.alert-btn:hover {
    opacity:0.9;
}




    /* nav-btn will be added via JS into the shadow DOM so style it here */
    .nav-btn {
        width: 100% !important;
        background: linear-gradient(90deg, #6D28D9, #7C3AED) !important;
        color: white !important;
        padding: 12px 16px !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: none !important;
        margin-bottom: 10px !important;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06) !important;
        text-align: left !important;
        cursor: pointer !important;
        transition: transform .12s ease, box-shadow .12s ease;
    }

    .nav-btn:hover {
        background: linear-gradient(90deg, #7C3AED, #8B5CF6) !important;
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.12) !important;
    }

    .nav-btn:active {
        background: linear-gradient(90deg, #5B21B6, #6D28D9) !important;
        transform: scale(0.99);
    }

    /* In case standard .stButton selector is reachable */
    .sidebar .stButton>button {
        width: 100% !important;
    }
  
.shipment-mini-card {
    background: linear-gradient(135deg, #ffffff 0%, #f5f3ff 100%);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: 0 6px 18px rgba(109,40,217,0.12);
    border-left: 6px solid #7C3AED;
}

.shipment-mini-title {
    font-size: 0.90rem;
    font-weight: 600;
    color: #4B5563;
    margin-bottom: 6px;
}

.shipment-mini-value {
    font-size: 1.35rem;
    font-weight: 800;
    color: #111827;
}

.shipment-mini-delta {
    font-size: 0.85rem;
    margin-top: 6px;
    font-weight: 600;
}

.shipment-delta-up {
    color: #10B981;
}

.shipment-delta-down {
    color: #EF4444;
}

.shipment-delta-neutral {
    color: #6B7280;
}




.kpi-card {
    background: linear-gradient(135deg, #4C1D95, #6D28D9, #8B5CF6, #A78BFA);
    padding: 18px;
    border-radius: 14px;
    color: white !important;
    box-shadow: 0 12px 28px rgba(88,28,135,0.35);
    border: 1px solid rgba(255,255,255,0.18);
    transition: transform .15s ease, box-shadow .15s ease;
}
.kpi-card:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 18px 42px rgba(124,58,237,0.45);
}


.kpi-card:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 14px 35px rgba(124,58,237,0.35);
}

.kpi-title {
    font-size: 1rem;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.95);
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

.kpi-value {
    font-size: 2.1rem;
    font-weight: 900;
    color: #ffffff;
    text-shadow: 0 0 6px rgba(255,255,255,0.55);
}

.kpi-delta {
    font-size: 1rem;
    margin-top: 8px;
    font-weight: 700;
}

.delta-up {
    color: #C6F6D5 !important; /* green highlight */
    text-shadow: 0 0 6px rgba(16,185,129,0.6);
}

.delta-down {
    color: #FECACA !important; /* red highlight */
    text-shadow: 0 0 6px rgba(239,68,68,0.6);
}

.delta-neutral {
    color: #E5E7EB !important; /* light gray */
    text-shadow: 0 0 6px rgba(229,231,235,0.4);
}


    section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: linear-gradient(90deg, #6D28D9, #7C3AED) !important;
    color: white !important;
    padding: 12px 16px !important;
    border-radius: 10px !important;
    border: none !important;
    font-weight: 600 !important;
    margin-bottom: 10px !important;
    text-align: left !important;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06) !important;
    transition: 0.15s ease-in-out;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(90deg, #7C3AED, #8B5CF6) !important;
    transform: translateY(-2px);
}

section[data-testid="stSidebar"] .stButton > button:active {
    background: linear-gradient(90deg, #5B21B6, #6D28D9) !important;
    transform: scale(0.98);
}



    .activity-card {
        background: linear-gradient(180deg,#ffffff,#fbfbfd);
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 4px 12px rgba(2,6,23,0.06);
        margin-bottom: 10px;
        border-left: 6px solid #7C3AED;
    }
    .activity-title { font-weight:700; color:#111827; font-size:0.95rem; margin-bottom:4px; }
    .activity-meta { color:#6B7280; font-size:0.88rem; }
    .activity-time { color:#9CA3AF; font-size:0.82rem; }



    table.premium-table {
        border-collapse: collapse;
        width: 100%;
        border-radius: 10px;
        overflow: hidden;
        font-size: 0.95rem;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.03);
    }

    /* Header */
    table.premium-table thead th {
        background: linear-gradient(90deg,#6D28D9,#8B5CF6) !important;
        color: white !important;
        padding: 12px 14px !important;
        font-weight: 700 !important;
        border-bottom: 2px solid rgba(255,255,255,0.08) !important;
        text-align: left !important;
    }

    /* Body rows */
    table.premium-table tbody tr:nth-child(even) {
        background: #F7F5FF;
    }

    table.premium-table tbody tr:hover {
        background: #EFE9FF;
    }

    /* Cells */
    table.premium-table td {
        padding: 10px 14px;
        border-bottom: 1px solid #F1F2F4;
        color: #374151;
    }

    /* small responsive tweaks */
    @media (max-width: 800px) {
        table.premium-table thead th, table.premium-table td {
            padding: 8px 10px;
            font-size: 0.9rem;
        }
        .premium-header { font-size: 1.4rem; }
    }

 

    .shipment-detail-card {
        background: linear-gradient(90deg, rgba(109,40,217,0.95), rgba(124,58,237,0.95));
        color: white;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 12px 30px rgba(99,102,241,0.12);
        margin-bottom: 12px;
    }

    .shipment-detail-title { font-weight:800; font-size:1.05rem; margin-bottom:8px; }
    .shipment-detail-meta { font-size:0.95rem; color: rgba(255,255,255,0.92); margin-bottom:6px; }
    .shipment-metric { display:inline-block; background: rgba(255,255,255,0.08); padding:6px 10px; border-radius:8px; margin-right:8px; font-weight:700; }

    </style>
    """,
    unsafe_allow_html=True,
)

if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def nav_button(label, page_key):
    if st.sidebar.button(label, key=f"nav_{page_key}"):
        st.session_state.page = page_key
        st.rerun()



# -------- Sidebar --------
st.sidebar.markdown("<h3 style='text-align:center;margin-bottom:6px'>🚢 Control Tower</h3>", unsafe_allow_html=True)
st.sidebar.markdown("<hr/>", unsafe_allow_html=True)

nav_button("📊 Dashboard", "Dashboard")
nav_button("🚢 Shipments", "Shipments")
nav_button("⚠️ Risks", "Risks")
nav_button("🔮 Simulations", "Simulations")
nav_button("👥 Digital Twin", "Digital Twin")

st.sidebar.markdown("<hr/>", unsafe_allow_html=True)
st.sidebar.subheader("Real-time Controls")
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
refresh_rate = st.sidebar.slider("Refresh rate (seconds)", 5, 60, 30)

if st.sidebar.button("🔄 Manual Refresh"):
    st.experimental_rerun()

st.sidebar.markdown("<hr/>", unsafe_allow_html=True)
st.sidebar.subheader("System Status")
st.sidebar.progress(0.85, text="Operational: 85%")
st.sidebar.caption("Last updated: " + datetime.now().strftime("%H:%M:%S"))

# ------------------ DASHBOARD PAGE ------------------
if st.session_state.page == "Dashboard":


    st.markdown("""
        <h1 style="
            text-align:center;
            font-weight:900;
            font-size:2.3rem;
            color:#1f2937;
            margin-bottom:6px;">
            Autonomous Control Tower Dashboard
        </h1>
        <div style="height:4px; width: 1500px; background:#6366F1; margin:0 auto 28px auto; border-radius:6px;"></div>
    """, unsafe_allow_html=True)

  
    st.markdown("""
        <div style="font-size:1.45rem; font-weight:800; display:flex; align-items:center;">
            <div style="width:4px; height:27px; background:#7C3AED; border-radius:4px; margin-right:8px;"></div>
            Key Performance Indicators
        </div>
        <br/>
    """, unsafe_allow_html=True)

   
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown("""
            <div class='kpi-card'>
                <div class='kpi-title'>Total Shipments</div>
                <div class='kpi-value'>1,428</div>
                <div class='kpi-delta delta-up'>▲ +12% this month</div>
            </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown("""
            <div class='kpi-card'>
                <div class='kpi-title'>Risk Detection</div>
                <div class='kpi-value'>94%</div>
                <div class='kpi-delta delta-neutral'>Accuracy rate</div>
            </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown("""
            <div class='kpi-card'>
                <div class='kpi-title'>Cost Savings</div>
                <div class='kpi-value'>$1.2M</div>
                <div class='kpi-delta delta-up'>▲ Year to date</div>
            </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown("""
            <div class='kpi-card'>
                <div class='kpi-title'>Auto Actions</div>
                <div class='kpi-value'>847</div>
                <div class='kpi-delta delta-neutral'>Executed this month</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ======================================================
    #                 MAP + RECENT ACTIVITY
    # ======================================================

    map_col, activity_col = st.columns([2.3, 1])

    # ---------------- MAP LEFT ----------------
    with map_col:
        st.markdown("""
            <div style="font-size:1.45rem; font-weight:800; display:flex; align-items:center;">
                <div style="width:4px; height:27px; background:#10B981; border-radius:4px; margin-right:8px;"></div>
                🌍 Global Shipment Tracking
            </div>
            <br/>
        """, unsafe_allow_html=True)

        shipments = pd.DataFrame({
            'Shipment': ['SH-001', 'SH-002', 'SH-003', 'SH-004'],
            'Origin': ['Shanghai', 'Rotterdam', 'Singapore', 'Los Angeles'],
            'Destination': ['Rotterdam', 'New York', 'Dubai', 'Tokyo'],
            'Status': ['In Transit', 'Delayed', 'On Time', 'In Transit'],
            'Risk': ['High', 'Critical', 'Low', 'Medium'],
            'Lat': [31.2304, 51.9244, 1.3521, 34.0522],
            'Lon': [121.4737, 4.4777, 103.8198, -118.2437]
        })

        fig = px.scatter_mapbox(
            shipments,
            lat="Lat",
            lon="Lon",
            hover_name="Shipment",
            hover_data=["Origin", "Destination", "Status"],
            color="Risk",
            size=[20, 25, 15, 20],
            zoom=1.2,
            height=520,
            color_discrete_map={
                "High": "red",
                "Critical": "darkred",
                "Medium": "orange",
                "Low": "green"
            }
        )

        fig.update_layout(
            mapbox_style="open-street-map",
            margin=dict(l=0, r=0, t=0, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)

    # ---------------- RECENT ACTIVITY RIGHT ----------------
    with activity_col:

        st.markdown("""
            <div style="font-size:1.2rem; font-weight:800; display:flex; align-items:center;">
                <div style="width:6px; height:22px; background:#7C3AED; border-radius:4px; margin-right:8px;"></div>
                📋 Recent Activity
            </div>
            <br/>
        """, unsafe_allow_html=True)

        recent = [
            ("10:30", "SH-001", "Rerouted via alternate port", "Route Optimizer"),
            ("10:25", "SH-045", "Customs clearance expedited", "Action Executor"),
            ("10:20", "SH-089", "Risk detected: Port congestion", "Risk Detector"),
            ("10:15", "SH-112", "Mode switched to air freight", "Action Executor"),
            ("10:10", "SH-156", "Stakeholders notified of delay", "Stakeholder Comms"),
        ]

        for t, ship, act, agent in recent:
            st.markdown(
                f"""
                <div class='activity-card'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <div>
                            <div class='activity-title'>{act}</div>
                            <div class='activity-meta'>{ship} • {agent}</div>
                        </div>
                        <div class='activity-time'>{t}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True)





elif st.session_state.page == "Shipments":
    st.markdown("<div class='premium-header'>📦 Shipment Management</div>", unsafe_allow_html=True)
    st.markdown("<div class='premium-underline'></div>", unsafe_allow_html=True)

    # Search + Filters row (visual only - functionality preserved)
    s1, s2, s3, s4 = st.columns([2,1,1,1])
    with s1:
        search_term = st.text_input("Search Shipments", placeholder="Container #, Booking #")
    with s2:
        status_filter = st.selectbox("Status", ["All", "In Transit", "On Time", "Delayed", "Critical", "Completed", "Pending"])
    with s3:
        carrier_filter = st.selectbox("Mode", ["All", "Sea", "Air", "Rail"])
    with s4:
        if st.button("🔍 Apply Filters", use_container_width=True):
            st.experimental_rerun()

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Active Shipments</div>", unsafe_allow_html=True)

    shipments_data = pd.DataFrame({
        'ID': ['SH-001', 'SH-002', 'SH-003', 'SH-004', 'SH-005'],
        'Tracking': ['TRK789012', 'TRK789013', 'TRK789014', 'TRK789015', 'TRK789016'],
        'Origin': ['Shanghai', 'Rotterdam', 'Singapore', 'Los Angeles', 'Hamburg'],
        'Destination': ['Rotterdam', 'New York', 'Dubai', 'Tokyo', 'Shanghai'],
        'Status': ['In Transit', 'Delayed', 'On Time', 'In Transit', 'Pending'],
        'Mode': ['Sea', 'Sea', 'Air', 'Sea', 'Rail'],
        'ETA': ['2024-01-15', '2024-01-18', '2024-01-12', '2024-01-20', '2024-01-22'],
        'Risk': ['High', 'Critical', 'Low', 'Medium', 'Low']
    })

    df_show = shipments_data.copy()
    if status_filter != "All":
        df_show = df_show[df_show['Status'] == status_filter]
    if carrier_filter != "All":
        df_show = df_show[df_show['Mode'] == carrier_filter]
    if search_term:
        df_show = df_show[
            df_show['ID'].str.contains(search_term, case=False) |
            df_show['Origin'].str.contains(search_term, case=False) |
            df_show['Destination'].str.contains(search_term, case=False)
        ]

    # render styled table
    st.markdown(styled_table(df_show, table_id="active-shipments"), unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Shipment Details</div>", unsafe_allow_html=True)

    selected_shipment = st.selectbox("Select Shipment", shipments_data['ID'].tolist())
    if selected_shipment:
        # Example: find row and show a colorful gradient card with key metrics
        row = shipments_data[shipments_data['ID'] == selected_shipment].iloc[0]
        with st.container():
            st.markdown(
                f"""
                <div class="shipment-detail-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                        <div style="min-width:220px;">
                            <div class="shipment-detail-title">Shipment {html.escape(row['ID'])}</div>
                            <div class="shipment-detail-meta">{html.escape(row['Origin'])} → {html.escape(row['Destination'])}</div>
                            <div style="margin-top:8px;">
                                <span class="shipment-metric">Status: {html.escape(row['Status'])}</span>
                                <span class="shipment-metric">Mode: {html.escape(row['Mode'])}</span>
                                <span class="shipment-metric">ETA: {html.escape(row['ETA'])}</span>
                            </div>
                        </div>
                        <div style="min-width:200px;text-align:right;">
                            <div style="font-weight:800;font-size:1.1rem;">Risk</div>
                            <div style="margin-top:6px;font-weight:700;font-size:1.6rem;">{html.escape(row['Risk'])}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br/>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
        <div class="shipment-mini-card">
            <div class="shipment-mini-title">Current Location</div>
            <div class="shipment-mini-value">Pacific Ocean</div>
            <div class="shipment-mini-delta shipment-delta-up">↑ 34.0522° N, 118.2437° W</div>
        </div>

        <div class="shipment-mini-card">
            <div class="shipment-mini-title">Days in Transit</div>
            <div class="shipment-mini-value">12</div>
            <div class="shipment-mini-delta shipment-delta-up">↑ +1</div>
        </div>

        <div class="shipment-mini-card">
            <div class="shipment-mini-title">Distance Covered</div>
            <div class="shipment-mini-value">8,450 km</div>
            <div class="shipment-mini-delta shipment-delta-up">↑ 68%</div>
        </div>
    """, unsafe_allow_html=True)


        with c2:
             st.markdown(f"""
        <div class="shipment-mini-card">
            <div class="shipment-mini-title">Risk Score</div>
            <div class="shipment-mini-value">0.82</div>
            <div class="shipment-mini-delta shipment-delta-up">↑ High</div>
        </div>

        <div class="shipment-mini-card">
            <div class="shipment-mini-title">Estimated Delay</div>
            <div class="shipment-mini-value">18 hours</div>
            <div class="shipment-mini-delta shipment-delta-up">↑ +6h</div>
        </div>

        <div class="shipment-mini-card">
            <div class="shipment-mini-title">Autonomous Actions</div>
            <div class="shipment-mini-value">3</div>
            <div class="shipment-mini-delta shipment-delta-neutral">Today</div>
        </div>
    """, unsafe_allow_html=True)

        st.subheader("🚢 Shipment Timeline")
        timeline_data = pd.DataFrame({
            'Event': ['Departure', 'Port Entry', 'Customs Clearance', 'Current', 'Estimated Arrival'],
            'Date': ['2024-01-01', '2024-01-08', '2024-01-09', '2024-01-13', '2024-01-15'],
            'Status': ['Completed', 'Completed', 'In Progress', 'Current', 'Pending'],
            'Location': ['Shanghai', 'Singapore', 'Singapore', 'Pacific Ocean', 'Rotterdam']
        })
        # Render timeline as a styled table for consistent look
        st.markdown(styled_table(timeline_data, table_id="timeline-table"), unsafe_allow_html=True)


elif st.session_state.page == "Risks":
    st.markdown("<div class='premium-header'>⚠️ Risk Management</div>", unsafe_allow_html=True)
    st.markdown("<div class='premium-underline'></div>", unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown("<div class='kpi-card'><div class='kpi-title'>Active Risks</div><div class='kpi-value'>24</div><div class='kpi-delta delta-up'>▲ +3</div></div>", unsafe_allow_html=True)
    with r2:
        st.markdown("<div class='kpi-card'><div class='kpi-title'>Critical Risks</div><div class='kpi-value'>8</div><div class='kpi-delta delta-up'>▲ +2</div></div>", unsafe_allow_html=True)
    with r3:
        st.markdown("<div class='kpi-card'><div class='kpi-title'>Mitigations Applied</div><div class='kpi-value'>16</div><div class='kpi-delta delta-neutral'>67%</div></div>", unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.subheader("Risk Breakdown by Type")
    risk_types = pd.DataFrame({
        'Type': ['Port Congestion', 'Customs Delay', 'Quality Hold', 'Weather Impact', 'Equipment Failure', 'Other'],
        'Count': [8, 6, 4, 3, 2, 1],
        'Severity': ['High', 'High', 'Medium', 'Medium', 'Low', 'Low']
    })
    fig_risk = px.bar(risk_types, x='Type', y='Count', color='Severity',
                      color_discrete_map={'High': 'red', 'Medium':'orange', 'Low':'yellow'})
    st.plotly_chart(fig_risk, use_container_width=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.subheader("🚨 Recent Risk Alerts")
    alerts = pd.DataFrame({
        'Time': ['10:30', '10:25', '10:20', '10:15', '10:10'],
        'Shipment': ['SH-001', 'SH-045', 'SH-089', 'SH-112', 'SH-156'],
        'Risk Type': ['Port Congestion', 'Customs Delay', 'Weather Impact', 'Quality Hold', 'Port Congestion'],
        'Severity': ['High', 'Critical', 'Medium', 'Medium', 'High'],
        'Action Taken': ['Rerouted', 'Expedited Clearance', 'Schedule Adjusted', 'Remote Inspection', 'Monitoring'],
        'Status': ['Resolved', 'In Progress', 'Resolved', 'In Progress', 'Detected']
    })
    st.markdown(styled_table(alerts, table_id="alerts-table"), unsafe_allow_html=True)


elif st.session_state.page == "Simulations":
    st.markdown("<div class='premium-header'>🔮 Mitigation Simulations</div>", unsafe_allow_html=True)
    st.markdown("<div class='premium-underline'></div>", unsafe_allow_html=True)

    st.markdown("<div class='flat-title'>Digital Twin Simulations</div>", unsafe_allow_html=True)

    scenarios = [
        {
            "name": "Port Congestion Mitigation",
            "shipment": "SH-001",
            "risk": "Port congestion at Rotterdam",
            "options": [
                {"name": "Alternative Port", "time_savings": 24, "cost": 5000, "risk": 0.3},
                {"name": "Schedule Delay", "time_savings": -12, "cost": 1000, "risk": 0.5},
                {"name": "Mode Switch", "time_savings": 48, "cost": 15000, "risk": 0.2}
            ]
        },
        {
            "name": "Customs Delay Mitigation",
            "shipment": "SH-045",
            "risk": "Customs clearance delayed",
            "options": [
                {"name": "Expedited Service", "time_savings": 20, "cost": 2500, "risk": 0.4},
                {"name": "Additional Docs", "time_savings": 12, "cost": 500, "risk": 0.6}
            ]
        }
    ]

    for idx, scenario in enumerate(scenarios):
        with st.expander(f"📊 {scenario['name']} — {scenario['shipment']}"):
            st.markdown(f"**Risk:** {scenario['risk']}")
            options_df = pd.DataFrame(scenario["options"])
            st.markdown(styled_table(options_df, table_id=f"options-{idx}"), unsafe_allow_html=True)

          
            fig = px.scatter(
                options_df,
                x="cost",
                y="time_savings",
                size="risk",
                color="name",
                hover_name="name",
                title="Cost vs Time Savings"
            )
            fig.update_layout(height=360, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

            if st.button(f"Run Simulation for {scenario['shipment']}", key=f"sim_run_{idx}"):
                with st.spinner("Running simulation..."):
                    time.sleep(1.2)
                st.success("Simulation completed — recommended: Alternative Port")

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Simulation Summary</div>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("<div class='kpi-card'><div class='kpi-title'>Baseline Delay (hrs)</div><div class='kpi-value'>48</div><div class='kpi-delta delta-down'>▼ -30%</div></div>", unsafe_allow_html=True)
    with col_b:
        st.markdown("<div class='kpi-card'><div class='kpi-title'>AI Mitigated Delay (hrs)</div><div class='kpi-value'>12</div><div class='kpi-delta delta-neutral'>Projected</div></div>", unsafe_allow_html=True)
    with col_c:
        st.markdown("<div class='kpi-card'><div class='kpi-title'>Estimated Savings</div><div class='kpi-value'>$1.6M</div><div class='kpi-delta delta-up'>▲ +75%</div></div>", unsafe_allow_html=True)

elif st.session_state.page == "Digital Twin":
    st.markdown("<div class='premium-header'>👥 Digital Twin & MCP Agents</div>", unsafe_allow_html=True)
    st.markdown("<div class='premium-underline'></div>", unsafe_allow_html=True)

    st.markdown("<div class='flat-title'>🤖 MCP Agent Network</div>", unsafe_allow_html=True)

    agents = pd.DataFrame({
        'Agent': ['Central Orchestrator', 'Risk Detector', 'Route Optimizer', 'Stakeholder Comms', 'Simulation Engine', 'Action Executor'],
        'Status': ['Active', 'Active', 'Active', 'Active', 'Active', 'Active'],
        'CPU %': ['15%','8%','12%','6%','22%','9%'],
        'Memory': ['512MB','256MB','384MB','192MB','768MB','320MB'],
        'Messages': ['1,425','892','764','543','672','456'],
        'Uptime': ['7d 12h']*6
    })
    st.markdown(styled_table(agents, table_id="agents-table"), unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("<div class='flat-title'>📡 MCP Message Flow</div>", unsafe_allow_html=True)
    messages = pd.DataFrame({
        'Time': ['10:30:01','10:30:03','10:30:05','10:30:07','10:30:10'],
        'From': ['Risk Detector','Orchestrator','Simulation Engine','Orchestrator','Action Executor'],
        'To': ['Orchestrator','Simulation Engine','Orchestrator','Action Executor','Orchestrator'],
        'Message': ['Risk detected: Port congestion','Simulate mitigation options','3 options simulated, best: reroute','Execute reroute action','Action completed successfully'],
        'Context': ['SH-001']*5
    })
    st.markdown(styled_table(messages, table_id="messages-table"), unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("<div class='flat-title'>🔄 Real-time Agent Activity</div>", unsafe_allow_html=True)

    nodes = pd.DataFrame({
        'Node': ['Orchestrator','Risk Detector','Route Optimizer','Stakeholder Comms','Simulation Engine','Action Executor'],
        'X': [0,-2,0,2,-2,2],
        'Y': [0,1,2,1,-1,-1],
        'Size': [30,20,20,20,25,25],
        'Color': ['#FF6B6B','#4ECDC4','#45B7D1','#96CEB4','#FFEAA7','#DDA0DD']
    })
    edges = pd.DataFrame({
        'From': ['Orchestrator','Orchestrator','Orchestrator','Risk Detector','Route Optimizer','Simulation Engine'],
        'To':   ['Risk Detector','Route Optimizer','Stakeholder Comms','Simulation Engine','Action Executor','Action Executor']
    })


    fig_net = go.Figure()
    for _, edge in edges.iterrows():
        from_node = nodes[nodes['Node'] == edge['From']].iloc[0]
        to_node = nodes[nodes['Node'] == edge['To']].iloc[0]
        fig_net.add_trace(go.Scatter(x=[from_node['X'], to_node['X']], y=[from_node['Y'], to_node['Y']],
                                     mode='lines', line=dict(width=2,color='#888'), hoverinfo='none'))
    fig_net.add_trace(go.Scatter(x=nodes['X'], y=nodes['Y'], mode='markers+text', text=nodes['Node'],
                                 textposition="bottom center",
                                 marker=dict(size=nodes['Size'], color=nodes['Color'], line=dict(width=2, color='white'))))
    fig_net.update_layout(title="MCP Agent Communication Network", showlegend=False, hovermode='closest',
                          margin=dict(b=0,l=0,r=0,t=40), xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                          yaxis=dict(showgrid=False, zeroline=False, showticklabels=False), height=420)
    st.plotly_chart(fig_net, use_container_width=True)


st.markdown("<hr/>", unsafe_allow_html=True)
st.caption("Autonomous Control Tower v1.0 | Real-time monitoring active | Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))