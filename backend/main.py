from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os
from .gemini_client import get_sensor_overview

app = FastAPI(title="Coastal Flood Monitoring API")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory event store
events_store: List[dict] = []

# Load processed CSV (has risk_score column)
csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "final_output.csv")
df = pd.read_csv(csv_path)
df["DateTime"] = pd.to_datetime(df["DateTime"])

# Load raw Scripps CSV for richer environmental signals (CSPD, PRES, currents)
raw_csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "output.csv")
df_raw = pd.read_csv(raw_csv_path) if os.path.exists(raw_csv_path) else pd.DataFrame()


class Event(BaseModel):
    device_id: str
    alert_level: str
    value: Optional[float] = None
    water_depth: Optional[float] = None
    humidity: Optional[float] = None
    temp: Optional[float] = None
    distance: Optional[float] = None
    vibration: Optional[float] = None
    timestamp: Optional[str] = None
    device_name: Optional[str] = None
    host_timestamp: Optional[str] = None


# Prediction functions
def predict_device1(temp, depth_str):
    depth_map = {"Shallow": 5.0, "Normal": 20.0, "Deep": 50.0}
    depth = depth_map.get(depth_str, 20.0)
    if temp > 25 or depth > 30:
        return 2  # critical
    elif temp > 20 or depth > 15:
        return 1  # warning
    return 0  # normal

def predict_device2(water_velocity):
    velocity_map = {"low": -0.15, "normal": 0.03, "high": 0.25}
    vel = velocity_map.get(water_velocity.lower(), 0.03)
    if abs(vel) > 0.2:
        return 2
    elif abs(vel) > 0.1:
        return 1
    return 0

def predict_combined(temp, depth_str, water_velocity):
    d1 = predict_device1(temp, depth_str)
    d2 = predict_device2(water_velocity)
    return max(d1, d2)

def map_risk(level):
    return {0: "normal", 1: "warning", 2: "critical"}.get(level, "normal")


@app.get("/")
def root() -> dict:
    return {"message": "Coastal Flood Monitoring API is running"}


@app.post("/event", status_code=201)
def create_event(event: Event) -> dict:
    """Accept sensor event and store it."""
    # Validate alert level
    if event.alert_level not in ("normal", "warning", "critical"):
        raise HTTPException(
            status_code=422,
            detail="alert_level must be one of: normal, warning, critical"
        )
    
    # Record the event
    record = {
        "device_id": event.device_id,
        "device_name": event.device_name,
        "alert_level": event.alert_level,
        "value": event.value,
        "water_depth": event.water_depth,
        "humidity": event.humidity,
        "temp": event.temp,
        "distance": event.distance,
        "vibration": event.vibration,
        "timestamp": event.timestamp,
        "host_timestamp": event.host_timestamp,
        "server_received_at": datetime.now(timezone.utc).isoformat(),
    }
    
    events_store.append(record)
    
    # Keep only the last 1000 events
    if len(events_store) > 1000:
        events_store.pop(0)
    
    return {
        "status": "accepted",
        "event_index": len(events_store) - 1,
        "total_events": len(events_store),
    }


@app.get("/events")
def list_events(limit: int = 50) -> dict:
    """Retrieve recent events."""
    safe_limit = max(1, min(limit, 500))
    return {
        "total_events": len(events_store),
        "returned": min(safe_limit, len(events_store)),
        "events": events_store[-safe_limit:],
    }


@app.get("/events/latest")
def latest_event() -> dict:
    """Get the most recent event."""
    if not events_store:
        return {"total_events": 0, "event": None}

    return {
        "total_events": len(events_store),
        "event": events_store[-1],
    }


def _compute_env_risk() -> dict:
    """Derive environmental risk label and stats from the raw Scripps CSV."""
    if df_raw.empty:
        return {"label": "normal", "score": 0, "avg_cspd": 0.0, "max_cspd": 0.0, "avg_pres": None}

    avg_cspd = float(df_raw["CSPD"].mean()) if "CSPD" in df_raw.columns else 0.0
    max_cspd = float(df_raw["CSPD"].max()) if "CSPD" in df_raw.columns else 0.0
    avg_pres = float(df_raw["PRES"].mean()) if "PRES" in df_raw.columns else None

    # High current speed (CSPD m/s) and pressure spikes indicate storm/flood conditions
    if max_cspd > 0.5 or avg_cspd > 0.35:
        label, score = "high", 2
    elif max_cspd > 0.3 or avg_cspd > 0.2:
        label, score = "elevated", 1
    else:
        label, score = "normal", 0

    return {"label": label, "score": score, "avg_cspd": avg_cspd, "max_cspd": max_cspd, "avg_pres": avg_pres}


@app.get("/summary")
def get_summary() -> dict:
    """Get AI-generated summary combining Arduino and CSV environmental data."""
    # --- CSV environmental conclusions ---
    avg_temp = float(df["TEMP"].mean())
    high_risk_count = int((df["risk_score"] >= 0.5).sum())
    env = _compute_env_risk()

    csv_conclusion = (
        f"Scripps ocean data: avg temp {avg_temp:.2f}°C, "
        f"avg current speed {env['avg_cspd']:.3f} m/s (peak {env['max_cspd']:.3f} m/s), "
        f"environmental risk: {env['label']} ({high_risk_count} elevated-risk readings)."
    )

    # --- Arduino conclusions from latest events ---
    dev1 = next((e for e in events_store[::-1] if e.get("device_id") == "water_node"), None)

    d1_temp = float(dev1["temp"]) if dev1 and dev1.get("temp") else 14.0
    d1_water_depth = float(dev1["water_depth"]) if dev1 and dev1.get("water_depth") else 0.0
    d1_humidity = float(dev1["humidity"]) if dev1 and dev1.get("humidity") else 57.0
    d1_vibration = float(dev1["vibration"]) if dev1 and dev1.get("vibration") else 1.0

    if d1_water_depth < 0.3:
        d1_depth_str = "Shallow"
    elif d1_water_depth < 0.6:
        d1_depth_str = "Normal"
    else:
        d1_depth_str = "Deep"

    arduino_alert = dev1["alert_level"] if dev1 else "normal"
    alert_map = {"normal": 0, "warning": 1, "critical": 2}
    arduino_risk_int = alert_map.get(arduino_alert, 0)

    arduino_conclusion = (
        f"Arduino KNN (on-device): alert={arduino_alert}, "
        f"water_depth={d1_water_depth:.3f}, humidity={d1_humidity:.1f}%, "
        f"temp={d1_temp:.1f}°C, vibration={d1_vibration:.3f}g."
    )

    # Combined risk: take the higher of the two signals
    combined_risk = max(arduino_risk_int, env["score"])
    combined_label = map_risk(combined_risk)

    # --- Call Gemini ---
    overview = get_sensor_overview(
        alert_level=combined_label,
        combined_risk=combined_risk,
        d1_temp=d1_temp,
        d1_depth=d1_depth_str,
        d1_risk=arduino_risk_int,
        arduino_alert=arduino_alert,
        d1_humidity=d1_humidity,
        d1_vibration=d1_vibration,
        avg_temp=avg_temp,
        high_risk_count=high_risk_count,
        env_risk_label=env["label"],
        avg_cspd=env["avg_cspd"],
        max_cspd=env["max_cspd"],
    )

    return {
        "csv_conclusion": csv_conclusion,
        "arduino_conclusion": arduino_conclusion,
        "env_risk": env["label"],
        "env_risk_score": env["score"],
        "arduino_alert": arduino_alert,
        "combined_risk": combined_label,
        "ai_summary": overview,
    }