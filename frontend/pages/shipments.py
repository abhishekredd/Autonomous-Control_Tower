import streamlit as st
import pandas as pd
from datetime import datetime

def show_shipments():
    """Shipments page for multi-page app"""
    
    # Get API functions from main app
    from app import fetch_shipments, create_shipment, fetch_shipment_details
    
    st.title("📦 Shipment Management")
    
    # Tabs
    tab1, tab2 = st.tabs(["All Shipments", "Create New"])
    
    with tab1:
        # Fetch shipments
        shipments = fetch_shipments()
        
        if shipments:
            df = pd.DataFrame(shipments)
            
            # Search and filter
            col1, col2 = st.columns(2)
            with col1:
                search_term = st.text_input("Search shipments")
            with col2:
                status_filter = st.selectbox(
                    "Filter by status",
                    ["ALL", "IN_TRANSIT", "DELAYED", "DELIVERED", "PENDING"]
                )
            
            # Apply filters
            filtered_df = df
            if search_term:
                filtered_df = filtered_df[
                    filtered_df['shipment_id'].str.contains(search_term, case=False) |
                    filtered_df['origin'].str.contains(search_term, case=False) |
                    filtered_df['destination'].str.contains(search_term, case=False)
                ]
            
            if status_filter != "ALL":
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            
            # Display table
            st.dataframe(
                filtered_df[['shipment_id', 'origin', 'destination', 'status', 'risk_score', 'estimated_value']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No shipments found")
    
    with tab2:
        st.subheader("Create New Shipment")
        
        with st.form("create_shipment"):
            col1, col2 = st.columns(2)
            
            with col1:
                shipment_id = st.text_input("Shipment ID", 
                                          value=f"SH{datetime.now().strftime('%Y%m%d%H%M')}")
                origin = st.text_input("Origin", "Shanghai, China")
                destination = st.text_input("Destination", "Rotterdam, Netherlands")
            
            with col2:
                carrier = st.selectbox("Carrier", 
                                     ["MAERSK", "CMA CGM", "MSC", "COSCO", "HAPAG-LLOYD"])
                estimated_value = st.number_input("Estimated Value (USD)", 
                                                 min_value=1000, value=50000)
            
            if st.form_submit_button("Create Shipment"):
                shipment_data = {
                    "shipment_id": shipment_id,
                    "origin": origin,
                    "destination": destination,
                    "carrier": carrier,
                    "estimated_value": float(estimated_value),
                    "status": "PENDING"
                }
                
                result = create_shipment(shipment_data)
                if result:
                    st.success(f"Shipment {shipment_id} created!")
                    st.rerun()
                else:
                    st.error("Failed to create shipment")

if __name__ == "__main__":
    show_shipments()