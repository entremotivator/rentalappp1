# =====================================================
# pages/1_🏠_Property_Search.py
# =====================================================

import streamlit as st
import json
import pandas as pd
from utils.auth import initialize_auth_state
from utils.rentcast_api import fetch_property_details
from utils.database import get_user_usage

st.set_page_config(page_title="Property Search", page_icon="🏠")

# Initialize auth state
initialize_auth_state()

# Check if user is authenticated
if st.session_state.user is None:
    st.warning("Please log in from the main page to access this feature.")
    st.stop()

st.title("🏠 Property Search")
st.markdown("Search for detailed property information and analytics.")

# User info sidebar
with st.sidebar:
    st.subheader("Account Info")
    user_email = st.session_state.user.email
    user_id = st.session_state.user.id
    queries_used = get_user_usage(user_id, user_email)
    
    st.metric("Email", user_email)
    st.metric("Queries Used", f"{queries_used}/30")
    
    if queries_used >= 30:
        st.error("🚫 Query limit reached!")
    elif queries_used >= 25:
        st.warning("⚠️ Approaching limit!")

# Main content
st.subheader("🔍 Search Property")
address = st.text_input(
    "Enter Property Address",
    placeholder="e.g., 123 Main St, New York, NY 10001",
    help="Enter a complete address for best results"
)

if st.button("🔍 Search Property", type="primary", use_container_width=True):
    if not address:
        st.error("Please enter a property address.")
    else:
        with st.spinner("Searching property data..."):
            # Fetch property details (no market data)
            property_data = fetch_property_details(address, user_id, user_email)
            
            if property_data:
                st.success("✅ Property data retrieved successfully!")
                
                # Display property information in organized tabs
                tab1, tab2 = st.tabs(["🏠 Property Details", "📋 JSON Data"])
                
                with tab1:
                    if "properties" in property_data and property_data["properties"]:
                        prop = property_data["properties"][0]
                        
                        # Basic property info
                        st.subheader("Basic Information")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Property Type", prop.get("propertyType", "N/A"))
                            st.metric("Bedrooms", prop.get("bedrooms", "N/A"))
                        
                        with col2:
                            st.metric("Bathrooms", prop.get("bathrooms", "N/A"))
                            st.metric("Square Feet", prop.get("squareFootage", "N/A"))
                        
                        with col3:
                            st.metric("Year Built", prop.get("yearBuilt", "N/A"))
                            st.metric("Lot Size", prop.get("lotSize", "N/A"))
                        
                        # Address information
                        if "address" in prop:
                            addr = prop["address"]
                            st.subheader("Address Details")
                            st.text(f"{addr.get('line1', '')} {addr.get('line2', '')}")
                            st.text(f"{addr.get('city', '')}, {addr.get('state', '')} {addr.get('zipCode', '')}")
                        
                        # Financial information
                        st.subheader("Estimated Values")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if "rentEstimate" in prop:
                                rent_est = prop["rentEstimate"]
                                st.metric("Rent Estimate", f"${rent_est.get('rent', 'N/A'):,}/month")
                        
                        with col2:
                            if "valueEstimate" in prop:
                                value_est = prop["valueEstimate"]
                                st.metric("Property Value", f"${value_est.get('value', 'N/A'):,}")
                    else:
                        st.warning("No property details found for this address.")
                
                with tab2:
                    # Display JSON data in a card
                    with st.container():
                        st.subheader("📋 Complete JSON Response")
                        
                        # Create a card-like appearance using markdown and containers
                        with st.expander("View Raw JSON Data", expanded=True):
                            # Pretty print JSON with syntax highlighting
                            json_str = json.dumps(property_data, indent=2)
                            st.code(json_str, language='json')
                        
                        # Alternative card display with key information
                        if "properties" in property_data and property_data["properties"]:
                            st.subheader("📊 Key Data Points")
                            prop = property_data["properties"][0]
                            
                            # Create info cards
                            cards_data = []
                            
                            # Basic info card
                            basic_info = {
                                "Category": "Basic Information",
                                "Data": {
                                    "Property Type": prop.get("propertyType", "N/A"),
                                    "Bedrooms": prop.get("bedrooms", "N/A"),
                                    "Bathrooms": prop.get("bathrooms", "N/A"),
                                    "Square Feet": prop.get("squareFootage", "N/A"),
                                    "Year Built": prop.get("yearBuilt", "N/A"),
                                    "Lot Size": prop.get("lotSize", "N/A")
                                }
                            }
                            
                            # Address info card
                            if "address" in prop:
                                addr = prop["address"]
                                address_info = {
                                    "Category": "Address Information",
                                    "Data": {
                                        "Line 1": addr.get("line1", "N/A"),
                                        "Line 2": addr.get("line2", "N/A"),
                                        "City": addr.get("city", "N/A"),
                                        "State": addr.get("state", "N/A"),
                                        "ZIP Code": addr.get("zipCode", "N/A"),
                                        "County": addr.get("county", "N/A")
                                    }
                                }
                                cards_data.append(address_info)
                            
                            # Financial info card
                            financial_info = {"Category": "Financial Estimates", "Data": {}}
                            if "rentEstimate" in prop:
                                rent_est = prop["rentEstimate"]
                                financial_info["Data"]["Rent Estimate"] = f"${rent_est.get('rent', 'N/A'):,}/month"
                                financial_info["Data"]["Rent Range Low"] = f"${rent_est.get('rentRangeLow', 'N/A'):,}/month"
                                financial_info["Data"]["Rent Range High"] = f"${rent_est.get('rentRangeHigh', 'N/A'):,}/month"
                            
                            if "valueEstimate" in prop:
                                value_est = prop["valueEstimate"]
                                financial_info["Data"]["Property Value"] = f"${value_est.get('value', 'N/A'):,}"
                                financial_info["Data"]["Value Range Low"] = f"${value_est.get('valueRangeLow', 'N/A'):,}"
                                financial_info["Data"]["Value Range High"] = f"${value_est.get('valueRangeHigh', 'N/A'):,}"
                            
                            if financial_info["Data"]:
                                cards_data.append(financial_info)
                            
                            cards_data.insert(0, basic_info)
                            
                            # Display cards
                            for card in cards_data:
                                with st.container():
                                    st.markdown(f"**{card['Category']}**")
                                    
                                    # Create columns for the card data
                                    if len(card['Data']) <= 3:
                                        cols = st.columns(len(card['Data']))
                                    else:
                                        cols = st.columns(3)
                                    
                                    items = list(card['Data'].items())
                                    for i, (key, value) in enumerate(items):
                                        col_idx = i % len(cols)
                                        with cols[col_idx]:
                                            st.metric(key, value)
                                    
                                    st.markdown("---")
            else:
                st.error("❌ No property data found. Please check the address and try again.")

# Tips section
st.markdown("---")
st.subheader("💡 Tips for Better Results")
st.markdown("""
- Include the full address with city, state, and ZIP code
- Use standard address formatting (e.g., "123 Main St, New York, NY 10001")
- Check spelling of street names and city names
- For apartments, include unit numbers when possible
""")

# Usage info
st.info("ℹ️ This search only includes property data. Market data has been disabled to optimize performance.")
