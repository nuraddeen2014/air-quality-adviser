# app.py
from dotenv import load_dotenv

load_dotenv()  # Must run before importing modules that depend on environment variables

import streamlit as st
from core.air_quality import fetch_air_quality
from core.input_validation import validate_and_clean_location
from risk_logic import analyze_risk
from core.storage import LocationHistoryStore
from core.models import AirReading
from core.ai_helper import generate_ai_health_advice

# Page setup
st.set_page_config(
    page_title="Air Quality & Health Advisor", page_icon="🌤️", layout="wide"
)

# Initialize Storage
store = LocationHistoryStore()

st.title("🌤️ Air Quality & Health Advisor")
st.caption(
    "Real-time air quality metrics, EPA risk calculation, and personalized advice."
)

# ---------------------------------------------------------------------------
# Sidebar: User Profile Settings
# ---------------------------------------------------------------------------
st.sidebar.header("👤 Profile Settings")
age_group = st.sidebar.selectbox(
    "Age Group",
    options=["adult", "child", "older_adult"],
    format_func=lambda x: x.replace("_", " ").title(),
)
has_respiratory = st.sidebar.checkbox("Respiratory Condition (Asthma, COPD, etc.)")

user_profile = {"age_group": age_group, "has_respiratory_condition": has_respiratory}

# ---------------------------------------------------------------------------
# Sidebar: Clickable Favorites List
# ---------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("⭐ Saved Favorites")

favorites = getattr(
    store, "load_favourites", getattr(store, "load_favorites", lambda: [])
)()

if favorites:
    st.sidebar.caption("Click any city below to view its live report:")
    for fav in favorites:
        # Each favorite is an active, full-width button
        if st.sidebar.button(f"📍 {fav}", key=f"fav_{fav}", use_container_width=True):
            st.session_state["active_city"] = fav
            st.rerun()
else:
    st.sidebar.info("No saved favorites yet.")

# ---------------------------------------------------------------------------
# Main Search Interface
# ---------------------------------------------------------------------------
col_input, col_btn = st.columns([4, 1])

with col_input:
    current_city = st.session_state.get("active_city", "")
    city_input = st.text_input(
        "Enter City Name:",
        value=current_city,
        placeholder="e.g. Lagos, London, Tokyo",
        key="city_search_input",
    )

with col_btn:
    st.write("")
    search_clicked = st.button(
        "Check Air Quality", type="primary", use_container_width=True
    )

# Handle search submission
if search_clicked and city_input:
    st.session_state["active_city"] = city_input

active_city = st.session_state.get("active_city")

# ---------------------------------------------------------------------------
# Render Report when an Active City is Selected
# ---------------------------------------------------------------------------
if active_city:
    clean_city = validate_and_clean_location(active_city)

    if not clean_city:
        st.error("⚠️ Invalid city name. Please enter a valid location.")
    else:
        with st.spinner(f"Fetching air quality for **{clean_city}**..."):
            raw_response = fetch_air_quality(clean_city)

        if "error" in raw_response:
            st.error(f"❌ {raw_response['error']}")
        else:
            # 1. Parse using model factory
            reading = AirReading.from_open_meteo(clean_city.title(), raw_response)

            # 2. Analyze EPA Air Quality Risk
            pollutant_dict = reading.to_pollutant_dict()
            risk = analyze_risk(pollutants=pollutant_dict, profile=user_profile)

            # 3. Save Reading to History
            store.save_reading(reading.to_dict())

            # ---------------------------------------------------------------------------
            # Display Report Metrics
            # ---------------------------------------------------------------------------
            st.markdown("---")
            header_col, fav_col = st.columns([3, 1])

            with header_col:
                st.subheader(f"📍 Report for {reading.city}")
                st.caption(
                    f"Coords: {reading.latitude:.2f}°, {reading.longitude:.2f}° | Updated: {reading.timestamp}"
                )

            with fav_col:
                if st.button("⭐ Add to Favorites", key="add_fav_btn"):
                    save_fav = getattr(
                        store, "save_favourite", getattr(store, "save_favorite", None)
                    )
                    if save_fav:
                        save_fav(reading.city)
                        st.success(f"Saved {reading.city}!")
                        st.rerun()  # Instantly refresh sidebar to show new button

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("EPA AQI", risk.get("aqi", "N/A"))
            m2.metric("Category", risk.get("level", "Unknown"))
            m3.metric(
                "Dominant Pollutant", str(risk.get("dominant_pollutant", "N/A")).upper()
            )
            m4.metric("Outdoor Status", risk.get("outdoor_status", "N/A"))

            if risk.get("outdoor_safe"):
                st.success(f"🟢 **Safe:** {risk.get('advice')}")
            else:
                st.warning(f"⚠️ **Caution:** {risk.get('advice')}")

            # Pollutants Breakdown
            st.markdown("### 📊 Measured Pollutants")
            p1, p2, p3, p4 = st.columns(4)
            p1.metric(
                "PM2.5",
                f"{reading.pm2_5} µg/m³" if reading.pm2_5 is not None else "N/A",
            )
            p2.metric(
                "PM10", f"{reading.pm10} µg/m³" if reading.pm10 is not None else "N/A"
            )
            p3.metric(
                "NO₂",
                (
                    f"{reading.nitrogen_dioxide} µg/m³"
                    if reading.nitrogen_dioxide is not None
                    else "N/A"
                ),
            )
            p4.metric(
                "Ozone (O₃)",
                f"{reading.ozone} µg/m³" if reading.ozone is not None else "N/A",
            )

            # AI Guidance Section
            st.markdown("---")
            st.markdown("### 🤖 Personalized AI Guidance")

            with st.spinner("Generating insights..."):
                ai_advice = generate_ai_health_advice(reading.city, risk, user_profile)
                st.markdown(ai_advice)

                if hasattr(store, "save_health_advice"):
                    store.save_health_advice(
                        {
                            "city": reading.city,
                            "timestamp": reading.timestamp,
                            "advice": ai_advice,
                        }
                    )

# ---------------------------------------------------------------------------
# Search History Section
# ---------------------------------------------------------------------------
st.markdown("---")
with st.expander("📜 Recent Search History"):
    history = store.load_readings()
    if history:
        st.dataframe(history, use_container_width=True)
    else:
        st.info("No search history recorded yet.")
