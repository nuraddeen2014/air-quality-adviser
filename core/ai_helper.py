# Abdulmalik: Code to connect to the Gemini API
# ai_helper.py
import os
import streamlit as st

try:
    from google import genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def _get_api_key() -> str:
    """Fetches key from environment or Streamlit secrets."""
    key = os.getenv("GEMINI_API_KEY")
    if not key and hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        key = st.secrets["GEMINI_API_KEY"]
    return key or ""


def generate_ai_health_advice(city: str, risk_data: dict, user_profile: dict) -> str:
    """Generates health recommendations based on risk assessment and user profile."""
    api_key = _get_api_key()

    if not GENAI_AVAILABLE or not api_key:
        return (
            f"**Rule-Based Health Guidance for {city}:**\n\n"
            f"- **AQI Level:** {risk_data.get('level', 'Unknown')} (AQI {risk_data.get('aqi', 'N/A')})\n"
            f"- **Outdoor Status:** {risk_data.get('outdoor_status', 'Caution')}\n"
            f"- **Advice:** {risk_data.get('advice', '')}\n\n"
            "*(Set `GEMINI_API_KEY` in environment or secrets for personalized AI recommendations.)*"
        )

    prompt = f"""
    You are an expert Health & Air Quality Advisor.
    Provide concise, actionable health guidance (3 bullet points max + 1 summary sentence) 
    for someone living in or visiting {city}.

    Context:
    - Calculated EPA AQI: {risk_data.get('aqi')} ({risk_data.get('level')})
    - Dominant Pollutant: {risk_data.get('dominant_pollutant')}
    - Outdoor Status: {risk_data.get('outdoor_status')}
    - User Profile: Age Group = {user_profile.get('age_group')}, Respiratory Condition = {user_profile.get('has_respiratory_condition')}
    - Sensitive Individual: {risk_data.get('is_sensitive')}

    Instructions:
    - Address whether outdoor exercise or commuting is safe.
    - Provide specific precautions tailored to their health profile.
    - Keep tone encouraging, clear, and easy to understand.
    """

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Standard Advice for {city}: {risk_data.get('advice', 'Take basic precautions.')}"
