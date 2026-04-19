from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from gemini_client import get_explanation

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


class Event(BaseModel):
    device_id: str
    value: float
    alert_level: str  # "normal", "warning", or "critical"
    timestamp: Optional[str] = None
    device_name: Optional[str] = None
    host_timestamp: Optional[str] = None


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
        "value": event.value,
        "alert_level": event.alert_level,
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


@app.get("/explanation")
def explanation(alert_level: str = "normal", risk_score: float = 0.0) -> dict:
    text = get_explanation(alert_level.lower(), risk_score)
    return {"explanation": text, "alert_level": alert_level, "risk_score": risk_score}


@app.get("/events/latest")
def latest_event() -> dict:
    """Get the most recent event."""
    if not events_store:
        return {"total_events": 0, "event": None}

    return {
        "total_events": len(events_store),
        "event": events_store[-1],
    }