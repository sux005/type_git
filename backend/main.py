from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from gemini_client import get_explanation

app = FastAPI(title="Edge Event API")

# In-memory event store for hackathon/demo use.
# Fine for a demo; replace with a database later if needed.
EVENTS: list[dict] = []


class Features(BaseModel):
    current_water: int = Field(..., ge=0)
    delta_water: int


class DeviceEvent(BaseModel):
    device_id: int
    timestamp_ms: int = Field(..., ge=0)
    alert_level: Literal["NORMAL", "WARNING", "CRITICAL"]
    features: Features
    device_name: Optional[str] = None
    host_timestamp: Optional[str] = None


@app.get("/")
def root() -> dict:
    return {"message": "Edge Event API is running"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/event", status_code=201)
def create_event(event: DeviceEvent, request: Request) -> dict:
    record = {
        "device_id": event.device_id,
        "device_name": event.device_name,
        "timestamp_ms": event.timestamp_ms,
        "host_timestamp": event.host_timestamp,
        "server_received_at": datetime.now(timezone.utc).isoformat(),
        "alert_level": event.alert_level,
        "features": event.features.model_dump(),
        "source_ip": request.client.host if request.client else None,
    }

    EVENTS.append(record)

    return {
        "status": "accepted",
        "event_index": len(EVENTS) - 1,
        "event": record,
    }


@app.get("/events")
def list_events(limit: int = 50) -> dict:
    safe_limit = max(1, min(limit, 500))
    return {
        "count": len(EVENTS),
        "events": EVENTS[-safe_limit:],
    }


@app.get("/explanation")
def explanation(alert_level: str = "normal", risk_score: float = 0.0) -> dict:
    text = get_explanation(alert_level.lower(), risk_score)
    return {"explanation": text, "alert_level": alert_level, "risk_score": risk_score}


@app.get("/events/latest")
def latest_event() -> dict:
    if not EVENTS:
        return {"count": 0, "event": None}

    return {
        "count": len(EVENTS),
        "event": EVENTS[-1],
    }