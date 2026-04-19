
import marimo

__generated_with = "0.23.1"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import json
    return json, mo, pd


@app.cell
def _(pd):
    df = pd.read_csv("final_output.csv")
    df["DATE Time"] = pd.to_datetime(df["DATE Time"])
    return (df,)


@app.cell
def _(json):
    try:
        with open("events_dummy.json", "r") as f:
            events = json.load(f)
    except:
        events = []
    return (events,)


@app.cell
def _():
    def map_risk(level):
        if level == 0:
            return "Normal"
        elif level == 1:
            return "Warning"
        else:
            return "Critical"

    def color_risk(level):
        if level == 0:
            return "#4caf50"
        elif level == 1:
            return "#ff9800"
        else:
            return "#f44336"

    return color_risk, map_risk


@app.cell
def _(df):
    latest = df.iloc[-1]
    avg_temp = df["TEMP"].mean()
    high_risk = df[df["RISK_SCORE"] >= 2].shape[0]
    return avg_temp, high_risk, latest


@app.cell
def _(mo):
    theme_toggle = mo.ui.switch(value=True)
    return (theme_toggle,)


@app.cell
def _(avg_temp, color_risk, df, events, high_risk, latest, map_risk, mo, theme_toggle):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    is_dark = theme_toggle.value

    # --- Theme colors ---
    bg         = "#1a1a1a" if is_dark else "#f6f8fa"
    surface    = "#2a2a2a" if is_dark else "#ffffff"
    border     = "transparent" if is_dark else "#d0d7de"
    card_border= "none"    if is_dark else "1px solid #d0d7de"
    text_main  = "#e6edf3" if is_dark else "#1f2328"
    text_muted = "#8b949e" if is_dark else "#656d76"
    chart_bg   = "#111111" if is_dark else "#f6f8fa"
    chart_fg   = "#e6edf3" if is_dark else "#1f2328"
    chart_tick = "#8b949e" if is_dark else "#656d76"
    divider    = "#333" if is_dark else "#d0d7de"

    # --- Depth string to meters ---
    depth_map = {
        "Shallow": 5.0,
        "Normal": 20.0,
        "Deep":  50.0,
    }

    # --- Lookup: Device 1 — temp + depth ---
    def predict_device1(temp, depth_str):
        depth_m = depth_map.get(str(depth_str).lower(), 20.0)
        df_clean = df[["TEMP", "DEPTH", "RISK_SCORE"]].dropna()
        dist = ((df_clean["TEMP"] - temp) ** 2 + (df_clean["DEPTH"] - depth_m) ** 2) ** 0.5
        closest = df_clean.iloc[dist.idxmin()]
        return int(closest["RISK_SCORE"])

    # --- Lookup: Device 2 — water velocity ---
    def predict_device2(water_velocity):
        df_clean = df[["WATER VELOCITY", "RISK_SCORE"]].dropna()
        dist = (df_clean["WATER VELOCITY"] - water_velocity).abs()
        closest = df_clean.iloc[dist.idxmin()]
        return int(closest["RISK_SCORE"])

    # --- Combined lookup: temp + depth + water velocity ---
    def predict_combined(temp, depth_str, water_velocity):
        depth_m = depth_map.get(str(depth_str).lower(), 20.0)
        df_clean = df[["TEMP", "DEPTH", "WATER VELOCITY", "RISK_SCORE"]].dropna()
        dist = (
            (df_clean["TEMP"] - temp) ** 2 +
            (df_clean["DEPTH"] - depth_m) ** 2 +
            (df_clean["WATER VELOCITY"] - water_velocity) ** 2
        ) ** 0.5
        closest = df_clean.iloc[dist.idxmin()]
        return int(closest["RISK_SCORE"])

    # --- Pull device data from events ---
    dev1 = next((e for e in events if e["device_id"] == "Device 1"), None)
    dev2 = next((e for e in events if e["device_id"] == "Device 2"), None)

    d1_temp      = float(dev1["temp"])    if dev1 else 14.0
    d1_depth_str = str(dev1["depth"])     if dev1 else "Shallow"
    d1_timestamp = dev1["timestamp"]      if dev1 else "—"

    velocity_map = {
        "low":    -0.15,
        "normal":  0.03,
        "high":    0.25,
    }
    d2_velocity_str = str(dev2["water velocity"]).lower() if dev2 else "normal"
    d2_velocity = velocity_map.get(d2_velocity_str, 0.03)
    d2_timestamp = dev2["timestamp"]      if dev2 else "—"

    # --- Predictions ---
    risk_d1       = predict_device1(d1_temp, d1_depth_str)
    risk_d2       = predict_device2(d2_velocity)
    combined_risk = predict_combined(d1_temp, d1_depth_str, d2_velocity)

    col_d1       = color_risk(risk_d1)
    col_d2       = color_risk(risk_d2)
    col_combined = color_risk(combined_risk)

    buzzer_triggered = combined_risk >= 1

    # --- Charts ---
    plt.style.use("dark_background" if is_dark else "default")

    fig1, ax1 = plt.subplots(figsize=(7, 3))
    ax1.plot(df["DATE Time"], df["TEMP"], color="#4fc3f7", linewidth=0.8)
    ax1.set_title("Temperature Over Time", color=chart_fg, fontsize=11)
    ax1.tick_params(colors=chart_tick, labelsize=7)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax1.set_facecolor(chart_bg)
    fig1.patch.set_facecolor(chart_bg)
    fig1.tight_layout()

    fig2, ax2 = plt.subplots(figsize=(7, 3))
    risk_counts = df["RISK_SCORE"].value_counts().sort_index()
    ax2.bar(risk_counts.index.astype(str), risk_counts.values,
            color=["#4caf50", "#ff9800", "#f44336"][:len(risk_counts)])
    ax2.set_title("Risk Distribution", color=chart_fg, fontsize=11)
    ax2.tick_params(colors=chart_tick, labelsize=8)
    ax2.set_facecolor(chart_bg)
    fig2.patch.set_facecolor(chart_bg)
    fig2.tight_layout()

    fig3, ax3 = plt.subplots(figsize=(7, 3))
    df3 = df[["TEMP", "RISK_SCORE"]].dropna()
    scatter_colors = df3["RISK_SCORE"].map({0: "#4caf50", 1: "#ff9800", 2: "#f44336"}).fillna("#4caf50").tolist()
    ax3.scatter(df3["TEMP"], df3["RISK_SCORE"], c=scatter_colors, alpha=0.5, s=10)
    ax3.set_xlabel("TEMP", color=chart_tick, fontsize=9)
    ax3.set_ylabel("RISK_SCORE", color=chart_tick, fontsize=9)
    ax3.set_title("Temperature vs Risk", color=chart_fg, fontsize=11)
    ax3.tick_params(colors=chart_tick, labelsize=8)
    ax3.set_facecolor(chart_bg)
    fig3.patch.set_facecolor(chart_bg)
    fig3.tight_layout()

    # --- Device 1 card ---
    card_d1 = mo.Html(f"""
        <div style="padding:20px 0 16px 0;border-bottom:1px solid {divider};margin-bottom:8px;">
            <div style="display:flex;align-items:baseline;gap:12px;margin-bottom:12px;">
                <div style="font-size:22px;font-weight:700;color:{text_main};">Device 1</div>
                <div style="font-size:22px;font-weight:700;color:{text_muted};">{d1_depth_str}</div>
            </div>
            <div style="display:flex;gap:10px;margin-bottom:12px;">
                <div style="background:{surface};border:{card_border};border-radius:8px;padding:10px 16px;flex:1;">
                    <div style="color:{text_muted};font-size:11px;margin-bottom:4px;">LIVE TEMP</div>
                    <div style="color:{text_main};font-size:20px;font-weight:700;">{d1_temp} °C</div>
                </div>
                <div style="background:{surface};border:{card_border};border-radius:8px;padding:10px 16px;flex:1;">
                    <div style="color:{text_muted};font-size:11px;margin-bottom:4px;">DEPTH</div>
                    <div style="color:{text_main};font-size:20px;font-weight:700;">{d1_depth_str}</div>
                </div>
            </div>
            <div style="display:inline-block;background:{col_d1}22;border:1.5px solid {col_d1};
                        border-radius:6px;padding:6px 16px;margin-bottom:8px;">
                <span style="color:{col_d1};font-weight:700;font-size:15px;letter-spacing:1px;">
                    ⚡ PREDICTED: {map_risk(risk_d1).upper()}
                </span>
            </div>
            <div style="color:{text_muted};font-size:13px;">🕐 {d1_timestamp}</div>
        </div>
    """)

    # --- Device 2 card ---
    card_d2 = mo.Html(f"""
        <div style="padding:20px 0 16px 0;border-bottom:1px solid {divider};margin-bottom:8px;">
            <div style="display:flex;align-items:baseline;gap:12px;margin-bottom:12px;">
                <div style="font-size:22px;font-weight:700;color:{text_main};">Device 2</div>
                <div style="font-size:22px;font-weight:700;color:{text_muted};">Water Velocity</div>
            </div>
            <div style="display:flex;gap:10px;margin-bottom:12px;">
                <div style="background:{surface};border:{card_border};border-radius:8px;padding:10px 16px;flex:1;">
                    <div style="color:{text_muted};font-size:11px;margin-bottom:4px;">WATER VELOCITY</div>
                    <div style="color:{text_main};font-size:20px;font-weight:700;">{dev2["water velocity"] if dev2 else "—"}</div>
                </div>
            </div>
            <div style="display:inline-block;background:{col_d2}22;border:1.5px solid {col_d2};
                        border-radius:6px;padding:6px 16px;margin-bottom:8px;">
                <span style="color:{col_d2};font-weight:700;font-size:15px;letter-spacing:1px;">
                    ⚡ PREDICTED: {map_risk(risk_d2).upper()}
                </span>
            </div>
            <div style="color:{text_muted};font-size:13px;">🕐 {d2_timestamp}</div>
        </div>
    """)

    # --- Device 3 card (buzzer) ---
    if buzzer_triggered:
        d3_col   = col_combined
        d3_icon  = "🔔"
        d3_label = f"ALERT SENT — {map_risk(combined_risk).upper()}"
    else:
        d3_col   = "#4caf50"
        d3_icon  = "✅"
        d3_label = "STATUS NORMAL"

    card_d3 = mo.Html(f"""
        <div style="padding:20px 0 16px 0;margin-bottom:8px;">
            <div style="display:flex;align-items:baseline;gap:12px;margin-bottom:12px;">
                <div style="font-size:22px;font-weight:700;color:{text_main};">Device 3</div>
                <div style="font-size:22px;font-weight:700;color:{text_muted};">Buzzer</div>
            </div>
            <div style="display:inline-block;background:{d3_col}22;border:1.5px solid {d3_col};
                        border-radius:6px;padding:10px 20px;">
                <span style="color:{d3_col};font-weight:700;font-size:16px;letter-spacing:1px;">
                    {d3_icon} {d3_label}
                </span>
            </div>
        </div>
    """)

    left_col = mo.vstack([
        mo.Html(f"<h1 style='font-size:26px;font-weight:700;color:{text_main};margin-bottom:16px;'>📡 Real-Time Updates</h1>"),
        card_d1,
        card_d2,
        card_d3,
    ])

    # --- Right col: combined system state ---
    risk_col = col_combined

    metrics_html = mo.Html(f"""
        <div style="display:flex;gap:16px;margin-bottom:8px;">
            <div style="background:{surface};border:{card_border};border-radius:10px;padding:20px 24px;flex:1;">
                <div style="color:{text_muted};font-size:13px;margin-bottom:6px;">Predicted Risk Score</div>
                <div style="font-size:32px;font-weight:700;color:{text_main};">{combined_risk}</div>
            </div>
            <div style="background:{surface};border:{card_border};border-radius:10px;padding:20px 24px;flex:1;">
                <div style="color:{text_muted};font-size:13px;margin-bottom:6px;">Status</div>
                <div style="font-size:32px;font-weight:700;color:{col_combined};">{map_risk(combined_risk)}</div>
            </div>
        </div>
    """)

    insight_html = mo.Html(f"""
        <div style="background:{surface};border:{card_border};border-radius:10px;
                    padding:20px 24px;font-size:15px;line-height:2;color:{text_muted};">
            • Average temperature: <strong style="color:{text_main};">{avg_temp:.2f} °C</strong><br>
            • High-risk events detected: <strong style="color:#f44336;">{high_risk}</strong><br>
            • Risk increases as temperature deviates from baseline
        </div>
    """)

    right_col = mo.vstack([
        mo.Html(f"<h1 style='font-size:26px;font-weight:700;color:{text_main};margin-bottom:16px;'>📊 Prediction and Data Layer</h1>"),
        mo.Html(f"<h2 style='font-size:20px;color:{text_main};margin:8px 0 10px;'>Current System State</h2>"),
        metrics_html,
        mo.Html(f"<h2 style='font-size:20px;color:{text_main};margin:24px 0 10px;'>Temperature Over Time</h2>"),
        mo.ui.matplotlib(ax1),
        mo.Html(f"<h2 style='font-size:20px;color:{text_main};margin:24px 0 10px;'>Risk Distribution</h2>"),
        mo.ui.matplotlib(ax2),
        mo.Html(f"<h2 style='font-size:20px;color:{text_main};margin:24px 0 10px;'>Temperature vs Risk</h2>"),
        mo.ui.matplotlib(ax3),
        mo.Html(f"<p style='color:{text_muted};font-size:13px;margin-top:6px;'>Higher temperatures correlate with increased risk levels.</p>"),
        mo.Html(f"<h2 style='font-size:20px;color:{text_main};margin:24px 0 10px;'>System Insight</h2>"),
        insight_html,
    ])

    # --- Final layout ---
    mo.vstack([
        mo.Html(f"""
            <style>
                :root {{ color-scheme: {"dark" if is_dark else "light"}; }}
                body {{
                    background-color: {bg} !important;
                    color: {text_main} !important;
                }}
                .marimo, [class*="marimo"], main, #root, #app {{
                    background-color: {bg} !important;
                }}
                p, span, div, h1, h2, h3, h4 {{ color: inherit; }}
            </style>
            <div style="background:{bg};margin:-16px -24px 0 -24px;padding:24px 24px 0 24px;">
                <h1 style="font-size:36px;font-weight:800;color:{text_main};margin:0 0 16px 0;">
                    🌊 Flood Monitoring System
                </h1>
            </div>
        """),
        theme_toggle,
        mo.Html(f"<hr style='border:none;border-top:1px solid {divider};margin:12px 0;'>"),
        mo.hstack([left_col, right_col], widths=[1, 2]),
        mo.Html(f"""
            <div style="padding:16px 0;">
                <hr style='border:none;border-top:1px solid {divider};'>
                <p style='color:{text_muted};font-size:12px;text-align:center;margin-top:8px;'>
                    Edge AI + Cloud + Data + Explainability Pipeline
                </p>
            </div>
        """)
    ])
    return


if __name__ == "__main__":
    app.run()