# =====================================================
# pages/1_🏠_Property_Search.py
# =====================================================

import streamlit as st
import json
import logging
from utils.auth import initialize_auth_state
from utils.rentcast_api import fetch_property_details
from utils.database import get_user_usage
from streamlit.components.v1 import html

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Property Search", page_icon="🏠", layout="wide")

# =====================================================
# 1. Initialize & Auth
# =====================================================
initialize_auth_state()

if st.session_state.user is None:
    st.warning("⚠️ Please log in from the main page to access this feature.")
    st.stop()

user_email = st.session_state.user.email
user_id = st.session_state.user.id

# =====================================================
# 2. Sidebar (Usage / Limits)
# =====================================================
with st.sidebar:
    st.subheader("👤 Account Info")
    queries_used = get_user_usage(user_id, user_email)

    st.metric("Email", user_email)
    st.metric("Queries Used", f"{queries_used}/30")

    if queries_used >= 30:
        st.error("🚫 Query limit reached!")
    elif queries_used >= 25:
        st.warning("⚠️ Approaching limit!")


# =====================================================
# 3. Search Form
# =====================================================
st.title("🏠 Property Search")
st.markdown("Retrieve detailed property information with a clean, card-based layout.")

address = st.text_input(
    "Enter Property Address",
    placeholder="e.g., 123 Main St, New York, NY 10001",
    help="Enter a complete address for best results"
)


# =====================================================
# 4. Helper Functions
# =====================================================
def safe_get(data, key, default="N/A"):
    """Safely get a value from dict with default fallback"""
    try:
        value = data.get(key, default)
        return value if value is not None and value != "" else default
    except (AttributeError, TypeError):
        return default


def format_currency(value):
    """Format currency values safely"""
    try:
        if isinstance(value, (int, float)) and value > 0:
            return f"${value:,.0f}"
        elif isinstance(value, str) and value.replace(',', '').replace('$', '').isdigit():
            return f"${int(value.replace(',', '').replace('$', '')):,}"
        return "N/A"
    except (ValueError, TypeError):
        return "N/A"


def build_card(title: str, content: str) -> str:
    """Build HTML card component"""
    return f"""
    <div class="card">
        <h3>{title}</h3>
        <div class="content">{content}</div>
    </div>
    """


def process_property_data(raw_data):
    """Process and validate property data from API response"""
    try:
        # Debug logging
        logger.info(f"Raw API response type: {type(raw_data)}")
        logger.info(f"Raw API response: {str(raw_data)[:500]}...")
        
        # Handle different response formats
        if isinstance(raw_data, str):
            try:
                property_data = json.loads(raw_data)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return None
        elif isinstance(raw_data, (dict, list)):
            property_data = raw_data
        else:
            logger.error(f"Unexpected data type: {type(raw_data)}")
            return None
        
        # Check for properties in response
        if not property_data:
            logger.error("Empty property data received")
            return None
            
        # Handle different API response structures
        properties = None
        
        # Case 1: Direct list of properties (like your API response)
        if isinstance(property_data, list) and len(property_data) > 0:
            properties = property_data
        # Case 2: Dictionary with "properties" key
        elif isinstance(property_data, dict) and "properties" in property_data:
            properties = property_data["properties"]
        # Case 3: Dictionary with "data" key
        elif isinstance(property_data, dict) and "data" in property_data:
            properties = property_data["data"]
        # Case 4: Single property object (has property-like keys)
        elif isinstance(property_data, dict) and any(key in property_data for key in ["formattedAddress", "propertyType", "bedrooms", "id"]):
            properties = [property_data]
        
        if not properties or len(properties) == 0:
            logger.error("No properties found in response")
            return None
            
        # Return the first property
        first_property = properties[0]
        logger.info(f"Successfully processed property: {first_property.get('formattedAddress', 'Unknown Address')}")
        return first_property
        
    except Exception as e:
        logger.error(f"Error processing property data: {e}")
        return None


# =====================================================
# 5. Property Search Logic
# =====================================================
if st.button("🔍 Search Property", type="primary", use_container_width=True):
    if not address:
        st.error("❌ Please enter a property address.")
    else:
        with st.spinner("🔎 Fetching property data..."):
            try:
                # Fetch raw data from API
                raw_response = fetch_property_details(address, user_id, user_email)
                
                if not raw_response:
                    st.error("⚠️ No response from API. Please try again.")
                    st.stop()
                
                # Process the response
                prop = process_property_data(raw_response)
                
                if not prop:
                    st.error("⚠️ No property data found or invalid response format.")
                    # Show debug info
                    with st.expander("Debug: Raw API Response"):
                        st.code(str(raw_response)[:2000] + "..." if len(str(raw_response)) > 2000 else str(raw_response))
                    st.stop()

                # Display success message
                st.success(f"✅ Property found: {safe_get(prop, 'address', address)}")

                # =====================================================
                # Build Property Information Cards
                # =====================================================
                cards_html = ""

                # Basic Property Information
                basic_info = f"""
                <b>Property Type:</b> {safe_get(prop, 'propertyType')}<br>
                <b>Bedrooms:</b> {safe_get(prop, 'bedrooms')}<br>
                <b>Bathrooms:</b> {safe_get(prop, 'bathrooms')}<br>
                <b>Square Footage:</b> {safe_get(prop, 'squareFootage')} sq ft<br>
                <b>Lot Size:</b> {safe_get(prop, 'lotSize')}<br>
                <b>Year Built:</b> {safe_get(prop, 'yearBuilt')}<br>
                <b>Stories:</b> {safe_get(prop, 'stories')}
                """
                cards_html += build_card("🏠 Basic Information", basic_info)

                # Address Information
                address_info = f"""
                <b>Full Address:</b> {safe_get(prop, 'formattedAddress', safe_get(prop, 'address'))}<br>
                <b>Street:</b> {safe_get(prop, 'addressLine1')}<br>
                <b>City:</b> {safe_get(prop, 'city')}<br>
                <b>State:</b> {safe_get(prop, 'state')}<br>
                <b>ZIP Code:</b> {safe_get(prop, 'zipCode')}<br>
                <b>County:</b> {safe_get(prop, 'county')}
                """
                cards_html += build_card("📍 Address", address_info)

                # Valuation Information
                valuation_info = ""
                estimated_value = safe_get(prop, 'estimatedValue')
                if estimated_value != "N/A":
                    valuation_info += f"<b>Estimated Value:</b> {format_currency(estimated_value)}<br>"
                
                market_value = safe_get(prop, 'marketValue')
                if market_value != "N/A":
                    valuation_info += f"<b>Market Value:</b> {format_currency(market_value)}<br>"
                
                assessed_value = safe_get(prop, 'assessedValue')
                if assessed_value != "N/A":
                    valuation_info += f"<b>Assessed Value:</b> {format_currency(assessed_value)}<br>"
                
                if valuation_info:
                    cards_html += build_card("💰 Property Valuation", valuation_info)

                # Features & Amenities
                features = safe_get(prop, 'features')
                if features != "N/A" and isinstance(features, dict):
                    features_html = "<br>".join([
                        f"<b>{k.replace('_', ' ').title()}:</b> {v}" 
                        for k, v in features.items() if v
                    ])
                    if features_html:
                        cards_html += build_card("🔧 Features & Amenities", features_html)

                # Property Taxes
                property_taxes = safe_get(prop, 'propertyTaxes')
                if property_taxes != "N/A" and isinstance(property_taxes, dict):
                    tax_html = ""
                    for year, tax_data in property_taxes.items():
                        if isinstance(tax_data, dict):
                            total = format_currency(tax_data.get('total', 0))
                            tax_html += f"<b>{year}:</b> {total}<br>"
                        else:
                            tax_html += f"<b>{year}:</b> {format_currency(tax_data)}<br>"
                    
                    if tax_html:
                        cards_html += build_card("🏛️ Property Taxes", tax_html)

                # Tax Assessments
                tax_assessments = safe_get(prop, 'taxAssessments')
                if tax_assessments != "N/A" and isinstance(tax_assessments, dict):
                    assess_html = ""
                    for year, assessment in tax_assessments.items():
                        if isinstance(assessment, dict):
                            total_val = format_currency(assessment.get('value', 0))
                            land_val = format_currency(assessment.get('land', 0))
                            improvements_val = format_currency(assessment.get('improvements', 0))
                            assess_html += f"<b>{year}:</b><br>"
                            assess_html += f"&nbsp;&nbsp;Total: {total_val}<br>"
                            assess_html += f"&nbsp;&nbsp;Land: {land_val}<br>"
                            assess_html += f"&nbsp;&nbsp;Improvements: {improvements_val}<br>"
                    
                    if assess_html:
                        cards_html += build_card("📊 Tax Assessments", assess_html)

                # Sale History
                history = safe_get(prop, 'history')
                if history != "N/A" and isinstance(history, (dict, list)):
                    hist_html = ""
                    if isinstance(history, dict):
                        for event_key, event_data in history.items():
                            if isinstance(event_data, dict):
                                event_type = event_data.get('event', 'Sale')
                                date = event_data.get('date', 'Unknown')
                                price = format_currency(event_data.get('price', 0))
                                hist_html += f"<b>{event_type}:</b> {date} - {price}<br>"
                    elif isinstance(history, list):
                        for event in history:
                            if isinstance(event, dict):
                                event_type = event.get('event', 'Sale')
                                date = event.get('date', 'Unknown')
                                price = format_currency(event.get('price', 0))
                                hist_html += f"<b>{event_type}:</b> {date} - {price}<br>"
                    
                    if hist_html:
                        cards_html += build_card("📜 Sale History", hist_html)

                # Owner Information
                owner = safe_get(prop, 'owner')
                if owner != "N/A" and isinstance(owner, dict):
                    owner_html = ""
                    names = owner.get('names', [])
                    if names:
                        owner_html += f"<b>Owner(s):</b> {', '.join(names)}<br>"
                    
                    owner_type = safe_get(owner, 'type')
                    if owner_type != "N/A":
                        owner_html += f"<b>Owner Type:</b> {owner_type}<br>"
                    
                    mailing_address = owner.get('mailingAddress', {})
                    if isinstance(mailing_address, dict):
                        formatted_addr = safe_get(mailing_address, 'formattedAddress')
                        if formatted_addr != "N/A":
                            owner_html += f"<b>Mailing Address:</b> {formatted_addr}<br>"
                    
                    if owner_html:
                        cards_html += build_card("👤 Owner Information", owner_html)

                # Raw JSON Data (for debugging)
                try:
                    pretty_json = json.dumps(prop, indent=2, default=str)
                    if len(pretty_json) > 5000:
                        pretty_json = pretty_json[:5000] + "\n\n... (truncated)"
                    cards_html += build_card("📋 Raw JSON Data", f"<pre>{pretty_json}</pre>")
                except Exception as e:
                    cards_html += build_card("📋 Raw JSON Data", f"<pre>Error displaying JSON: {str(e)}</pre>")

                # =====================================================
                # Render Final Layout
                # =====================================================
                if not cards_html:
                    st.warning("⚠️ No property information could be extracted from the response.")
                else:
                    full_html = f"""
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            color: #2c3e50;
                            background-color: #f8f9fa;
                        }}
                        .container {{
                            display: grid;
                            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                            gap: 20px;
                            padding: 10px;
                        }}
                        .card {{
                            background: #ffffff;
                            padding: 24px;
                            border-radius: 12px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                            transition: all 0.3s ease;
                            border: 1px solid #e9ecef;
                        }}
                        .card:hover {{
                            transform: translateY(-2px);
                            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                        }}
                        .card h3 {{
                            margin-top: 0;
                            margin-bottom: 16px;
                            color: #2c3e50;
                            font-size: 20px;
                            font-weight: 600;
                            border-bottom: 2px solid #3498db;
                            padding-bottom: 8px;
                        }}
                        .content {{
                            font-size: 14px;
                            line-height: 1.8;
                            color: #495057;
                        }}
                        .content b {{
                            color: #2c3e50;
                            font-weight: 600;
                        }}
                        pre {{
                            white-space: pre-wrap;
                            word-wrap: break-word;
                            background: #f8f9fa;
                            padding: 16px;
                            border-radius: 8px;
                            font-size: 12px;
                            border: 1px solid #dee2e6;
                            max-height: 400px;
                            overflow-y: auto;
                        }}
                        @media (max-width: 768px) {{
                            .container {{
                                grid-template-columns: 1fr;
                            }}
                        }}
                    </style>
                    <div class="container">
                        {cards_html}
                    </div>
                    """
                    html(full_html, height=1200, scrolling=True)

            except Exception as e:
                logger.error(f"Error in property search: {e}")
                st.error(f"❌ Error fetching property data: {str(e)}")
                
                # Show debug information
                with st.expander("🔍 Debug Information"):
                    st.text(f"Error Type: {type(e).__name__}")
                    st.text(f"Error Message: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())


# =====================================================
# 6. Helpful Tips
# =====================================================
st.markdown("---")
st.subheader("💡 Tips for Better Results")
st.markdown("""
- Include the **full address** with city, state, and ZIP code  
- Use standard address formatting (e.g., `123 Main St, New York, NY 10001`)  
- Double-check spelling of **street/city names**  
- For apartments/condos, include **unit numbers** if possible  
- If no results are found, try variations of the address format
- Check the Raw JSON Data card for complete API response details
""")

# Debug section (only show if there are issues)
if st.checkbox("🔧 Show Debug Mode", help="Enable to see additional debugging information"):
    st.info("Debug mode enabled. Additional logging and error information will be displayed.")
