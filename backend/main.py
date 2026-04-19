from datetime import datetime, timezone, timedelta
from typing import List, Optional
import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os
import httpx

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
_GEMINI_MODEL = "gemini-2.5-flash"
_gemini_cache: dict = {"summary": None, "fetched_at": 0.0}
_GEMINI_TTL = 300  # 5 minutes


def _call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return ""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{_GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    try:
        resp = httpx.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15,
        )
        data = resp.json()
        if not resp.is_success:
            return f"[Gemini error {resp.status_code}: {data.get('error', {}).get('message', '')[:80]}]"
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"[Gemini unavailable: {str(e)[:60]}]"

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

# ---------------------------------------------------------------------------
# Live NDBC buoy fetch
#   CCE2 (34.302, -120.802) → 46054 West Santa Barbara  (~32 km, same area as CSV)
#   CCE1 (33.437, -122.462) → 46042 Monterey            (same longitude, CA Current)
# ---------------------------------------------------------------------------
NDBC_BUOYS = {
    "CCE2": {"id": "46054", "lat": 34.274, "lon": -120.459, "desc": "West Santa Barbara (near CCE2)"},
    "CCE1": {"id": "46042", "lat": 36.785, "lon": -122.469, "desc": "Monterey (nearest to CCE1 longitude)"},
}
_ndbc_cache: dict = {"data": None, "fetched_at": 0.0}
_NDBC_TTL = 600  # refresh every 10 minutes


def _parse_ndbc_line(line: str) -> dict:
    """Parse one data row from NDBC standard meteorological text."""
    parts = line.split()
    if len(parts) < 15:
        return {}
    def f(v): return None if v == "MM" else float(v)
    return {
        "wdir": f(parts[5]),   # wind direction (deg)
        "wspd": f(parts[6]),   # wind speed (m/s)
        "wvht": f(parts[8]),   # wave height (m)
        "dpd":  f(parts[9]),   # dominant wave period (s)
        "pres": f(parts[12]),  # atmospheric pressure (hPa)
        "atmp": f(parts[13]),  # air temp (°C)
        "wtmp": f(parts[14]),  # sea surface temp (°C)
    }


def fetch_live_ndbc() -> dict:
    """Fetch latest reading from both CCE-adjacent NDBC buoys. Cached 10 min."""
    now = time.time()
    if _ndbc_cache["data"] and (now - _ndbc_cache["fetched_at"]) < _NDBC_TTL:
        return _ndbc_cache["data"]

    result = {}
    for name, buoy in NDBC_BUOYS.items():
        url = f"https://www.ndbc.noaa.gov/data/realtime2/{buoy['id']}.txt"
        try:
            resp = httpx.get(url, timeout=8)
            lines = [l for l in resp.text.splitlines() if not l.startswith("#") and l.strip()]
            if lines:
                latest = _parse_ndbc_line(lines[0])
                latest["buoy_id"] = buoy["id"]
                latest["desc"] = buoy["desc"]
                result[name] = latest
        except Exception:
            result[name] = None

    _ndbc_cache["data"] = result
    _ndbc_cache["fetched_at"] = now
    return result


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
    """
    Two-layer environmental risk:
      1. LIVE — NDBC buoy readings (waves, wind, pressure) for current conditions
      2. HISTORICAL — Scripps CCE mooring CSV (percentile-based multi-factor baseline)
    Risk score = max(live_score, historical_score).
    """
    risk_points = 0
    details = []
    live_detail_parts = []
    avg_cspd, max_cspd, high_pct = 0.0, 0.0, 0.0

    # ------------------------------------------------------------------
    # Layer 1: LIVE NDBC data (current conditions)
    # ------------------------------------------------------------------
    buoys = fetch_live_ndbc()

    for cce_name, reading in buoys.items():
        if not reading:
            continue
        buoy_parts = [f"{cce_name} ({reading['desc']})"]

        # Wave height — WVHT > 2m = elevated, > 3.5m = high
        wvht = reading.get("wvht")
        if wvht is not None:
            buoy_parts.append(f"waves {wvht:.1f}m")
            if wvht > 3.5:
                risk_points += 2
            elif wvht > 2.0:
                risk_points += 1

        # Wind speed — WSPD > 10 m/s (~20 knots) = elevated, > 17 m/s (~33 kts) = high
        wspd = reading.get("wspd")
        if wspd is not None:
            buoy_parts.append(f"wind {wspd:.1f} m/s")
            if wspd > 17:
                risk_points += 2
            elif wspd > 10:
                risk_points += 1

        # Pressure — below 1005 hPa = storm, below 1010 = low
        pres = reading.get("pres")
        if pres is not None:
            buoy_parts.append(f"pressure {pres:.0f} hPa")
            if pres < 1005:
                risk_points += 2
            elif pres < 1010:
                risk_points += 1

        # Sea surface temp for context (no risk points, just reporting)
        wtmp = reading.get("wtmp")
        if wtmp is not None:
            buoy_parts.append(f"SST {wtmp:.1f}°C")

        live_detail_parts.append(", ".join(buoy_parts))

    if live_detail_parts:
        details.append("Live buoys — " + " | ".join(live_detail_parts))

    # ------------------------------------------------------------------
    # Layer 2: HISTORICAL Scripps CSV (baseline context)
    # ------------------------------------------------------------------
    hist_detail_parts = []
    if not df_raw.empty:
        if "CSPD" in df_raw.columns:
            cspd = df_raw["CSPD"].dropna()
            avg_cspd = float(cspd.mean())
            max_cspd = float(cspd.max())
            p95 = float(cspd.quantile(0.95))
            high_pct = float((cspd > cspd.quantile(0.75)).mean() * 100)
            hist_detail_parts.append(f"historical current avg {avg_cspd:.3f} m/s, p95={p95:.3f} m/s")
            if p95 > 0.45:
                risk_points += 1

        if "PRES" in df_raw.columns:
            pres_std = float(df_raw["PRES"].dropna().std())
            hist_detail_parts.append(f"pressure variability std={pres_std:.3f} dbar")
            if pres_std > 1.5:
                risk_points += 1

        if "TEMP" in df_raw.columns:
            temp_range = float(df_raw["TEMP"].dropna().max() - df_raw["TEMP"].dropna().min())
            hist_detail_parts.append(f"temp range {temp_range:.1f}°C over dataset")

        if hist_detail_parts:
            details.append("Scripps CCE2 historical — " + ", ".join(hist_detail_parts))

    if risk_points >= 4:
        label, score = "high", 2
    elif risk_points >= 2:
        label, score = "elevated", 1
    else:
        label, score = "normal", 0

    return {
        "label": label,
        "score": score,
        "avg_cspd": avg_cspd,
        "max_cspd": max_cspd,
        "high_current_pct": high_pct,
        "env_detail": "; ".join(details),
    }


def _adjust_arduino_alert(alert: str, water_depth: float, humidity: float, vibration: float) -> str:
    """
    The Arduino KNN uses vibration ~1.0g as baseline (gravity at rest).
    Training data has critical samples at water_depth≥0.6 with vibration=1.0,
    which causes false critical classifications from sensor noise alone.
    Downgrade to warning unless multiple sensors independently confirm a real event.
    """
    if alert != "critical":
        return alert
    active_vibration = vibration > 1.15   # actual movement above gravity baseline
    high_water = water_depth > 0.65       # clearly above critical threshold
    high_humidity = humidity > 82         # storm-level humidity
    confirmed = sum([active_vibration, high_water, high_humidity])
    if confirmed < 2:
        return "warning"
    return "critical"


@app.get("/summary")
def get_summary(force: bool = Query(False)) -> dict:
    """Get AI-generated summary combining Arduino and CSV environmental data."""
    # --- CSV environmental conclusions ---
    avg_temp = float(df["TEMP"].mean())
    high_risk_count = int((df["risk_score"] >= 0.5).sum())
    env = _compute_env_risk()

    csv_conclusion = (
        f"Scripps ocean data ({env['label']} environmental risk): {env['env_detail']}; "
        f"avg ocean temp {avg_temp:.2f}°C, {high_risk_count} elevated-risk readings historically."
    )

    # --- Arduino conclusions from latest events ---
    dev1 = next((e for e in events_store[::-1] if e.get("device_id") == "water_node"), None)

    d1_temp = float(dev1["temp"]) if dev1 and dev1.get("temp") else 14.0
    d1_water_depth = float(dev1["water_depth"]) if dev1 and dev1.get("water_depth") else 0.0
    d1_humidity = float(dev1["humidity"]) if dev1 and dev1.get("humidity") else 57.0
    d1_vibration = float(dev1["vibration"]) if dev1 and dev1.get("vibration") else 1.0

    raw_alert = dev1["alert_level"] if dev1 else "normal"
    arduino_alert = _adjust_arduino_alert(raw_alert, d1_water_depth, d1_humidity, d1_vibration)
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

    # --- Gemini summary (server-side cached, 5 min TTL) ---
    now = time.time()
    if force or _gemini_cache["summary"] is None or (now - _gemini_cache["fetched_at"]) >= _GEMINI_TTL:
        prompt = (
            f"You are a coastal flood monitoring AI for emergency responders.\n\n"
            f"Arduino edge sensor (on-device KNN): {arduino_conclusion}\n"
            f"Scripps ocean dataset: {csv_conclusion}\n"
            f"Combined alert: {combined_label}\n\n"
            f"Write exactly 2 sentences summarizing current coastal flood risk. "
            f"Reference specific sensor values. State what the Arduino detected AND what the ocean dataset indicates. "
            f"No filler phrases."
        )
        _gemini_cache["summary"] = _call_gemini(prompt)
        _gemini_cache["fetched_at"] = now

    return {
        "csv_conclusion": csv_conclusion,
        "arduino_conclusion": arduino_conclusion,
        "env_risk": env["label"],
        "env_risk_score": env["score"],
        "arduino_alert": arduino_alert,
        "combined_risk": combined_label,
        "gemini_summary": _gemini_cache["summary"] or "",
    }