import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import json

def main():
    st.set_page_config(
        page_title="Control Tower Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Control Tower Dashboard")
    
    # Sidebar filters
    with st.sidebar:
        st.header("Filters")
        
        # Date range
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=7), datetime.now()),
            max_value=datetime.now()
        )
        
        # Status filter
        status_options = ["All", "In Transit", "Delayed", "At Risk", "Completed"]
        selected_status = st.multiselect(
            "Status",
            options=status_options,
            default=["In Transit", "Delayed", "At Risk"]
        )
        
        # Risk level filter
        risk_levels = st.multiselect(
            "Risk Level",
            options=["All", "Low", "Medium", "High", "Critical"],
            default=["High", "Critical"]
        )
        
        st.divider()
        
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Active Shipments",
            "142",
            delta="+12",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "At Risk",
            "24",
            delta="+3",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "Delayed",
            "18",
            delta="-2",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "On Time %",
            "87%",
            delta="+2%",
            delta_color="normal"
        )
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Shipments by Status")
        
        # Status distribution data
        status_data = pd.DataFrame({
            "Status": ["In Transit", "Delayed", "At Risk", "Completed", "Pending"],
            "Count": [89, 18, 24, 45, 12]
        })
        
        fig = px.pie(
            status_data,
            values="Count",
            names="Status",
            color="Status",
            color_discrete_map={
                "In Transit": "#2E86AB",
                "Delayed": "#E76F51",
                "At Risk": "#F4A261",
                "Completed": "#588157",
                "Pending": "#6D6875"
            }
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("⚠️ Risks by Type")
        
        # Risk type distribution
        risk_data = pd.DataFrame({
            "Type": ["Port Congestion", "Customs Delay", "Quality Hold", 
                    "Weather Impact", "Equipment Failure", "Other"],
            "Count": [8, 6, 4, 3, 2, 1],
            "Severity": ["High", "High", "Medium", "Medium", "Low", "Low"]
        })
        
        fig = px.bar(
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
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("🔄 Recent Activity")
    
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
    
    st.dataframe(
        activity_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Time": st.column_config.TextColumn("Time", width="small"),
            "Shipment": st.column_config.TextColumn("Shipment", width="small"),
            "Activity": st.column_config.TextColumn("Activity"),
            "Agent": st.column_config.TextColumn("Agent", width="medium")
        }
    )
    
    # Map visualization
    st.subheader("🌍 Live Shipment Locations")
    
    # Sample shipment locations
    map_data = pd.DataFrame({
        "lat": [31.2304, 51.9244, 1.3521, 34.0522, 53.5511, 35.6762, 22.3193],
        "lon": [121.4737, 4.4777, 103.8198, -118.2437, 9.9937, 139.6503, 114.1694],
        "shipment": ["SH-001", "SH-002", "SH-003", "SH-004", "SH-005", "SH-006", "SH-007"],
        "status": ["In Transit", "Delayed", "In Transit", "In Transit", "At Risk", "In Transit", "Delayed"],
        "size": [20, 25, 15, 20, 30, 18, 22]
    })
    
    # Create map
    fig = px.scatter_mapbox(
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
        height=500
    )
    
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics
    st.subheader("📊 Performance Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Avg Transit Time", "8.2 days", "-0.3 days")
        st.progress(0.82, text="On-time Performance: 82%")
    
    with col2:
        st.metric("Risk Detection Rate", "94%", "+3%")
        st.progress(0.94, text="Detection Accuracy: 94%")
    
    with col3:
        st.metric("Cost Savings", "$124K", "+$18K")
        st.progress(0.76, text="Cost Efficiency: 76%")
    
    # Footer
    st.divider()
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("Dashboard updates every 30 seconds")

if __name__ == "__main__":
    main()