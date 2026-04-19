import marimo

__generated_with = "0.23.1"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import requests
    return mo, pd, requests


@app.cell
def _(pd):
    df = pd.read_csv("data/final_output.csv")
    df["DateTime"] = pd.to_datetime(df["DateTime"])
    return (df,)


@app.cell
def _(requests):
    def _alert_to_risk(alert_level: str) -> int:
        level = str(alert_level).upper()
        if level == "CRITICAL":
            return 2
        elif level == "WARNING":
            return 1
        return 0

    def _translate(raw: dict):
        device_id = raw.get("device_id")
        alert = raw.get("alert_level", "NORMAL")
        risk = _alert_to_risk(alert)
        features = raw.get("features") or {}
        current_water = features.get("current_water", 0)
        timestamp = raw.get("server_received_at", "—")
        if device_id == 1:
            depth_map = {0: "Shallow", 1: "Normal", 2: "Deep"}
            return {"device_id": "Device 1", "temp": round(current_water / 1023 * 30, 1),
                    "depth": depth_map.get(risk, "Shallow"), "timestamp": timestamp}
        elif device_id == 2:
            velocity_map = {0: "low", 1: "normal", 2: "high"}
            return {"device_id": "Device 2", "water velocity": velocity_map.get(risk, "normal"),
                    "timestamp": timestamp}
        return None

    try:
        resp = requests.get("http://3.15.176.0:8000/events", timeout=5)
        resp.raise_for_status()
        events = [e for raw in resp.json().get("events", []) if (e := _translate(raw)) is not None]
    except Exception:
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
    high_risk = df[df["risk_score"] >= 2].shape[0]
    return avg_temp, high_risk


@app.cell
def _(mo):
    theme_toggle = mo.ui.switch(value=True)
    return (theme_toggle,)


@app.cell
def _(avg_temp, color_risk, df, events, high_risk, map_risk, mo, theme_toggle):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import sys, os
    _backend = os.path.join(os.getcwd(), "backend")
    if _backend not in sys.path:
        sys.path.insert(0, _backend)
    try:
        import importlib, gemini_client as _gc
        importlib.reload(_gc)
        _get_sensor_overview = _gc.get_sensor_overview
    except Exception:
        _get_sensor_overview = None

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
        df_clean = df[["TEMP", "DEPTH", "risk_score"]].dropna()
        dist = ((df_clean["TEMP"] - temp) ** 2 + (df_clean["DEPTH"] - depth_m) ** 2) ** 0.5
        closest = df_clean.iloc[dist.idxmin()]
        return 2 if closest["risk_score"] >= 0.7 else (1 if closest["risk_score"] >= 0.4 else 0)

    # --- Lookup: Device 2 — temp proxy ---
    def predict_device2(water_velocity):
        velocity_to_temp = {"low": -0.15, "normal": 0.03, "high": 0.25}
        temp_proxy = 14.0 + velocity_to_temp.get(water_velocity, 0.03) * 50
        df_clean = df[["TEMP", "risk_score"]].dropna()
        dist = (df_clean["TEMP"] - temp_proxy).abs()
        closest = df_clean.iloc[dist.idxmin()]
        return 2 if closest["risk_score"] >= 0.7 else (1 if closest["risk_score"] >= 0.4 else 0)

    # --- Combined lookup: temp + depth ---
    def predict_combined(temp, depth_str, water_velocity):
        depth_m = depth_map.get(str(depth_str).lower(), 20.0)
        df_clean = df[["TEMP", "DEPTH", "risk_score"]].dropna()
        dist = ((df_clean["TEMP"] - temp) ** 2 + (df_clean["DEPTH"] - depth_m) ** 2) ** 0.5
        closest = df_clean.iloc[dist.idxmin()]
        return 2 if closest["risk_score"] >= 0.7 else (1 if closest["risk_score"] >= 0.4 else 0)

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

    # --- Gemini overview ---
    _alert_map   = {0: "normal", 1: "warning", 2: "critical"}
    _alert_level = _alert_map.get(combined_risk, "normal")
    if _get_sensor_overview:
        try:
            _overview_text = _get_sensor_overview(
                alert_level=_alert_level,
                combined_risk=combined_risk,
                d1_temp=d1_temp,
                d1_depth=d1_depth_str,
                d1_risk=risk_d1,
                d2_velocity=d2_velocity_str,
                d2_risk=risk_d2,
                avg_temp=avg_temp,
                high_risk_count=high_risk,
            )
        except Exception as e:
            _overview_text = f"AI overview unavailable: {e}"
    else:
        _overview_text = "AI overview unavailable (gemini_client not loaded)."

    col_d1       = color_risk(risk_d1)
    col_d2       = color_risk(risk_d2)
    col_combined = color_risk(combined_risk)

    def risk_emoji(level):
        return {0: "☀️", 1: "🌦️", 2: "⚡"}.get(level, "☀️")

    buzzer_triggered = combined_risk >= 1

    # --- Charts ---
    plt.style.use("dark_background" if is_dark else "default")

    fig1, ax1 = plt.subplots(figsize=(7, 3))
    ax1.plot(df["DateTime"], df["TEMP"], color="#4fc3f7", linewidth=0.8)
    ax1.set_title("Temperature Over Time", color=chart_fg, fontsize=11)
    ax1.tick_params(colors=chart_tick, labelsize=7)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax1.set_facecolor(chart_bg)
    fig1.patch.set_facecolor(chart_bg)
    fig1.tight_layout()

    fig2, ax2 = plt.subplots(figsize=(7, 3))
    risk_bins = pd.cut(df["risk_score"], bins=[0, 0.4, 0.7, 1.0], labels=["Normal", "Warning", "Critical"], include_lowest=True)
    risk_counts = risk_bins.value_counts().reindex(["Normal", "Warning", "Critical"])
    ax2.bar(risk_counts.index, risk_counts.values, color=["#4caf50", "#ff9800", "#f44336"])
    ax2.set_title("Risk Distribution", color=chart_fg, fontsize=11)
    ax2.tick_params(colors=chart_tick, labelsize=8)
    ax2.set_facecolor(chart_bg)
    fig2.patch.set_facecolor(chart_bg)
    fig2.tight_layout()

    fig3, ax3 = plt.subplots(figsize=(7, 3))
    df3 = df[["TEMP", "risk_score"]].dropna()
    scatter_colors = df3["risk_score"].apply(lambda s: "#f44336" if s >= 0.7 else ("#ff9800" if s >= 0.4 else "#4caf50")).tolist()
    ax3.scatter(df3["TEMP"], df3["risk_score"], c=scatter_colors, alpha=0.5, s=10)
    ax3.set_xlabel("TEMP", color=chart_tick, fontsize=9)
    ax3.set_ylabel("risk_score", color=chart_tick, fontsize=9)
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
                    {risk_emoji(risk_d1)} PREDICTED: {map_risk(risk_d1).upper()}
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
                    {risk_emoji(risk_d2)} PREDICTED: {map_risk(risk_d2).upper()}
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

    gemini_html = mo.Html(f"""
    <div style="background:{surface};border:{card_border};border-radius:10px;
                padding:20px 24px;min-height:120px;">
        <div style="color:{text_main};font-size:20px;line-height:1.7;">{_overview_text}</div>
    </div>
    """)

    right_col = mo.vstack([
        mo.Html(f"<h1 style='font-size:26px;font-weight:700;color:{text_main};margin-bottom:16px;'>📊 Prediction and Data Layer</h1>"),
        mo.Html(f"<h2 style='font-size:20px;color:{text_main};margin:8px 0 10px;'>Current System State</h2>"),
        metrics_html,
        mo.Html(f"<h2 style='font-size:20px;color:{text_main};margin:24px 0 10px;'>Overview</h2>"),
        gemini_html,
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

    # --- Ocean background colors per theme ---
    if is_dark:
        ocean_grad  = "linear-gradient(to bottom,#0f172a,#0c1a2e,#0f2744)"
        w1, w2, w3  = "#1e3a8a", "#0c4a6e", "#075985"
        title_color = "rgba(186,230,253,0.9)"
        sub_color   = "rgba(125,211,252,0.65)"
    else:
        ocean_grad  = "linear-gradient(to bottom,#eff6ff,#ecfeff,#dbeafe)"
        w1, w2, w3  = "#3b82f6", "#06b6d4", "#0ea5e9"
        title_color = "rgba(30,58,138,0.85)"
        sub_color   = "rgba(29,78,216,0.65)"

    # --- Final layout ---
    mo.vstack([
        mo.Html(f"""
            <style>
                :root {{ color-scheme: {"dark" if is_dark else "light"}; }}
                html, body,
                .marimo, [class*="marimo"], main, #root, #app {{
                    background: transparent !important;
                    color: {text_main} !important;
                }}
                p, span, div, h1, h2, h3, h4 {{ color: inherit; }}
                @keyframes bubble-float {{
                    0%,100% {{ transform:translateY(0) translateX(0); opacity:0.25; }}
                    25%      {{ transform:translateY(-30px) translateX(10px); opacity:0.5; }}
                    50%      {{ transform:translateY(-55px) translateX(-8px); opacity:0.3; }}
                    75%      {{ transform:translateY(-25px) translateX(5px); opacity:0.4; }}
                }}
            </style>
            <script>
            (function() {{
                // remove stale bg on theme toggle
                var old = document.getElementById('ocean-bg');
                if (old) old.remove();

                var bg = document.createElement('div');
                bg.id = 'ocean-bg';
                bg.style.cssText = [
                    'position:fixed','inset:0','z-index:0',
                    'overflow:hidden','pointer-events:none',
                    'background:{ocean_grad}'
                ].join(';');

                bg.innerHTML = `
                  <div style="position:absolute;inset:0;opacity:0.3;">
                    <svg style="position:absolute;width:100%;height:100%;"
                         xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320" preserveAspectRatio="none">
                      <path fill="{w1}" fill-opacity="0.4"
                            d="M0,96L48,112C96,128,192,160,288,160C384,160,480,128,576,122.7C672,117,768,139,864,138.7C960,139,1056,117,1152,101.3C1248,85,1344,75,1392,69.3L1440,64L1440,320L0,320Z">
                        <animate attributeName="d" dur="10s" repeatCount="indefinite" values="
                          M0,96L48,112C96,128,192,160,288,160C384,160,480,128,576,122.7C672,117,768,139,864,138.7C960,139,1056,117,1152,101.3C1248,85,1344,75,1392,69.3L1440,64L1440,320L0,320Z;
                          M0,128L48,138.7C96,149,192,171,288,165.3C384,160,480,128,576,128C672,128,768,160,864,165.3C960,171,1056,149,1152,133.3C1248,117,1344,107,1392,101.3L1440,96L1440,320L0,320Z;
                          M0,96L48,112C96,128,192,160,288,160C384,160,480,128,576,122.7C672,117,768,139,864,138.7C960,139,1056,117,1152,101.3C1248,85,1344,75,1392,69.3L1440,64L1440,320L0,320Z"/>
                      </path>
                    </svg>
                  </div>
                  <div style="position:absolute;inset:0;opacity:0.2;">
                    <svg style="position:absolute;width:100%;height:100%;transform:translateY(20%);"
                         xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320" preserveAspectRatio="none">
                      <path fill="{w2}" fill-opacity="0.4"
                            d="M0,192L48,197.3C96,203,192,213,288,192C384,171,480,117,576,112C672,107,768,149,864,165.3C960,181,1056,171,1152,154.7C1248,139,1344,117,1392,106.7L1440,96L1440,320L0,320Z">
                        <animate attributeName="d" dur="15s" repeatCount="indefinite" values="
                          M0,192L48,197.3C96,203,192,213,288,192C384,171,480,117,576,112C672,107,768,149,864,165.3C960,181,1056,171,1152,154.7C1248,139,1344,117,1392,106.7L1440,96L1440,320L0,320Z;
                          M0,160L48,170.7C96,181,192,203,288,197.3C384,192,480,160,576,138.7C672,117,768,107,864,122.7C960,139,1056,181,1152,186.7C1248,192,1344,160,1392,144L1440,128L1440,320L0,320Z;
                          M0,192L48,197.3C96,203,192,213,288,192C384,171,480,117,576,112C672,107,768,149,864,165.3C960,181,1056,171,1152,154.7C1248,139,1344,117,1392,106.7L1440,96L1440,320L0,320Z"/>
                      </path>
                    </svg>
                  </div>
                  <div style="position:absolute;inset:0;opacity:0.25;">
                    <svg style="position:absolute;width:100%;height:100%;transform:translateY(40%);"
                         xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320" preserveAspectRatio="none">
                      <path fill="{w3}" fill-opacity="0.3"
                            d="M0,224L48,213.3C96,203,192,181,288,181.3C384,181,480,203,576,213.3C672,224,768,224,864,208C960,192,1056,160,1152,154.7C1248,149,1344,171,1392,181.3L1440,192L1440,320L0,320Z">
                        <animate attributeName="d" dur="12s" repeatCount="indefinite" values="
                          M0,224L48,213.3C96,203,192,181,288,181.3C384,181,480,203,576,213.3C672,224,768,224,864,208C960,192,1056,160,1152,154.7C1248,149,1344,171,1392,181.3L1440,192L1440,320L0,320Z;
                          M0,256L48,240C96,224,192,192,288,181.3C384,171,480,181,576,197.3C672,213,768,235,864,229.3C960,224,1056,192,1152,170.7C1248,149,1344,139,1392,133.3L1440,128L1440,320L0,320Z;
                          M0,224L48,213.3C96,203,192,181,288,181.3C384,181,480,203,576,213.3C672,224,768,224,864,208C960,192,1056,160,1152,154.7C1248,149,1344,171,1392,181.3L1440,192L1440,320L0,320Z"/>
                      </path>
                    </svg>
                  </div>
                  <div style="position:absolute;inset:0;background:linear-gradient(to bottom,rgba(255,255,255,0.06),transparent);"></div>
                `;

                document.body.insertBefore(bg, document.body.firstChild);

                // lift all siblings above the fixed bg
                Array.from(document.body.children).forEach(function(el) {{
                    if (el.id !== 'ocean-bg') {{
                        el.style.position = 'relative';
                        el.style.zIndex   = '1';
                    }}
                }});
            }})();
            </script>
            <div style="margin:-16px -24px 0 -24px;padding:28px 24px 20px 24px;text-align:center;">
                <h1 style="font-size:38px;font-weight:800;color:{title_color};margin:0 0 8px 0;">
                    🌊 Flood Monitoring System
                </h1>
                <p style="font-size:15px;color:{sub_color};margin:0;">
                    Real-time Coastal Sensor Dashboard
                </p>
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
