import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import asyncio
import websockets
import json

# Page config
st.set_page_config(
    page_title="Autonomous Control Tower",
    page_icon="🚢",
    layout="wide"
)

# Sidebar
with st.sidebar:
    st.title("🚢 Control Tower")
    
    view = st.selectbox(
        "Navigation",
        ["Dashboard", "Shipments", "Risks", "Simulations", "Digital Twin"]
    )
    
    st.divider()
    
    st.subheader("Real-time Controls")
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    refresh_rate = st.slider("Refresh rate (seconds)", 5, 60, 30)
    
    if st.button("🔄 Manual Refresh"):
        st.rerun()
    
    st.divider()
    
    st.subheader("System Status")
    st.progress(0.85, text="Operational: 85%")
    st.caption("Last updated: " + datetime.now().strftime("%H:%M:%S"))

# Main content based on selected view
if view == "Dashboard":
    st.title("🏢 Autonomous Control Tower Dashboard")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Shipments", "142", "+12")
    with col2:
        st.metric("At Risk", "24", "+3", delta_color="inverse")
    with col3:
        st.metric("Autonomous Actions", "8", "Today")
    with col4:
        st.metric("Cost Savings", "$124K", "+$18K")
    
    # Map visualization
    st.subheader("🌍 Global Shipment Tracking")
    
    # Sample shipment data
    shipments = pd.DataFrame({
        'Shipment': ['SH-001', 'SH-002', 'SH-003', 'SH-004'],
        'Origin': ['Shanghai', 'Rotterdam', 'Singapore', 'Los Angeles'],
        'Destination': ['Rotterdam', 'New York', 'Dubai', 'Tokyo'],
        'Status': ['In Transit', 'Delayed', 'On Time', 'In Transit'],
        'Risk': ['High', 'Critical', 'Low', 'Medium'],
        'Lat': [31.2304, 51.9244, 1.3521, 34.0522],
        'Lon': [121.4737, 4.4777, 103.8198, -118.2437]
    })
    
    fig = px.scatter_geo(shipments,
                        lat='Lat',
                        lon='Lon',
                        color='Risk',
                        hover_name='Shipment',
                        hover_data=['Origin', 'Destination', 'Status'],
                        size=[20, 25, 15, 20],
                        projection='natural earth',
                        color_discrete_map={
                            'High': 'red',
                            'Critical': 'darkred',
                            'Medium': 'orange',
                            'Low': 'green'
                        })
    
    fig.update_layout(height=500, title="Live Shipment Locations")
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent activities
    st.subheader("📋 Recent Activities")
    
    activities = pd.DataFrame({
        'Time': ['10:30', '10:25', '10:20', '10:15', '10:10'],
        'Shipment': ['SH-001', 'SH-045', 'SH-089', 'SH-112', 'SH-156'],
        'Activity': ['Rerouted via alternative port', 
                    'Customs clearance expedited',
                    'Risk detected: Port congestion',
                    'Mode switched to air freight',
                    'Stakeholders notified of delay'],
        'Agent': ['Route Optimizer', 'Action Executor', 'Risk Detector', 
                 'Action Executor', 'Stakeholder Comms']
    })
    
    st.dataframe(activities, use_container_width=True, hide_index=True)
    
elif view == "Shipments":
    st.title("📦 Shipment Management")
    
    # Shipment list
    st.subheader("Active Shipments")
    
    # Fetch from API (simulated)
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
    
    st.dataframe(shipments_data, use_container_width=True, hide_index=True)
    
    # Shipment details
    st.subheader("Shipment Details")
    selected_shipment = st.selectbox("Select Shipment", shipments_data['ID'].tolist())
    
    if selected_shipment:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Location", "Pacific Ocean", "34.0522° N, 118.2437° W")
            st.metric("Days in Transit", "12", "+1")
            st.metric("Distance Covered", "8,450 km", "68%")
        
        with col2:
            st.metric("Risk Score", "0.82", "High")
            st.metric("Estimated Delay", "18 hours", "+6h")
            st.metric("Autonomous Actions", "3", "Today")
        
        # Timeline
        st.subheader("🚢 Shipment Timeline")
        
        timeline_data = pd.DataFrame({
            'Event': ['Departure', 'Port Entry', 'Customs Clearance', 'Current', 'Estimated Arrival'],
            'Date': ['2024-01-01', '2024-01-08', '2024-01-09', '2024-01-13', '2024-01-15'],
            'Status': ['Completed', 'Completed', 'In Progress', 'Current', 'Pending'],
            'Location': ['Shanghai', 'Singapore', 'Singapore', 'Pacific Ocean', 'Rotterdam']
        })
        
        fig_timeline = px.timeline(timeline_data, 
                                 x_start='Date',
                                 x_end='Date',
                                 y='Event',
                                 color='Status',
                                 hover_data=['Location'],
                                 color_discrete_map={
                                     'Completed': 'green',
                                     'In Progress': 'blue',
                                     'Current': 'orange',
                                     'Pending': 'gray'
                                 })
        
        fig_timeline.update_layout(height=300)
        st.plotly_chart(fig_timeline, use_container_width=True)

elif view == "Risks":
    st.title("⚠️ Risk Management")
    
    # Risk overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Active Risks", "24", "+3")
    with col2:
        st.metric("Critical Risks", "8", "+2", delta_color="inverse")
    with col3:
        st.metric("Mitigations Applied", "16", "67%")
    
    # Risk breakdown
    st.subheader("Risk Breakdown by Type")
    
    risk_types = pd.DataFrame({
        'Type': ['Port Congestion', 'Customs Delay', 'Quality Hold', 
                'Weather Impact', 'Equipment Failure', 'Other'],
        'Count': [8, 6, 4, 3, 2, 1],
        'Severity': ['High', 'High', 'Medium', 'Medium', 'Low', 'Low']
    })
    
    fig_risk = px.bar(risk_types, 
                     x='Type', 
                     y='Count',
                     color='Severity',
                     color_discrete_map={
                         'High': 'red',
                         'Medium': 'orange',
                         'Low': 'yellow'
                     })
    
    st.plotly_chart(fig_risk, use_container_width=True)
    
    # Recent risk alerts
    st.subheader("🚨 Recent Risk Alerts")
    
    alerts = pd.DataFrame({
        'Time': ['10:30', '10:25', '10:20', '10:15', '10:10'],
        'Shipment': ['SH-001', 'SH-045', 'SH-089', 'SH-112', 'SH-156'],
        'Risk Type': ['Port Congestion', 'Customs Delay', 'Weather Impact', 
                     'Quality Hold', 'Port Congestion'],
        'Severity': ['High', 'Critical', 'Medium', 'Medium', 'High'],
        'Action Taken': ['Rerouted', 'Expedited Clearance', 'Schedule Adjusted',
                        'Remote Inspection', 'Monitoring'],
        'Status': ['Resolved', 'In Progress', 'Resolved', 'In Progress', 'Detected']
    })
    
    st.dataframe(alerts, use_container_width=True, hide_index=True)

elif view == "Simulations":
    st.title("🔮 Mitigation Simulations")
    
    st.subheader("Digital Twin Simulations")
    
    # Simulation scenarios
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
    
    for scenario in scenarios:
        with st.expander(f"📊 {scenario['name']} - {scenario['shipment']}"):
            st.write(f"**Risk:** {scenario['risk']}")
            
            options_df = pd.DataFrame(scenario["options"])
            st.dataframe(options_df, use_container_width=True, hide_index=True)
            
            # Visualization
            fig = px.scatter(options_df,
                           x='cost',
                           y='time_savings',
                           size='risk',
                           color='name',
                           hover_name='name',
                           title="Cost vs Time Savings Analysis")
            
            st.plotly_chart(fig, use_container_width=True)
            
            if st.button(f"Run Simulation for {scenario['shipment']}", key=scenario['name']):
                st.success(f"Simulation running for {scenario['shipment']}...")
                # In production, this would trigger the simulation service

elif view == "Digital Twin":
    st.title("👥 Digital Twin & MCP Agents")
    
    st.subheader("🤖 MCP Agent Network")
    
    # Agent status
    agents = pd.DataFrame({
        'Agent': ['Central Orchestrator', 'Risk Detector', 'Route Optimizer', 
                 'Stakeholder Comms', 'Simulation Engine', 'Action Executor'],
        'Status': ['Active', 'Active', 'Active', 'Active', 'Active', 'Active'],
        'CPU %': ['15%', '8%', '12%', '6%', '22%', '9%'],
        'Memory': ['512MB', '256MB', '384MB', '192MB', '768MB', '320MB'],
        'Messages': ['1,425', '892', '764', '543', '672', '456'],
        'Uptime': ['7d 12h', '7d 12h', '7d 12h', '7d 12h', '7d 12h', '7d 12h']
    })
    
    st.dataframe(agents, use_container_width=True, hide_index=True)
    
    # Agent communication flow
    st.subheader("📡 MCP Message Flow")
    
    # Sample message flow
    messages = pd.DataFrame({
        'Time': ['10:30:01', '10:30:03', '10:30:05', '10:30:07', '10:30:10'],
        'From': ['Risk Detector', 'Orchestrator', 'Simulation Engine', 
                'Orchestrator', 'Action Executor'],
        'To': ['Orchestrator', 'Simulation Engine', 'Orchestrator', 
              'Action Executor', 'Orchestrator'],
        'Message': ['Risk detected: Port congestion', 
                   'Simulate mitigation options',
                   '3 options simulated, best: reroute',
                   'Execute reroute action',
                   'Action completed successfully'],
        'Context': ['SH-001', 'SH-001', 'SH-001', 'SH-001', 'SH-001']
    })
    
    st.dataframe(messages, use_container_width=True, hide_index=True)
    
    # Real-time visualization
    st.subheader("🔄 Real-time Agent Activity")
    
    # Create a network graph visualization
    nodes = pd.DataFrame({
        'Node': ['Orchestrator', 'Risk Detector', 'Route Optimizer', 
                'Stakeholder Comms', 'Simulation Engine', 'Action Executor'],
        'X': [0, -2, 0, 2, -2, 2],
        'Y': [0, 1, 2, 1, -1, -1],
        'Size': [30, 20, 20, 20, 25, 25],
        'Color': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
    })
    
    edges = pd.DataFrame({
        'From': ['Orchestrator', 'Orchestrator', 'Orchestrator', 
                'Risk Detector', 'Route Optimizer', 'Simulation Engine'],
        'To': ['Risk Detector', 'Route Optimizer', 'Stakeholder Comms',
              'Simulation Engine', 'Action Executor', 'Action Executor']
    })
    
    # Create network visualization
    fig = go.Figure()
    
    # Add edges
    for _, edge in edges.iterrows():
        from_node = nodes[nodes['Node'] == edge['From']].iloc[0]
        to_node = nodes[nodes['Node'] == edge['To']].iloc[0]
        
        fig.add_trace(go.Scatter(
            x=[from_node['X'], to_node['X']],
            y=[from_node['Y'], to_node['Y']],
            mode='lines',
            line=dict(width=2, color='#888'),
            hoverinfo='none'
        ))
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=nodes['X'],
        y=nodes['Y'],
        mode='markers+text',
        text=nodes['Node'],
        textposition="bottom center",
        marker=dict(
            size=nodes['Size'],
            color=nodes['Color'],
            line=dict(width=2, color='white')
        ),
        hovertext=nodes['Node'] + "<br>Status: Active",
        hoverinfo='text'
    ))
    
    fig.update_layout(
        title="MCP Agent Communication Network",
        showlegend=False,
        hovermode='closest',
        margin=dict(b=0,l=0,r=0,t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.divider()
st.caption("Autonomous Control Tower v1.0 | Real-time monitoring active | Last updated: " + 
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"))