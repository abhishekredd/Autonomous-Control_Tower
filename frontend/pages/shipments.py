
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import html


st.set_page_config(
    page_title="Autonomous Control Tower - Shipments",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    /* ====== General page tweaks ====== */
    .stApp {
        background-color: #FAFBFE;
    }
    h1, h2, h3 { margin: 6px 0; }

    /* ====== Premium Table (A1) ====== */
    table.premium-table {
        border-collapse: collapse;
        width: 100%;
        border-radius: 10px;
        overflow: hidden;
        font-size: 0.95rem;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        margin-bottom: 14px;
    }
    table.premium-table thead th {
        background: linear-gradient(90deg, #6D28D9 0%, #8B5CF6 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        padding: 12px 14px !important;
        text-align: left !important;
        border-bottom: 2px solid rgba(255,255,255,0.06) !important;
    }
    table.premium-table tbody tr:nth-child(even) {
        background: #F6F3FF;
    }
    table.premium-table tbody tr:hover {
        background: #EFE9FF;
    }
    table.premium-table td {
        padding: 10px 14px;
        border-bottom: 1px solid #F1F2F6;
        color: #111827;
    }

    /* make the HTML table container responsive */
    .premium-table-wrapper {
        width: 100%;
        overflow-x: auto;
    }

    /* ====== Metric small colored boxes ====== */
    .metrics-row {
        display:flex;
        gap:14px;
        flex-wrap:wrap;
        margin-bottom:12px;
    }
    .metric-box {
        flex: 1 1 220px;               /* responsive: try keep same width */
        min-width: 180px;
        max-width: 100%;
        background: linear-gradient(135deg,#6D28D9 0%, #7C3AED 60%);
        color: white;
        padding: 12px 14px;
        border-radius: 10px;
        box-shadow: 0 10px 24px rgba(99,102,241,0.10);
        text-align: left;
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 700;
        opacity: 0.95;
    }
    .metric-value {
        font-size: 1.35rem;
        font-weight: 800;
        margin-top: 6px;
    }
    .metric-sub {
        font-size: 0.8rem;
        opacity: 0.88;
        margin-top: 4px;
    }

    /* ====== Shipment detail colorful card ====== */
    .shipment-detail-card {
        background: linear-gradient(90deg, rgba(109,40,217,0.98), rgba(124,58,237,0.98));
        color: white;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 18px 40px rgba(99,102,241,0.12);
        margin-bottom: 12px;
    }
    .shipment-detail-title {
        font-weight:800;
        font-size:1.05rem;
        margin-bottom:6px;
    }
    .shipment-detail-meta {
        font-size:0.95rem;
        color: rgba(255,255,255,0.95);
        margin-bottom:8px;
    }
    .shipment-metric-pill {
        display:inline-block;
        background: rgba(255,255,255,0.08);
        padding:6px 10px;
        border-radius:8px;
        margin-right:8px;
        font-weight:700;
        font-size:0.9rem;
    }

    /* ====== Small helper for full-width plotly charts in container ====== */
    .stPlotlyChart > div {
        width: 100% !important;
    }

    /* small screens tweak */
    @media (max-width: 880px) {
        .metrics-row { gap:10px; }
        .metric-box { flex: 1 1 100%; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def styled_table_html(df: pd.DataFrame, table_id: str = None):
    """
    Return an HTML block with the DataFrame rendered using premium styles.
    Uses pandas.DataFrame.to_html and wraps in a responsive container.
    """
   
    html_table = df.to_html(classes="premium-table", index=False, justify="left", border=0, escape=True)
    if table_id:
        html_table = html_table.replace('class="premium-table"', f'class="premium-table" id="{table_id}"')
    wrapper = f'<div class="premium-table-wrapper">{html_table}</div>'
    return wrapper


if "shipments" not in st.session_state:
    st.session_state.shipments = pd.DataFrame({
        'ID': ['SH-001', 'SH-002', 'SH-003', 'SH-004', 'SH-005'],
        'Tracking': ['TRK789012', 'TRK789013', 'TRK789014', 'TRK789015', 'TRK789016'],
        'Origin': ['Shanghai', 'Rotterdam', 'Singapore', 'Los Angeles', 'Hamburg'],
        'Destination': ['Rotterdam', 'New York', 'Dubai', 'Tokyo', 'Shanghai'],
        'Status': ['In Transit', 'Delayed', 'On Time', 'In Transit', 'At Risk'],
        'Mode': ['Sea', 'Sea', 'Air', 'Sea', 'Rail'],
        'ETA': ['2024-01-15', '2024-01-18', '2024-01-12', '2024-01-20', '2024-01-22'],
        'Risk': ['High', 'Critical', 'Low', 'Medium', 'High'],
        'Value': ['$500K', '$320K', '$150K', '$280K', '$420K']
    })


st.markdown("<h1 style='margin-bottom:6px;'>🚢 Autonomous Control Tower — Shipments</h1>", unsafe_allow_html=True)
st.markdown("<div style='height:6px; width:220px; border-radius:6px; background: linear-gradient(90deg,#6D28D9,#8B5CF6); margin-bottom:16px;'></div>", unsafe_allow_html=True)

tabs = st.tabs(["All Shipments", "Create Shipment", "Shipment Details"])


with tabs[0]:
    st.subheader("All Shipments")
    # filters row
    fcol1, fcol2, fcol3, fcol4 = st.columns([2.5, 1.2, 1.2, 1.2])
    with fcol1:
        search_q = st.text_input("Search (ID or Tracking)", placeholder="e.g. SH-001 or TRK789012")
    with fcol2:
        status_filter = st.selectbox("Status", ["All"] + sorted(st.session_state.shipments['Status'].unique().tolist()))
    with fcol3:
        mode_filter = st.selectbox("Mode", ["All"] + sorted(st.session_state.shipments['Mode'].unique().tolist()))
    with fcol4:
        risk_filter = st.selectbox("Risk", ["All"] + sorted(st.session_state.shipments['Risk'].unique().tolist()))

   
    df_all = st.session_state.shipments.copy()
    if status_filter != "All":
        df_all = df_all[df_all["Status"] == status_filter]
    if mode_filter != "All":
        df_all = df_all[df_all["Mode"] == mode_filter]
    if risk_filter != "All":
        df_all = df_all[df_all["Risk"] == risk_filter]
    if search_q:
        df_all = df_all[
            df_all["ID"].str.contains(search_q, case=False) |
            df_all["Tracking"].str.contains(search_q, case=False) |
            df_all["Origin"].str.contains(search_q, case=False) |
            df_all["Destination"].str.contains(search_q, case=False)
        ]


    st.markdown(styled_table_html(df_all, table_id="all-shipments"), unsafe_allow_html=True)

  
    st.subheader("📊 Shipment Statistics")
    total = len(df_all)
    at_risk = len(df_all[df_all['Risk'].isin(['High', 'Critical'])])
    delayed = len(df_all[df_all['Status'] == 'Delayed'])
    on_time = len(df_all[df_all['Status'] == 'On Time'])

    cols = st.columns(4)
    metrics = [
        ("Total Shipments", total, "Total rows returned"),
        ("At Risk", at_risk, "High / Critical risk"),
        ("Delayed", delayed, "Status = Delayed"),
        ("On Time", on_time, "Status = On Time")
    ]
    for col, (title, value, sub) in zip(cols, metrics):
        col.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-title">{html.escape(title)}</div>
                <div class="metric-value">{html.escape(str(value))}</div>
                <div class="metric-sub">{html.escape(sub)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )


with tabs[1]:
    st.subheader("Create New Shipment")
    st.markdown("<div style='margin-bottom:8px;'>Fill the form to create a shipment (will be stored in session for demo).</div>", unsafe_allow_html=True)

    with st.form("create_shipment_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            tracking = st.text_input("Tracking Number", value=f"TRK{int(datetime.now().timestamp()) % 1000000}")
            sid = st.text_input("Shipment ID", value=f"SH-{len(st.session_state.shipments) + 1:03d}")
            origin = st.text_input("Origin", "Shanghai")
            destination = st.text_input("Destination", "Rotterdam")
            mode = st.selectbox("Mode", ["Sea", "Air", "Rail", "Multimodal"])
        with c2:
            status = st.selectbox("Status", ["In Transit", "On Time", "Delayed", "At Risk", "Pending"])
            risk = st.selectbox("Risk", ["Low", "Medium", "High", "Critical"])
            eta = st.date_input("ETA", datetime.now() + timedelta(days=10))
            value = st.text_input("Value", "$100K")
        submitted = st.form_submit_button("Create Shipment", use_container_width=True)

    if submitted:
        new_row = {
            "ID": sid,
            "Tracking": tracking,
            "Origin": origin,
            "Destination": destination,
            "Status": status,
            "Mode": mode,
            "ETA": eta.strftime("%Y-%m-%d"),
            "Risk": risk,
            "Value": value
        }
    
        st.session_state.shipments = pd.concat([st.session_state.shipments, pd.DataFrame([new_row])], ignore_index=True)
        st.success(f"Shipment {sid} created and added to the list.")
     
        st.markdown(styled_table_html(st.session_state.shipments.tail(6), table_id="newly-created"), unsafe_allow_html=True)

   
    st.markdown("<div style='margin-top:12px; font-weight:700;'>Recent Shipments</div>", unsafe_allow_html=True)
    st.markdown(styled_table_html(st.session_state.shipments.tail(10).reset_index(drop=True), table_id="recent-shipments"), unsafe_allow_html=True)

with tabs[2]:
    st.subheader("Shipment Details")
    if st.session_state.shipments.empty:
        st.info("No shipments available. Create one in the 'Create Shipment' tab.")
    else:
  
        sel_col, preview_col = st.columns([2, 3])
        with sel_col:
            sel_id = st.selectbox("Select Shipment ID", st.session_state.shipments["ID"].tolist(), index=0)

        row = st.session_state.shipments[st.session_state.shipments["ID"] == sel_id].iloc[0]

      
        st.markdown(
            f"""
            <div class="shipment-detail-card">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">
                    <div style="min-width:220px;">
                        <div class="shipment-detail-title">Shipment {html.escape(row['ID'])}</div>
                        <div class="shipment-detail-meta">{html.escape(row['Origin'])} → {html.escape(row['Destination'])}</div>
                        <div style="margin-top:8px;">
                            <span class="shipment-metric-pill">Status: {html.escape(row['Status'])}</span>
                            <span class="shipment-metric-pill">Mode: {html.escape(row['Mode'])}</span>
                            <span class="shipment-metric-pill">ETA: {html.escape(str(row['ETA']))}</span>
                        </div>
                    </div>
                    <div style="min-width:240px;text-align:right;">
                        <div style="font-weight:800;font-size:1.0rem;">Risk</div>
                        <div style="margin-top:8px;font-weight:800;font-size:1.6rem;">{html.escape(row['Risk'])}</div>
                        <div style="margin-top:8px;font-size:0.9rem;opacity:0.95;">Tracking: {html.escape(str(row['Tracking']))}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

      
        mcols = st.columns(4)
        metrics_info = [
            ("Current Location", "Pacific Ocean"),
            ("Days in Transit", "12"),
            ("Distance Covered", "8,450 km"),
            ("Autonomous Actions", "3")
        ]
        for mc, (mtitle, mval) in zip(mcols, metrics_info):
            mc.markdown(
                f"""
                <div class="metric-box" style="background: linear-gradient(135deg,#10B981,#06B6D4);">
                    <div class="metric-title">{html.escape(mtitle)}</div>
                    <div class="metric-value">{html.escape(mval)}</div>
                    <div class="metric-sub">&nbsp;</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<br/>", unsafe_allow_html=True)

       
        timeline_df = pd.DataFrame({
            "Event": ["Order Placed", "Departure", "Port Entry", "Customs Clearance", "Current", "Estimated Arrival"],
            "Date": ["2024-01-01", "2024-01-05", "2024-01-10", "2024-01-11", "2024-01-13", str(row["ETA"])],
            "Status": ["Completed", "Completed", "Completed", "In Progress", "Current", "Pending"],
            "Location": ["Shanghai", "Shanghai Port", "Singapore Port", "Singapore Port", "Indian Ocean", row["Destination"]]
        })

        fig = go.Figure()
        color_map = {"Completed": "#10B981", "In Progress": "#F59E0B", "Current": "#EF4444", "Pending": "#6D6875"}
        for i, r in timeline_df.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[r["Date"]],
                    y=[i],
                    mode="markers+text",
                    marker=dict(size=18, color=color_map.get(r["Status"], "#6D6875")),
                    text=[r["Event"]],
                    textposition="bottom center",
                    hovertext=f"{r['Event']}<br>{r['Location']}<br>Status: {r['Status']}",
                    hoverinfo="text"
                )
            )
        fig.update_layout(
            yaxis=dict(showticklabels=False),
            height=360,
            margin=dict(t=30, b=10, l=10, r=10),
            xaxis=dict(title="Date")
        )
        st.plotly_chart(fig, use_container_width=True)

        # Recent events table (styled)
        events_df = pd.DataFrame({
            "Timestamp": ["2024-01-13 10:30", "2024-01-12 14:15", "2024-01-11 09:45", "2024-01-10 16:20"],
            "Event": ["Location update: Indian Ocean", "Customs clearance initiated", "Arrived at Singapore Port", "Departed Shanghai Port"],
            "Type": ["Location", "Customs", "Arrival", "Departure"]
        })
        st.markdown("<h4 style='margin-top:10px;'>📋 Recent Events</h4>", unsafe_allow_html=True)
        st.markdown(styled_table_html(events_df.reset_index(drop=True), table_id="events-table"), unsafe_allow_html=True)

        # Risk details (if any)
        if row["Risk"] in ["High", "Critical"]:
            st.markdown("<h4 style='margin-top:6px;'>⚠️ Risk Summary</h4>", unsafe_allow_html=True)
            risk_details = pd.DataFrame({
                "Risk Type": ["Port Congestion", "Customs Delay"],
                "Severity": ["High", "Medium"],
                "Detected": ["2024-01-10", "2024-01-11"],
                "Status": ["Mitigated", "Monitoring"],
                "Action": ["Rerouted", "Expedited Clearance"]
            })
            st.markdown(styled_table_html(risk_details, table_id="risk-table"), unsafe_allow_html=True)

        # Action buttons
        ab1, ab2, ab3 = st.columns(3)
        with ab1:
            if st.button("🔄 Trigger Risk Check", use_container_width=True):
                st.info(f"Risk check triggered for {row['ID']}")
        with ab2:
            if st.button("📍 Update Location", use_container_width=True):
                st.info(f"Location update invoked for {row['ID']}")
        with ab3:
            if st.button("📋 View Full History", use_container_width=True):
                st.info(f"Opening full history for {row['ID']} (demo)")

# Footer small caption
st.markdown("<hr/>", unsafe_allow_html=True)
st.caption(f"Autonomous Control Tower — demo • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")