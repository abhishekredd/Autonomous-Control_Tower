import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def show_dashboard():
    """Dashboard page for multi-page app"""
    
    # Get API functions from main app
    from app import fetch_dashboard_metrics, fetch_shipments, fetch_risks
    
    st.title("📊 Control Tower Dashboard")
    
    # Fetch real-time data
    metrics = fetch_dashboard_metrics()
    shipments = fetch_shipments(limit=20)
    risks = fetch_risks()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Shipments", 
                 metrics.get("active_shipments", 0) if metrics else 0)
    with col2:
        st.metric("High Risk", 
                 metrics.get("high_risk", 0) if metrics else 0,
                 delta_color="inverse")
    with col3:
        st.metric("On-Time Rate", 
                 f"{metrics.get('on_time_rate', 0)}%" if metrics else "0%")
    with col4:
        st.metric("Total Value", 
                 f"${metrics.get('total_value', 0):,}" if metrics else "$0")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌍 Shipment Locations")
        if shipments:
            # Prepare map data
            map_data = []
            for shipment in shipments:
                if shipment.get('current_latitude') and shipment.get('current_longitude'):
                    map_data.append({
                        'lat': shipment['current_latitude'],
                        'lon': shipment['current_longitude'],
                        'shipment': shipment.get('shipment_id', 'Unknown'),
                        'status': shipment.get('status', 'Unknown')
                    })
            
            if map_data:
                df = pd.DataFrame(map_data)
                fig = px.scatter_geo(df,
                                    lat='lat',
                                    lon='lon',
                                    hover_name='shipment',
                                    color='status',
                                    projection='natural earth')
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Risk Distribution")
        if risks:
            df_risks = pd.DataFrame(risks)
            risk_counts = df_risks['severity'].value_counts()
            
            fig = px.pie(values=risk_counts.values,
                        names=risk_counts.index,
                        title="Risk Severity Distribution")
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent shipments table
    st.subheader("📋 Recent Shipments")
    if shipments:
        df = pd.DataFrame(shipments)
        st.dataframe(
            df[['shipment_id', 'origin', 'destination', 'status', 'risk_score']].head(10),
            use_container_width=True,
            hide_index=True
        )

if __name__ == "__main__":
    show_dashboard()