import streamlit as st
import pandas as pd
import json
import os
import requests
from datetime import datetime
import time

st.set_page_config(layout="wide", page_title="Ocean Monitoring Dashboard", page_icon="🌊")
st.title("🌊 Explainable Ocean Monitoring System")

BASE = os.path.dirname(__file__)

@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join(BASE, "csv", "output_with_risk.csv"))
    df["TIME"] = pd.to_datetime(df["TIME"])
    return df

df = load_data()

def load_events():
    try:
        # Fetch real-time events from EC2 backend
        response = requests.get("http://3.15.176.0:8000/events", timeout=5)
        data = response.json()
        return data.get("events", [])
    except Exception as e:
        st.error(f"⚠️ Could not connect to backend: {e}")
        try:
            with open(os.path.join(BASE, "events.json"), "r") as f:
                return json.load(f)
        except:
            return []

# Auto-refresh placeholder
placeholder = st.empty()

# Load fresh data
events = load_events()

def risk_label(score: float) -> str:
    if score < 0.4:
        return "Normal"
    elif score < 0.7:
        return "Warning"
    return "Critical"

def risk_color(score: float) -> str:
    if score < 0.4:
        return "green"
    elif score < 0.7:
        return "orange"
    return "red"

col1, col2 = st.columns(2)

with col1:
    st.header("📡 Real-Time Sensor Data")

    # Show connection status
    if len(events) > 0:
        st.success(f"✅ Connected - {len(events)} events received")
    else:
        st.warning("⏳ Waiting for sensor data...")

    # Display latest event prominently
    if len(events) > 0:
        latest = events[-1]  # Most recent event
        device_id = latest.get("device_id", "unknown")
        alert_level = latest.get("alert_level", "unknown")
        value = latest.get("value", 0)
        timestamp = latest.get("server_received_at", "unknown")

        # Calculate risk score for color coding
        if alert_level == "critical":
            score = 0.8
            color = "🔴"
        elif alert_level == "warning":
            score = 0.5
            color = "🟡"
        else:
            score = 0.2
            color = "🟢"

        st.subheader(f"{color} Latest Reading")
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.metric("Device", device_id)
            st.metric("Sensor Value", f"{value:.3f}")
        with col_b:
            st.metric("Alert Level", alert_level.upper())
            st.caption(f"Updated: {timestamp[-8:] if timestamp != 'unknown' else 'N/A'}")

        st.divider()

    # Show recent events (last 5)
    st.subheader("Recent Events")
    if len(events) > 0:
        for event in events[-5:][::-1]:  # Show most recent first
            device_id = event.get("device_id", event.get("device", "unknown"))
            alert_level = event.get("alert_level", event.get("alert", "unknown"))
            timestamp = event.get("server_received_at", event.get("timestamp", "unknown"))
            value = event.get("value", event.get("sensor_value", 0))

            # Color coding for alerts
            if alert_level == "critical":
                score = 0.8
                icon = "🔴"
            elif alert_level == "warning":
                score = 0.5
                icon = "🟡"
            else:
                score = 0.2
                icon = "🟢"

            st.markdown(f"{icon} **{device_id}**: {alert_level.upper()} ({value:.3f}) - {timestamp[-8:] if timestamp != 'unknown' else 'N/A'}")
    else:
        st.info("No events received yet. Check your Arduino connection.")

with col2:
    st.header("Data Intelligence Layer")

    latest = df.iloc[-1]
    score = float(latest["risk_score"])

    st.subheader("Current System State")
    st.metric("Temperature", f"{latest['TEMP']:.2f} °C")
    st.metric("Risk Score", f"{score:.3f}")
    st.metric("Status", risk_label(score))

    st.subheader("Temperature Over Time")
    st.line_chart(df.set_index("TIME")["TEMP"])

    st.subheader("Risk Score Over Time")
    st.line_chart(df.set_index("TIME")["risk_score"])

    st.subheader("Temperature vs Risk Score")
    st.scatter_chart(df, x="TEMP", y="risk_score")
    st.caption("Higher current speeds and pressure correlate with increased flood risk.")

    avg_temp = df["TEMP"].mean()
    high_risk = df[df["risk_score"] >= 0.7].shape[0]

    st.subheader("System Insight")
    st.write(f"""
    - Average temperature: {avg_temp:.2f} °C
    - High-risk readings (score >= 0.7): {high_risk}
    - Risk score computed from current speed, pressure, and temperature
    """)

st.divider()
st.caption("Edge AI + Cloud + Data + Explainability Pipeline")

# Auto-refresh every 2 seconds
time.sleep(2)
st.rerun()
