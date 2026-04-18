from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import List, Optional
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from gemini_client import get_explanation

app = FastAPI(title="Coastal Flood Monitoring API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

events_store: List[dict] = []


class Event(BaseModel):
    device_id: str
    value: float
    alert_level: str  # normal | warning | critical
    timestamp: Optional[str] = None


@app.post("/event")
def post_event(event: Event):
    if event.alert_level not in ("normal", "warning", "critical"):
        raise HTTPException(status_code=422, detail="alert_level must be normal, warning, or critical")
    data = event.model_dump()
    if not data["timestamp"]:
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
    events_store.append(data)
    if len(events_store) > 100:
        events_store.pop(0)
    return {"status": "ok", "stored": len(events_store)}


@app.get("/events")
def get_events(limit: int = 20):
    return {"events": events_store[-limit:]}


@app.get("/explanation")
def get_explanation_endpoint(alert_level: str, risk_score: float):
    if alert_level not in ("normal", "warning", "critical"):
        raise HTTPException(status_code=422, detail="alert_level must be normal, warning, or critical")
    if not 0.0 <= risk_score <= 1.0:
        raise HTTPException(status_code=422, detail="risk_score must be between 0.0 and 1.0")
    explanation = get_explanation(alert_level, risk_score)
    return {"explanation": explanation, "alert_level": alert_level, "risk_score": risk_score}


@app.get("/health")
def health():
    return {"status": "alive", "event_count": len(events_store)}
