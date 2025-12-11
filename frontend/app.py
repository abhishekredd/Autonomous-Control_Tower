import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import time
from typing import Optional

# Page config
st.set_page_config(
    page_title="Autonomous Control Tower",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://api:8000"  # Change to localhost:8000 if running standalone
WEBSOCKET_URL = "ws://api:8000/ws"  # For real-time updates

# Session state initialization
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"
if 'websocket_connection' not in st.session_state:
    st.session_state.websocket_connection = None

# ========== API Functions ==========

def get_auth_headers() -> dict:
    """Get authentication headers for API requests"""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

def api_request(method: str, endpoint: str, data: Optional[dict] = None, params: Optional[dict] = None):
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        headers = get_auth_headers()
        
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return None
        
        if response.status_code == 401:
            st.error("Session expired. Please login again.")
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
        
        return response
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to API server. Please ensure backend is running.")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timeout. Please try again.")
        return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# ========== Data Fetching Functions ==========

@st.cache_data(ttl=30)
def fetch_dashboard_metrics():
    """Fetch dashboard metrics from API"""
    response = api_request("GET", "/api/v1/dashboard/metrics")
    if response and response.status_code == 200:
        return response.json()
    return None

@st.cache_data(ttl=60)
def fetch_shipments(skip: int = 0, limit: int = 100, status: Optional[str] = None):
    """Fetch shipments from API"""
    params = {"skip": skip, "limit": limit}
    if status:
        params["status"] = status
    
    response = api_request("GET", "/api/v1/shipments", params=params)
    if response and response.status_code == 200:
        return response.json()
    return []

@st.cache_data(ttl=60)
def fetch_risks(severity: Optional[str] = None):
    """Fetch risks from API"""
    params = {}
    if severity:
        params["severity"] = severity
    
    response = api_request("GET", "/api/v1/risks", params=params)
    if response and response.status_code == 200:
        return response.json()
    return []

@st.cache_data(ttl=120)
def fetch_shipment_details(shipment_id: int):
    """Fetch detailed shipment information"""
    response = api_request("GET", f"/api/v1/shipments/{shipment_id}")
    if response and response.status_code == 200:
        return response.json()
    return None

def create_shipment(shipment_data: dict):
    """Create new shipment via API"""
    response = api_request("POST", "/api/v1/shipments", data=shipment_data)
    if response and response.status_code == 200:
        return response.json()
    return None

def run_simulation(simulation_data: dict):
    """Run simulation via API"""
    response = api_request("POST", "/api/v1/simulations", data=simulation_data)
    if response and response.status_code == 200:
        return response.json()
    return None

# ========== Authentication Functions ==========

def login(username: str, password: str) -> bool:
    """Login to API and get token"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/token",
            data={"username": username, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            st.session_state.token = token_data["access_token"]
            st.session_state.user = {"username": username}
            return True
        else:
            st.error("Invalid credentials")
            return False
    except:
        # Fallback for development (without backend)
        if username == "admin" and password == "secret":
            st.session_state.token = "dev_token"
            st.session_state.user = {"username": username}
            st.info("⚠️ Using development mode (backend not connected)")
            return True
        st.error("Cannot connect to authentication server")
        return False

def logout():
    """Clear session and logout"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ========== Sidebar Navigation ==========

def render_sidebar():
    """Render sidebar navigation"""
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/container-ship.png", width=100)
        st.title("Control Tower")
        
        # User info
        if st.session_state.user:
            st.success(f"✅ {st.session_state.user.get('username', 'User')}")
            if st.button("🚪 Logout", use_container_width=True):
                logout()
        
        st.divider()
        
        # Navigation menu
        menu_items = {
            "📊 Dashboard": "Dashboard",
            "📦 Shipments": "Shipments",
            "⚠️ Risks": "Risks",
            "🔮 Simulations": "Simulations",
            "🤖 MCP Agents": "MCP Agents",
            "📈 Analytics": "Analytics",
            "⚙️ Settings": "Settings"
        }
        
        for icon_text, page_name in menu_items.items():
            if st.button(icon_text, 
                        use_container_width=True,
                        type="primary" if st.session_state.current_page == page_name else "secondary"):
                st.session_state.current_page = page_name
                st.rerun()
        
        st.divider()
        
        # System status
        st.subheader("System Status")
        col1, col2 = st.columns(2)
        with col1:
            status_color = "🟢" if st.session_state.token else "🔴"
            st.write(f"API: {status_color}")
        with col2:
            st.write("DB: 🟢")
        
        st.divider()
        
        # Quick actions
        st.subheader("Quick Actions")
        if st.button("🔄 Refresh All", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("Report generation started...")
        
        st.divider()
        st.caption(f"v1.0.0 | {datetime.now().strftime('%H:%M:%S')}")

# ========== Page Components ==========

def dashboard_page():
    """Dashboard page with real-time metrics"""
    st.title("📊 Control Tower Dashboard")
    
    # Fetch metrics
    metrics = fetch_dashboard_metrics()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Active Shipments",
            metrics.get("active_shipments", 0) if metrics else 0,
            delta="+12" if metrics else None
        )
    with col2:
        st.metric(
            "High Risk",
            metrics.get("high_risk", 0) if metrics else 0,
            delta="+3" if metrics else None,
            delta_color="inverse"
        )
    with col3:
        st.metric(
            "On-Time Rate",
            f"{metrics.get('on_time_rate', 0)}%" if metrics else "0%",
            delta="+2%" if metrics else None
        )
    with col4:
        st.metric(
            "Total Value",
            f"${metrics.get('total_value', 0):,}" if metrics else "$0",
            delta="+$250K" if metrics else None
        )
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌍 Shipment Locations")
        shipments = fetch_shipments(limit=20)
        
        if shipments:
            # Prepare map data
            map_data = []
            for shipment in shipments:
                if shipment.get('current_latitude') and shipment.get('current_longitude'):
                    map_data.append({
                        'lat': shipment['current_latitude'],
                        'lon': shipment['current_longitude'],
                        'shipment': shipment.get('shipment_id', 'Unknown'),
                        'status': shipment.get('status', 'Unknown'),
                        'risk': shipment.get('risk_score', 0)
                    })
            
            if map_data:
                df = pd.DataFrame(map_data)
                fig = px.scatter_mapbox(
                    df,
                    lat='lat',
                    lon='lon',
                    hover_name='shipment',
                    hover_data=['status', 'risk'],
                    color='status',
                    size_max=15,
                    zoom=1,
                    height=400
                )
                fig.update_layout(mapbox_style="carto-positron")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No location data available")
        else:
            st.info("No shipments found")
    
    with col2:
        st.subheader("📊 Risk Distribution")
        risks = fetch_risks()
        
        if risks:
            df_risks = pd.DataFrame(risks)
            risk_counts = df_risks['severity'].value_counts()
            
            fig = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                color=risk_counts.index,
                color_discrete_map={
                    'HIGH': '#DC2626',
                    'MEDIUM': '#F59E0B',
                    'LOW': '#10B981'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No risks detected")
    
    # Recent activities
    st.subheader("🔄 Recent Activities")
    
    # Fetch recent shipments
    recent_shipments = fetch_shipments(limit=10)
    if recent_shipments:
        activities = []
        for shipment in recent_shipments:
            activities.append({
                'Shipment': shipment.get('shipment_id'),
                'Status': shipment.get('status'),
                'Risk Score': f"{shipment.get('risk_score', 0):.1f}",
                'Last Updated': shipment.get('updated_at', 'N/A')
            })
        
        df_activities = pd.DataFrame(activities)
        st.dataframe(df_activities, use_container_width=True, hide_index=True)
    else:
        st.info("No recent activities")

def shipments_page():
    """Shipments management page"""
    st.title("📦 Shipment Management")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["All Shipments", "Create Shipment", "Track Shipment"])
    
    with tab1:
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("Search shipments")
        with col2:
            status_filter = st.selectbox(
                "Filter by status",
                ["ALL", "IN_TRANSIT", "DELAYED", "DELIVERED", "CANCELLED", "PENDING"]
            )
        
        # Fetch shipments
        shipments = fetch_shipments()
        
        if shipments:
            df = pd.DataFrame(shipments)
            
            # Apply filters
            if search_term:
                df = df[df['shipment_id'].str.contains(search_term, case=False) |
                       df['origin'].str.contains(search_term, case=False) |
                       df['destination'].str.contains(search_term, case=False)]
            
            if status_filter != "ALL":
                df = df[df['status'] == status_filter]
            
            # Display shipments
            st.dataframe(
                df[['shipment_id', 'origin', 'destination', 'status', 'risk_score', 'estimated_value']],
                use_container_width=True,
                hide_index=True
            )
            
            # Shipment details
            if not df.empty:
                selected_id = st.selectbox(
                    "Select shipment for details",
                    df['shipment_id'].tolist()
                )
                
                if selected_id:
                    shipment_details = fetch_shipment_details(
                        next(s['id'] for s in shipments if s['shipment_id'] == selected_id)
                    )
                    
                    if shipment_details:
                        with st.expander(f"Details for {selected_id}", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Status", shipment_details.get('status', 'N/A'))
                                st.metric("Origin", shipment_details.get('origin', 'N/A'))
                                st.metric("Destination", shipment_details.get('destination', 'N/A'))
                                st.metric("Carrier", shipment_details.get('carrier', 'N/A'))
                            with col2:
                                st.metric("Risk Score", f"{shipment_details.get('risk_score', 0):.1f}/10")
                                st.metric("Value", f"${shipment_details.get('estimated_value', 0):,}")
                                st.metric("Mode", shipment_details.get('transport_mode', 'N/A'))
                                st.metric("Last Updated", shipment_details.get('updated_at', 'N/A').split('T')[0])
        else:
            st.info("No shipments found")
    
    with tab2:
        st.subheader("Create New Shipment")
        
        with st.form("create_shipment_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                shipment_id = st.text_input("Shipment ID*", 
                                          value=f"SH{datetime.now().strftime('%Y%m%d%H%M')}")
                origin = st.text_input("Origin*", "Shanghai, China")
                destination = st.text_input("Destination*", "Rotterdam, Netherlands")
                carrier = st.selectbox("Carrier*", 
                                     ["MAERSK", "CMA CGM", "MSC", "COSCO", "HAPAG-LLOYD"])
            
            with col2:
                transport_mode = st.selectbox("Transport Mode*", ["SEA", "AIR", "RAIL", "ROAD"])
                estimated_value = st.number_input("Estimated Value (USD)*", 
                                                 min_value=1000, value=50000, step=1000)
                scheduled_departure = st.date_input("Scheduled Departure*")
                scheduled_arrival = st.date_input("Scheduled Arrival*")
            
            submitted = st.form_submit_button("Create Shipment", type="primary")
            
            if submitted:
                if not all([shipment_id, origin, destination]):
                    st.error("Please fill in all required fields (*)")
                else:
                    shipment_data = {
                        "tracking_number": shipment_id,
                        "reference_number": f"REF-{shipment_id}",
                        "origin": origin,
                        "destination": destination,
                        "mode": transport_mode,
                        "weight": 1000,  # or add a form field
                        "volume": 10,    # or add a form field
                        "value": float(estimated_value),
                        "estimated_departure": scheduled_departure.isoformat(),
                        "estimated_arrival": scheduled_arrival.isoformat(),
                        "shipper": "Acme Corporation",  # or add a form field
                        "carrier": carrier,
                        "consignee": "Global Imports BV"  # or add a form field
                    }
                    
                    result = create_shipment(shipment_data)
                    if result:
                        st.success(f"Shipment {shipment_id} created successfully!")
                        st.balloons()
                    else:
                        st.error("Failed to create shipment")
    
    with tab3:
        st.subheader("Track Shipment")
        
        shipment_id = st.text_input("Enter Shipment ID")
        
        if shipment_id:
            # In a real implementation, you would fetch real-time tracking data
            st.info("Real-time tracking would be implemented with WebSocket connection")
            
            # Simulated tracking data
            tracking_data = {
                "current_location": "Pacific Ocean",
                "coordinates": "35.6895° N, 139.6917° E",
                "status": "IN_TRANSIT",
                "progress": 65,
                "next_port": "Los Angeles",
                "eta": "2024-01-20",
                "distance_covered": "8,450 km",
                "distance_remaining": "4,550 km"
            }
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current Location", tracking_data["current_location"])
                st.metric("Status", tracking_data["status"])
                st.metric("Progress", f"{tracking_data['progress']}%")
                st.progress(tracking_data["progress"] / 100)
            
            with col2:
                st.metric("Next Port", tracking_data["next_port"])
                st.metric("ETA", tracking_data["eta"])
                st.metric("Distance Covered", tracking_data["distance_covered"])
                st.metric("Distance Remaining", tracking_data["distance_remaining"])

def risks_page():
    """Risk management page"""
    st.title("⚠️ Risk Management")
    
    # Fetch risks
    risks = fetch_risks()
    
    if risks:
        # Risk metrics
        col1, col2, col3 = st.columns(3)
        
        high_risks = len([r for r in risks if r.get('severity') == 'HIGH'])
        medium_risks = len([r for r in risks if r.get('severity') == 'MEDIUM'])
        active_risks = len([r for r in risks if r.get('status') == 'ACTIVE'])
        
        with col1:
            st.metric("Active Risks", active_risks)
        with col2:
            st.metric("High Severity", high_risks, delta_color="inverse")
        with col3:
            st.metric("Medium Severity", medium_risks)
        
        # Risks table
        st.subheader("Active Risks")
        
        df_risks = pd.DataFrame(risks)
        st.dataframe(
            df_risks[['id', 'shipment_id', 'risk_type', 'severity', 'probability', 'impact_score', 'status']],
            use_container_width=True,
            hide_index=True
        )
        
        # Risk details
        if not df_risks.empty:
            selected_risk = st.selectbox(
                "Select risk for details",
                df_risks['id'].tolist(),
                format_func=lambda x: f"Risk {x}"
            )
            
            risk_details = next((r for r in risks if r['id'] == selected_risk), None)
            
            if risk_details:
                with st.expander(f"Risk Details - ID: {selected_risk}", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Risk Type:** {risk_details.get('risk_type', 'N/A')}")
                        st.write(f"**Severity:** {risk_details.get('severity', 'N/A')}")
                        st.write(f"**Probability:** {risk_details.get('probability', 0):.2f}")
                        st.write(f"**Impact Score:** {risk_details.get('impact_score', 0)}")
                    
                    with col2:
                        st.write(f"**Status:** {risk_details.get('status', 'N/A')}")
                        st.write(f"**Detected:** {risk_details.get('detected_at', 'N/A')}")
                        st.write(f"**Description:** {risk_details.get('description', 'N/A')}")
                    
                    # Mitigation actions
                    st.subheader("Mitigation Actions")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🔄 Reroute", use_container_width=True):
                            st.info("Reroute action triggered")
                    with col2:
                        if st.button("⚡ Expedite", use_container_width=True):
                            st.info("Expedite action triggered")
                    with col3:
                        if st.button("📧 Notify", use_container_width=True):
                            st.info("Notification sent to stakeholders")
    else:
        st.info("No risks detected")

def simulations_page():
    """Simulations page"""
    st.title("🔮 Mitigation Simulations")
    
    # Simulation controls
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk Simulation")
        
        with st.form("risk_simulation_form"):
            risk_type = st.selectbox(
                "Risk Scenario",
                ["PORT_CONGESTION", "CUSTOMS_DELAY", "WEATHER", "LABOR_STRIKE", "EQUIPMENT_FAILURE"]
            )
            severity = st.slider("Severity Level", 1, 10, 5)
            duration_hours = st.number_input("Duration (hours)", min_value=1, max_value=720, value=24)
            
            submitted = st.form_submit_button("Run Simulation", type="primary")
            
            if submitted:
                simulation_data = {
                    "simulation_type": "RISK_IMPACT",
                    "parameters": {
                        "risk_type": risk_type,
                        "severity": severity,
                        "duration_hours": duration_hours
                    }
                }
                
                result = run_simulation(simulation_data)
                if result:
                    st.success("Simulation started!")
                    st.json(result)
                else:
                    st.error("Failed to run simulation")
    
    with col2:
        st.subheader("Mitigation Options")
        
        with st.form("mitigation_simulation_form"):
            action_type = st.selectbox(
                "Action Type",
                ["RE_ROUTE", "MODE_SWITCH", "EXPEDITE", "HOLD", "INSURANCE_CLAIM"]
            )
            cost_limit = st.number_input("Cost Limit (USD)", min_value=0, value=10000)
            time_constraint = st.number_input("Time Constraint (hours)", min_value=0, value=48)
            
            submitted = st.form_submit_button("Simulate Action", type="primary")
            
            if submitted:
                simulation_data = {
                    "simulation_type": "MITIGATION",
                    "parameters": {
                        "action_type": action_type,
                        "cost_limit": cost_limit,
                        "time_constraint": time_constraint
                    }
                }
                
                result = run_simulation(simulation_data)
                if result:
                    st.success("Action simulation started!")
                    st.json(result)
                else:
                    st.error("Failed to run simulation")
    
    # Simulation results
    st.subheader("Recent Simulations")
    
    # Mock simulation results
    simulations = [
        {
            "id": 1,
            "type": "RISK_IMPACT",
            "status": "COMPLETED",
            "result": "High impact detected",
            "created_at": "2024-01-10 10:30:00"
        },
        {
            "id": 2,
            "type": "MITIGATION",
            "status": "COMPLETED",
            "result": "Optimal route found",
            "created_at": "2024-01-10 09:15:00"
        },
        {
            "id": 3,
            "type": "RISK_IMPACT",
            "status": "RUNNING",
            "result": "In progress",
            "created_at": "2024-01-10 11:45:00"
        }
    ]
    
    df_simulations = pd.DataFrame(simulations)
    st.dataframe(df_simulations, use_container_width=True, hide_index=True)

def mcp_agents_page():
    """MCP Agents monitoring page"""
    st.title("🤖 MCP Agent Network")
    
    # Agent status
    agents = [
        {
            "name": "Central Orchestrator",
            "status": "ACTIVE",
            "cpu": "15%",
            "memory": "512MB",
            "messages": "1,425",
            "uptime": "7d 12h"
        },
        {
            "name": "Risk Detector",
            "status": "ACTIVE",
            "cpu": "8%",
            "memory": "256MB",
            "messages": "892",
            "uptime": "7d 12h"
        },
        {
            "name": "Route Optimizer",
            "status": "ACTIVE",
            "cpu": "12%",
            "memory": "384MB",
            "messages": "764",
            "uptime": "7d 12h"
        },
        {
            "name": "Stakeholder Comms",
            "status": "ACTIVE",
            "cpu": "6%",
            "memory": "192MB",
            "messages": "543",
            "uptime": "7d 12h"
        },
        {
            "name": "Simulation Engine",
            "status": "ACTIVE",
            "cpu": "22%",
            "memory": "768MB",
            "messages": "672",
            "uptime": "7d 12h"
        },
        {
            "name": "Action Executor",
            "status": "ACTIVE",
            "cpu": "9%",
            "memory": "320MB",
            "messages": "456",
            "uptime": "7d 12h"
        }
    ]
    
    df_agents = pd.DataFrame(agents)
    st.dataframe(df_agents, use_container_width=True, hide_index=True)
    
    # Agent communication flow
    st.subheader("📡 Agent Communication Flow")
    
    messages = [
        {
            "time": "10:30:01",
            "from": "Risk Detector",
            "to": "Orchestrator",
            "message": "Risk detected: Port congestion",
            "context": "SH-001"
        },
        {
            "time": "10:30:03",
            "from": "Orchestrator",
            "to": "Simulation Engine",
            "message": "Simulate mitigation options",
            "context": "SH-001"
        },
        {
            "time": "10:30:05",
            "from": "Simulation Engine",
            "to": "Orchestrator",
            "message": "3 options simulated, best: reroute",
            "context": "SH-001"
        },
        {
            "time": "10:30:07",
            "from": "Orchestrator",
            "to": "Action Executor",
            "message": "Execute reroute action",
            "context": "SH-001"
        },
        {
            "time": "10:30:10",
            "from": "Action Executor",
            "to": "Orchestrator",
            "message": "Action completed successfully",
            "context": "SH-001"
        }
    ]
    
    df_messages = pd.DataFrame(messages)
    st.dataframe(df_messages, use_container_width=True, hide_index=True)

def analytics_page():
    """Analytics page"""
    st.title("📈 Analytics & Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Performance Metrics")
        
        # Fetch metrics from API
        metrics = fetch_dashboard_metrics()
        
        if metrics:
            st.metric("On-Time Delivery", f"{metrics.get('on_time_rate', 0)}%")
            st.metric("Cost Efficiency", f"{metrics.get('cost_efficiency', 0)}%")
            st.metric("Risk Mitigation", f"{metrics.get('risk_mitigation', 0)}%")
            st.metric("Customer Satisfaction", f"{metrics.get('customer_satisfaction', 0)}%")
        else:
            # Fallback metrics
            st.metric("On-Time Delivery", "87%", "+2%")
            st.metric("Cost Efficiency", "92%", "+3%")
            st.metric("Risk Mitigation", "78%", "+5%")
            st.metric("Customer Satisfaction", "88%", "+1%")
    
    with col2:
        st.subheader("Trend Analysis")
        
        # Generate sample trend data
        import numpy as np
        np.random.seed(42)
        
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        risk_scores = np.random.randint(30, 70, 6)
        delivery_times = np.random.randint(5, 20, 6)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=months, 
            y=risk_scores, 
            name='Risk Score',
            line=dict(color='red')
        ))
        fig.add_trace(go.Scatter(
            x=months, 
            y=delivery_times, 
            name='Avg Delivery (days)',
            line=dict(color='blue'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Risk vs Delivery Time Trends',
            yaxis=dict(title='Risk Score'),
            yaxis2=dict(title='Delivery Days', overlaying='y', side='right')
        )
        
        st.plotly_chart(fig, use_container_width=True)

def settings_page():
    """Settings page"""
    st.title("⚙️ System Settings")
    
    tab1, tab2, tab3 = st.tabs(["API Configuration", "Notifications", "User Management"])
    
    with tab1:
        st.subheader("API Configuration")
        
        with st.form("api_config_form"):
            api_url = st.text_input("API Base URL", value=API_BASE_URL)
            api_timeout = st.number_input("API Timeout (seconds)", min_value=5, max_value=60, value=10)
            
            if st.form_submit_button("Save Configuration", type="primary"):
                st.success("Configuration saved!")
    
    with tab2:
        st.subheader("Notification Settings")
        
        email_notifications = st.checkbox("Email notifications", value=True)
        sms_alerts = st.checkbox("SMS alerts", value=False)
        webhook_integrations = st.checkbox("Webhook integrations", value=False)
        
        alert_threshold = st.select_slider(
            "Alert Threshold",
            options=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            value="MEDIUM"
        )
        
        if st.button("Update Notifications", type="primary"):
            st.success("Notification settings updated!")
    
    with tab3:
        st.subheader("User Management")
        
        if st.session_state.user:
            st.write(f"**Current User:** {st.session_state.user.get('username', 'N/A')}")
            st.write(f"**Role:** Administrator")
        
        with st.expander("Change Password"):
            current_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm Password", type="password")
            
            if st.button("Update Password", type="primary"):
                if new_pw == confirm_pw:
                    st.success("Password updated successfully!")
                else:
                    st.error("Passwords do not match")

# ========== Login Page ==========

def login_page():
    """Render login page"""
    st.title("🚢 Autonomous Control Tower")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://img.icons8.com/color/96/000000/container-ship.png", width=150)
    
    with col2:
        st.subheader("Sign in to your account")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            submit = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submit:
                if login(username, password):
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
        
        st.markdown("---")
        st.caption("Default credentials: admin / secret")
        
        # Development mode toggle
        if st.checkbox("Enable development mode (no backend required)"):
            st.info("Development mode enabled. Using mock data.")

# ========== Main App Logic ==========

def main():
    """Main application logic"""
    
    # Check authentication
    if not st.session_state.token:
        login_page()
        return
    
    # Render sidebar
    render_sidebar()
    
    # Render current page
    if st.session_state.current_page == "Dashboard":
        dashboard_page()
    elif st.session_state.current_page == "Shipments":
        shipments_page()
    elif st.session_state.current_page == "Risks":
        risks_page()
    elif st.session_state.current_page == "Simulations":
        simulations_page()
    elif st.session_state.current_page == "MCP Agents":
        mcp_agents_page()
    elif st.session_state.current_page == "Analytics":
        analytics_page()
    elif st.session_state.current_page == "Settings":
        settings_page()
    
    # Footer
    st.divider()
    st.caption(f"Autonomous Control Tower v1.0 | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()