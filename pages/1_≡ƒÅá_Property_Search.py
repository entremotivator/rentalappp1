# =====================================================
# pages/1_🏠_Property_Search.py
# =====================================================

import streamlit as st
import json
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
st.markdown("Search for detailed property information.")

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
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🔍 Search Property")
    address = st.text_input(
        "Enter Property Address",
        placeholder="e.g., 123 Main St, New York, NY 10001",
        help="Enter a complete address for best results"
    )

with col2:
    st.subheader("⚙️ Options")
    show_raw_json = st.checkbox("Show Raw JSON Response", value=False)

# Search button
if st.button("🔍 Search Property", type="primary", use_container_width=True):
    if not address:
        st.error("Please enter a property address.")
    else:
        with st.spinner("Searching property data..."):
            property_data = fetch_property_details(address, user_id, user_email)
            
            if property_data:
                st.success("✅ Property data retrieved successfully!")
                
                # Display property information in organized tabs
                tab1, tab2 = st.tabs(["🏠 Property Details", "📋 Raw Data"])
                
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
                        
                        # Financial estimates if available
                        st.subheader("Estimated Values")
                        col1, col2 = st.columns(2)
                        if "rentEstimate" in prop:
                            rent_est = prop["rentEstimate"]
                            st.metric("Rent Estimate", f"${rent_est.get('rent', 'N/A'):,}/month")
                        if "valueEstimate" in prop:
                            value_est = prop["valueEstimate"]
                            st.metric("Property Value", f"${value_est.get('value', 'N/A'):,}")
                    else:
                        st.warning("No property details found for this address.")
                
                with tab2:
                    if show_raw_json:
                        # Pretty-print JSON for readability
                        st.json(property_data)
                    else:
                        st.info("Enable 'Show Raw JSON Response' to view complete API response.")
            else:
                st.error("No property data found.")

# Helpful tips
st.markdown("---")
st.subheader("💡 Tips for Better Results")
st.markdown("""
- Include the full address with city, state, and ZIP code  
- Use standard address formatting (e.g., "123 Main St, New York, NY 10001")  
- Check spelling of street names and city names  
- For apartments, include unit numbers when possible  
""")
