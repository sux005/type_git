import streamlit as st
import pandas as pd
import json

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(layout="wide")
st.title("🌊 Explainable Ocean Monitoring System")

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("final_output.csv")
    df["DateTime"] = pd.to_datetime(df["DateTime"])
    return df

df = load_data()

# -----------------------------
# LOAD EVENTS (LOCAL PIPELINE)
# -----------------------------
def load_events():
    try:
        with open("events.json", "r") as f:
            return json.load(f)
    except:
        return []

events = load_events()

# -----------------------------
# HELPERS
# -----------------------------
def map_risk(level):
    if level == 0:
        return "Normal"
    elif level == 1:
        return "Warning"
    else:
        return "Critical"

def color_risk(level):
    if level == 0:
        return "Green"
    elif level == 1:
        return "Orange"
    else:
        return "Red"

def normalize_alert(level_str):
    if level_str == "Normal":
        return 0
    elif level_str == "Warning":
        return 1
    else:
        return 2

# -----------------------------
# LAYOUT
# -----------------------------
col1, col2 = st.columns(2)

# =============================
# LEFT: REAL-TIME SYSTEM
# =============================
with col1:
    st.header("📡 Real-Time System")

    if len(events) == 0:
        st.info("No events yet. Waiting for device input...")
    else:
        for event in events:
            lvl_num = normalize_alert(event["alert_level"])

            st.markdown(f"### Device: {event['device_id']}")
            st.markdown(
                f"**Alert:** :{color_risk(lvl_num)}[{event['alert_level'].upper()}]"
            )
            st.write(f"Timestamp: {event['timestamp']}")
            st.divider()

# =============================
# RIGHT: DATA INTELLIGENCE
# =============================
with col2:
    st.header("📊 Data Intelligence Layer")

    latest = df.iloc[-1]

    # --- CURRENT STATE ---
    st.subheader("Current System State")
    st.metric("Temperature", f"{latest['TEMP']} °C")
    st.metric("Risk Score", int(latest["risk_score"]))
    st.metric("Status", map_risk(int(latest["risk_score"])))

    # --- TREND ---
    st.subheader("Temperature Over Time")
    st.line_chart(df.set_index("DateTime")["TEMP"])

    # --- DISTRIBUTION ---
    st.subheader("Risk Distribution")
    st.bar_chart(df["risk_score"].value_counts().sort_index())

    # --- RELATIONSHIP (KEY VISUAL) ---
    st.subheader("🔗 Relationship: Temperature vs Risk")
    st.scatter_chart(df, x="TEMP", y="risk_score")
    st.caption("Higher temperatures correlate with increased risk levels.")

    # --- INSIGHT ---
    st.subheader("System Insight")

    avg_temp = df["TEMP"].mean()
    high_risk = df[df["risk_score"] >= 2].shape[0]

    st.write(f"""
    - Average temperature: {avg_temp:.2f} °C  
    - High-risk events detected: {high_risk}  
    - Risk increases as temperature deviates from baseline  
    """)

# -----------------------------
# FOOTER (OPTIONAL BUT NICE)
# -----------------------------
st.divider()
st.caption("Edge AI + Cloud + Data + Explainability Pipeline")