import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests

def main():
    st.set_page_config(
        page_title="Shipment Management",
        page_icon="🚢",
        layout="wide"
    )
    
    st.title("🚢 Shipment Management")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["All Shipments", "Create Shipment", "Shipment Details"])
    
    with tab1:
        st.subheader("All Shipments")
        
        # Search and filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            search_query = st.text_input("Search", placeholder="Tracking number or reference")
        
        with col2:
            status_filter = st.selectbox(
                "Status",
                ["All", "In Transit", "Delayed", "At Risk", "Completed", "Pending"]
            )
        
        with col3:
            mode_filter = st.selectbox(
                "Mode",
                ["All", "Sea", "Air", "Land", "Rail", "Multimodal"]
            )
        
        with col4:
            risk_filter = st.selectbox(
                "Risk Level",
                ["All", "Low", "Medium", "High", "Critical"]
            )
        
        # Shipments table
        shipments_data = pd.DataFrame({
            'ID': ['SH-001', 'SH-002', 'SH-003', 'SH-004', 'SH-005', 'SH-006', 'SH-007', 'SH-008'],
            'Tracking': ['TRK789012', 'TRK789013', 'TRK789014', 'TRK789015', 'TRK789016', 'TRK789017', 'TRK789018', 'TRK789019'],
            'Origin': ['Shanghai', 'Rotterdam', 'Singapore', 'Los Angeles', 'Hamburg', 'Tokyo', 'Dubai', 'Mumbai'],
            'Destination': ['Rotterdam', 'New York', 'Dubai', 'Tokyo', 'Shanghai', 'Los Angeles', 'London', 'Singapore'],
            'Status': ['In Transit', 'Delayed', 'On Time', 'In Transit', 'At Risk', 'In Transit', 'Delayed', 'Pending'],
            'Mode': ['Sea', 'Sea', 'Air', 'Sea', 'Rail', 'Air', 'Sea', 'Multimodal'],
            'ETA': ['2024-01-15', '2024-01-18', '2024-01-12', '2024-01-20', '2024-01-22', '2024-01-14', '2024-01-25', '2024-01-30'],
            'Risk': ['High', 'Critical', 'Low', 'Medium', 'High', 'Low', 'Medium', 'Low'],
            'Value': ['$500K', '$320K', '$150K', '$280K', '$420K', '$190K', '$350K', '$120K']
        })
        
        # Apply filters
        filtered_data = shipments_data
        
        if status_filter != "All":
            filtered_data = filtered_data[filtered_data['Status'] == status_filter]
        
        if mode_filter != "All":
            filtered_data = filtered_data[filtered_data['Mode'] == mode_filter]
        
        if risk_filter != "All":
            filtered_data = filtered_data[filtered_data['Risk'] == risk_filter]
        
        if search_query:
            filtered_data = filtered_data[
                filtered_data['ID'].str.contains(search_query, case=False) |
                filtered_data['Tracking'].str.contains(search_query, case=False)
            ]
        
        # Display table
        st.dataframe(
            filtered_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "Tracking": st.column_config.TextColumn("Tracking", width="medium"),
                "Origin": st.column_config.TextColumn("Origin", width="medium"),
                "Destination": st.column_config.TextColumn("Destination", width="medium"),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    width="small",
                    options=["In Transit", "Delayed", "On Time", "At Risk", "Pending"],
                    required=True
                ),
                "Mode": st.column_config.TextColumn("Mode", width="small"),
                "ETA": st.column_config.DateColumn("ETA", format="YYYY-MM-DD"),
                "Risk": st.column_config.TextColumn("Risk", width="small"),
                "Value": st.column_config.TextColumn("Value", width="small")
            }
        )
        
        # Statistics
        st.subheader("📊 Shipment Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Shipments", len(filtered_data))
        
        with col2:
            at_risk = len(filtered_data[filtered_data['Risk'].isin(['High', 'Critical'])])
            st.metric("At Risk", at_risk)
        
        with col3:
            delayed = len(filtered_data[filtered_data['Status'] == 'Delayed'])
            st.metric("Delayed", delayed)
        
        with col4:
            on_time = len(filtered_data[filtered_data['Status'] == 'On Time'])
            st.metric("On Time", on_time)
    
    with tab2:
        st.subheader("Create New Shipment")
        
        with st.form("create_shipment"):
            col1, col2 = st.columns(2)
            
            with col1:
                tracking_number = st.text_input("Tracking Number", value=f"TRK{int(datetime.now().timestamp())}")
                reference_number = st.text_input("Reference Number", value=f"SH-{len(shipments_data) + 1:03d}")
                origin = st.text_input("Origin", "Shanghai, China")
                destination = st.text_input("Destination", "Rotterdam, Netherlands")
                mode = st.selectbox("Transport Mode", ["Sea", "Air", "Land", "Rail", "Multimodal"])
            
            with col2:
                weight = st.number_input("Weight (kg)", min_value=0.0, value=10000.0)
                volume = st.number_input("Volume (m³)", min_value=0.0, value=25.0)
                value = st.number_input("Value (USD)", min_value=0.0, value=100000.0)
                shipper = st.text_input("Shipper", "Acme Corporation")
                carrier = st.text_input("Carrier", "Maersk Line")
                consignee = st.text_input("Consignee", "Global Imports BV")
            
            # Estimated dates
            col1, col2 = st.columns(2)
            with col1:
                estimated_departure = st.date_input("Estimated Departure", datetime.now() + timedelta(days=1))
            with col2:
                estimated_arrival = st.date_input("Estimated Arrival", datetime.now() + timedelta(days=15))
            
            # Submit button
            submitted = st.form_submit_button("Create Shipment", use_container_width=True)
            
            if submitted:
                st.success(f"Shipment {tracking_number} created successfully!")
                st.info("The shipment will now be monitored by the autonomous control tower.")
    
    with tab3:
        st.subheader("Shipment Details")
        
        # Select shipment
        selected_id = st.selectbox(
            "Select Shipment",
            shipments_data['ID'].tolist(),
            key="shipment_selector"
        )
        
        if selected_id:
            shipment = shipments_data[shipments_data['ID'] == selected_id].iloc[0]
            
            # Shipment details in columns
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Current Status", shipment['Status'])
                st.metric("Risk Level", shipment['Risk'])
                st.metric("Transport Mode", shipment['Mode'])
                st.metric("Estimated Value", shipment['Value'])
            
            with col2:
                st.metric("Origin", shipment['Origin'])
                st.metric("Destination", shipment['Destination'])
                st.metric("ETA", shipment['ETA'])
                st.metric("Tracking", shipment['Tracking'])
            
            # Timeline
            st.subheader("📅 Shipment Timeline")
            
            timeline_data = pd.DataFrame({
                'Event': ['Order Placed', 'Departure', 'Port Entry', 'Customs Clearance', 
                         'Current Location', 'Estimated Arrival'],
                'Date': ['2024-01-01', '2024-01-05', '2024-01-10', '2024-01-11', 
                        '2024-01-13', '2024-01-15'],
                'Status': ['Completed', 'Completed', 'Completed', 'In Progress', 
                          'Current', 'Pending'],
                'Location': ['Shanghai', 'Shanghai Port', 'Singapore Port', 'Singapore Port',
                           'Indian Ocean', 'Rotterdam']
            })
            
            fig = go.Figure()
            
            for i, row in timeline_data.iterrows():
                color = {
                    'Completed': '#588157',
                    'In Progress': '#2E86AB',
                    'Current': '#F4A261',
                    'Pending': '#6D6875'
                }.get(row['Status'], '#6D6875')
                
                fig.add_trace(go.Scatter(
                    x=[row['Date'], row['Date']],
                    y=[i, i],
                    mode='markers+text',
                    marker=dict(size=20, color=color),
                    text=[row['Event'], ''],
                    textposition="bottom center",
                    hoverinfo='text',
                    hovertext=f"{row['Event']}<br>{row['Location']}<br>Status: {row['Status']}"
                ))
            
            fig.update_layout(
                title="Shipment Progress Timeline",
                xaxis_title="Date",
                yaxis=dict(
                    ticktext=timeline_data['Event'].tolist(),
                    tickvals=list(range(len(timeline_data))),
                    title="Events"
                ),
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent events
            st.subheader("📋 Recent Events")
            
            events_data = pd.DataFrame({
                'Timestamp': ['2024-01-13 10:30', '2024-01-12 14:15', '2024-01-11 09:45',
                             '2024-01-10 16:20', '2024-01-09 11:10'],
                'Event': ['Location update: Indian Ocean', 'Customs clearance initiated',
                         'Arrived at Singapore Port', 'Departed Shanghai Port',
                         'Shipment documentation completed'],
                'Type': ['Location', 'Customs', 'Arrival', 'Departure', 'Documentation']
            })
            
            st.dataframe(events_data, use_container_width=True, hide_index=True)
            
            # Risk information
            if shipment['Risk'] in ['High', 'Critical']:
                st.warning(f"⚠️ This shipment is at {shipment['Risk']} risk level")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Detected Risks", "3")
                with col2:
                    st.metric("Mitigations Applied", "2")
                
                # Risk details
                with st.expander("View Risk Details"):
                    risks_data = pd.DataFrame({
                        'Risk Type': ['Port Congestion', 'Customs Delay', 'Weather Impact'],
                        'Severity': ['High', 'Medium', 'Low'],
                        'Detected': ['2024-01-10', '2024-01-11', '2024-01-12'],
                        'Status': ['Mitigated', 'Monitoring', 'Resolved'],
                        'Action': ['Rerouted', 'Expedited', 'Schedule Adjusted']
                    })
                    
                    st.dataframe(risks_data, use_container_width=True, hide_index=True)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Trigger Risk Check", use_container_width=True):
                    st.info(f"Risk check triggered for {selected_id}")
            
            with col2:
                if st.button("📍 Update Location", use_container_width=True):
                    st.info(f"Location update interface for {selected_id}")
            
            with col3:
                if st.button("📋 View Full History", use_container_width=True):
                    st.info(f"Showing full history for {selected_id}")

if __name__ == "__main__":
    main()