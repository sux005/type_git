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

# Load CSV data
csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "final_output.csv")
df = pd.read_csv(csv_path)
df["DATE Time"] = pd.to_datetime(df["DATE Time"])


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


@app.get("/summary")
def get_summary() -> dict:
    """Get AI-generated summary combining Arduino and CSV data."""
    # CSV conclusions
    avg_temp = df["TEMP"].mean()
    high_risk = (df["RISK_SCORE"] >= 2).sum()
    
    # Arduino conclusions from latest events
    dev1 = next((e for e in events_store[::-1] if e.get("device_id") == "water_node"), None)
    dev2 = next((e for e in events_store[::-1] if e.get("device_id") == "Device 2"), None)
    
    d1_temp = float(dev1["temp"]) if dev1 and dev1.get("temp") else 14.0
    d1_water_depth = float(dev1["water_depth"]) if dev1 and dev1.get("water_depth") else 0.0
    if d1_water_depth < 0.3:
        d1_depth_str = "Shallow"
    elif d1_water_depth < 0.6:
        d1_depth_str = "Normal"
    else:
        d1_depth_str = "Deep"
    
    d2_velocity_str = str(dev2.get("water velocity", "normal")).lower() if dev2 else "normal"
    
    risk_d1 = predict_device1(d1_temp, d1_depth_str)
    risk_d2 = predict_device2(d2_velocity_str)
    combined_risk = predict_combined(d1_temp, d1_depth_str, d2_velocity_str)
    
    alert_level = map_risk(combined_risk)
    
    # Call Gemini
    overview = get_sensor_overview(
        alert_level=alert_level,
        combined_risk=combined_risk,
        d1_temp=d1_temp,
        d1_depth=d1_depth_str,
        d1_risk=risk_d1,
        d2_velocity=d2_velocity_str,
        d2_risk=risk_d2,
        avg_temp=avg_temp,
        high_risk_count=high_risk,
    )
    
    return {
        "csv_conclusion": f"Historical data shows average temperature of {avg_temp:.2f}°C with {high_risk} high-risk events.",
        "arduino_conclusion": f"Current sensor readings: Device 1 temp {d1_temp}°C at {d1_depth_str} depth (risk: {map_risk(risk_d1)}), Device 2 velocity {d2_velocity_str} (risk: {map_risk(risk_d2)}), combined risk: {map_risk(combined_risk)}.",
        "ai_summary": overview,
    }