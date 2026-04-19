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
        return ("Water levels and environmental sensors indicate a critical flood risk. "
                "Immediate action recommended — coastal areas may experience flooding within hours.")
    elif alert_level == "warning" or risk_score >= 0.4:
        return ("Sensor readings show elevated coastal risk. "
                "Conditions are worsening — monitor closely and prepare for possible flooding.")
    return ("Coastal conditions are currently stable. "
            "No immediate flood risk detected based on current sensor data.")


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


def get_sensor_overview(
    alert_level: str,
    combined_risk: int,
    d1_temp: float,
    d1_depth: str,
    d1_risk: int,
    arduino_alert: str,
    d1_humidity: float,
    d1_vibration: float,
    avg_temp: float,
    high_risk_count: int,
    env_risk_label: str = "normal",
    avg_cspd: float = 0.0,
    max_cspd: float = 0.0,
    # legacy params kept for compatibility
    d2_velocity: str = "normal",
    d2_risk: int = 0,
) -> str:
    risk_label = {0: "Normal", 1: "Warning", 2: "Critical"}
    if not _api_key:
        return _fallback_explanation(alert_level, combined_risk / 2.0)
    prompt = f"""You are a coastal flood monitoring AI for emergency responders.

Arduino edge sensor (on-device KNN classifier):
- Alert level: {arduino_alert}
- Water depth: {d1_depth} | Temp: {d1_temp:.1f}°C | Humidity: {d1_humidity:.1f}% | Vibration: {d1_vibration:.3f}g
- On-device risk: {risk_label.get(d1_risk, d1_risk)}

Live ocean conditions (NDBC buoys near CCE1 & CCE2 moorings):
- Average current speed: {avg_cspd:.3f} m/s (peak: {max_cspd:.3f} m/s)
- Environmental risk: {env_risk_label}

Historical context (Scripps CCE2 mooring dataset):
- Historical avg ocean temp: {avg_temp:.2f}°C | Elevated-risk readings: {high_risk_count}

Combined system alert: {risk_label.get(combined_risk, combined_risk)}

Write exactly 2 sentences summarizing current coastal flood risk for emergency responders.
Sentence 1: what the Arduino edge sensor detected right now.
Sentence 2: what live buoy conditions and historical ocean data indicate about broader risk.
Use specific values. No filler phrases."""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception:
        return _fallback_explanation(alert_level, combined_risk / 2.0)
