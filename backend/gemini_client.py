from google import genai
import os

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def get_explanation(alert_level: str, risk_score: float) -> str:
    prompt = f"""You are a coastal flood monitoring system assistant.
Current sensor alert level: {alert_level}
Environmental risk score (0.0–1.0): {risk_score:.2f}

Generate a concise 1–2 sentence explanation of current coastal conditions and flood risk for emergency responders.
Be specific about what the data means. Do not use filler phrases."""
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt,
    )
    return response.text.strip()
