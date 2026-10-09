# core/ai_helper.py
import os
import streamlit as st
from dotenv import load_dotenv

# Ensure environment variables are loaded from .env
load_dotenv()

try:
    from google import genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def _get_api_key() -> str:
    """Fetches key from environment or Streamlit secrets safely."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            key = ""
    return key or ""


def generate_ai_health_advice(city: str, risk_data: dict, user_profile: dict) -> str:
    """Generates health recommendations based on risk assessment and user profile."""
    api_key = _get_api_key()

    if not GENAI_AVAILABLE:
        return (
            f"**Rule-Based Health Guidance for {city}:**\n\n"
            f"- **AQI Level:** {risk_data.get('level', 'Unknown')} (AQI {risk_data.get('aqi', 'N/A')})\n"
            f"- **Outdoor Status:** {risk_data.get('outdoor_status', 'Caution')}\n"
            f"- **Advice:** {risk_data.get('advice', '')}\n\n"
            "*(Error: `google-genai` package is not installed. Run `pip install google-genai`)*"
        )

    if not api_key:
        return (
            f"**Rule-Based Health Guidance for {city}:**\n\n"
            f"- **AQI Level:** {risk_data.get('level', 'Unknown')} (AQI {risk_data.get('aqi', 'N/A')})\n"
            f"- **Outdoor Status:** {risk_data.get('outdoor_status', 'Caution')}\n"
            f"- **Advice:** {risk_data.get('advice', '')}\n\n"
            "*(Error: `GEMINI_API_KEY` not found in `.env` or `.streamlit/secrets.toml`)*"
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
    - Explain concisely what those numbers mean.
    - Address whether outdoor exercise or commuting is safe.
    - Provide specific precautions tailored to their health profile.
    - Keep tone encouraging, clear, and easy to understand.
    """

    try:
        client = genai.Client(api_key=api_key)

        # Try primary model gemini-3.8-flash (or fall back to gemini-1.5-flash)
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )
        except Exception:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
            )

        return response.text
    except Exception as e:
        # Returns the explicit error message so you can debug API issues directly in UI
        return (
            f"⚠️ **Gemini API Error:** `{str(e)}`\n\n"
            f"**Standard Fallback Advice for {city}:** {risk_data.get('advice', 'Take basic precautions.')}"
        )
