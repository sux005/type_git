from google import genai
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

_api_key = os.environ.get("GEMINI_API_KEY")
if not _api_key:
    raise SystemExit("ERROR: GEMINI_API_KEY environment variable is not set")
client = genai.Client(api_key=_api_key)


def _fallback_explanation(alert_level: str, risk_score: float) -> str:
    if alert_level == "critical" or risk_score >= 0.7:
        return (f"Water levels and environmental sensors indicate a critical flood risk "
                f"(score: {risk_score:.2f}). Immediate action recommended — coastal areas "
                f"may experience flooding within hours.")
    elif alert_level == "warning" or risk_score >= 0.4:
        return (f"Sensor readings show elevated coastal risk (score: {risk_score:.2f}). "
                f"Conditions are worsening — monitor closely and prepare for possible flooding.")
    return (f"Coastal conditions are currently stable (score: {risk_score:.2f}). "
            f"No immediate flood risk detected based on current sensor data.")


def get_explanation(alert_level: str, risk_score: float) -> str:
    if not _api_key:
        return _fallback_explanation(alert_level, risk_score)
    prompt = f"""You are a coastal flood monitoring system assistant.
Current sensor alert level: {alert_level}
Environmental risk score (0.0–1.0): {risk_score:.2f}

Generate a concise 1–2 sentence explanation of current coastal conditions and flood risk for emergency responders.
Be specific about what the data means. Do not use filler phrases."""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception:
        return _fallback_explanation(alert_level, risk_score)
