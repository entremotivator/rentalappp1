# =====================================================
# pages/1_🏠_Property_Search.py
# =====================================================

import streamlit as st
import json
from utils.auth import initialize_auth_state
from utils.rentcast_api import fetch_property_details
from utils.database import get_user_usage
from streamlit.components.v1 import html

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
# 4. Helper: Build Card HTML
# =====================================================
def build_card(title: str, content: str) -> str:
    return f"""
    <div class="card">
        <h3>{title}</h3>
        <div class="content">{content}</div>
    </div>
    """


# =====================================================
# 5. Property Search Logic
# =====================================================
if st.button("🔍 Search Property", type="primary", use_container_width=True):
    if not address:
        st.error("❌ Please enter a property address.")
    else:
        with st.spinner("🔎 Fetching property data..."):
            try:
                property_data = fetch_property_details(address, user_id, user_email)

                if not property_data or "properties" not in property_data:
                    st.error("⚠️ No property data found.")
                    st.stop()

                prop = property_data["properties"][0]
                pretty_json = json.dumps(prop, indent=2)

                # =====================================================
                # Build Cards
                # =====================================================
                cards_html = ""

                # Basic Info
                basic_info = f"""
                <b>Type:</b> {prop.get("propertyType","N/A")}<br>
                <b>Bedrooms:</b> {prop.get("bedrooms","N/A")}<br>
                <b>Bathrooms:</b> {prop.get("bathrooms","N/A")}<br>
                <b>Sq Ft:</b> {prop.get("squareFootage","N/A")}<br>
                <b>Lot Size:</b> {prop.get("lotSize","N/A")}<br>
                <b>Year Built:</b> {prop.get("yearBuilt","N/A")}
                """
                cards_html += build_card("🏠 Basic Information", basic_info)

                # Address
                addr = prop.get("formattedAddress", "N/A")
                cards_html += build_card("📍 Address", addr)

                # Features
                if "features" in prop:
                    feat = prop["features"]
                    features_html = "<br>".join([f"<b>{k}:</b> {v}" for k,v in feat.items()])
                    cards_html += build_card("🔧 Features", features_html)

                # Property Taxes
                if "propertyTaxes" in prop:
                    tax_html = "<br>".join([
                        f"<b>{year}:</b> ${data['total']:,}" 
                        for year, data in prop["propertyTaxes"].items()
                    ])
                    cards_html += build_card("💰 Property Taxes", tax_html)

                # Tax Assessments
                if "taxAssessments" in prop:
                    assess_html = "<br>".join([
                        f"<b>{year}:</b> Total {data['value']:,} (Land {data['land']:,}, Improvements {data['improvements']:,})"
                        for year, data in prop["taxAssessments"].items()
                    ])
                    cards_html += build_card("📊 Tax Assessments", assess_html)

                # History
                if "history" in prop:
                    hist_html = "<br>".join([
                        f"<b>{h['event']}:</b> {h['date']} for ${h['price']:,}"
                        for h in prop["history"].values()
                    ])
                    cards_html += build_card("📜 History", hist_html)

                # Owner Info
                if "owner" in prop:
                    owner = prop["owner"]
                    owner_html = f"""
                    <b>Owner:</b> {", ".join(owner.get("names", []))}<br>
                    <b>Type:</b> {owner.get("type","N/A")}<br>
                    <b>Mailing Address:</b> {owner.get("mailingAddress",{}).get("formattedAddress","N/A")}
                    """
                    cards_html += build_card("👤 Owner Info", owner_html)

                # Raw JSON
                cards_html += build_card("📋 Raw JSON", f"<pre>{pretty_json}</pre>")

                # =====================================================
                # Render Final Layout
                # =====================================================
                full_html = f"""
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        color: #2c3e50;
                    }}
                    .container {{
                        display: flex;
                        flex-wrap: wrap;
                        justify-content: flex-start;
                    }}
                    .card {{
                        background: #fff;
                        padding: 20px;
                        margin: 15px;
                        border-radius: 12px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        flex: 1 1 320px;
                        transition: transform 0.2s ease, box-shadow 0.2s ease;
                    }}
                    .card:hover {{
                        transform: translateY(-4px);
                        box-shadow: 0 6px 16px rgba(0,0,0,0.15);
                    }}
                    .card h3 {{
                        margin-top: 0;
                        color: #34495e;
                        font-size: 18px;
                    }}
                    .content {{
                        font-size: 14px;
                        line-height: 1.6;
                    }}
                    pre {{
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        background: #f7f7f7;
                        padding: 10px;
                        border-radius: 8px;
                        font-size: 12px;
                    }}
                </style>
                <div class="container">
                    {cards_html}
                </div>
                """
                html(full_html, height=900, scrolling=True)

            except Exception as e:
                st.error(f"❌ Error fetching property data: {str(e)}")


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
""")
