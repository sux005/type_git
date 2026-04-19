import streamlit as st
import pandas as pd
import requests
import os

st.set_page_config(layout="wide")
st.title("Explainable Ocean Monitoring System")

BASE = os.path.dirname(__file__)
EC2_URL = "http://3.15.176.0:8000"

@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join(BASE, "csv", "output_with_risk.csv"))
    df["TIME"] = pd.to_datetime(df["TIME"])
    return df

df = load_data()

def load_events():
    try:
        response = requests.get(f"{EC2_URL}/events", timeout=5)
        response.raise_for_status()
        return response.json().get("events", [])
    except Exception:
        return []

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
    st.header("Real-Time System")

    if len(events) == 0:
        st.info("No events yet. Waiting for device input...")
    else:
        for event in events:
            score = float(event.get("risk_score", 0))
            st.markdown(f"### Device: {event['device_id']}")
            st.markdown(f"**Alert:** :{risk_color(score)}[{event['alert_level'].upper()}]")
            st.write(f"Timestamp: {event['timestamp']}")
            st.divider()

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
