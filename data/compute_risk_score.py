import pandas as pd
import numpy as np
import sys


def normalize(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - lo) / (hi - lo)


def compute_risk_score(df: pd.DataFrame) -> pd.Series:
    """
    Risk score from CCE mooring data (output.csv).
    Uses current speed, pressure, and temperature as flood risk proxies.
    Target: normalized 0.0-1.0 where 1.0 = maximum flood risk.
    """
    score = pd.Series(np.zeros(len(df)), index=df.index)
    total_weight = 0.0

    # Current speed — stronger currents = higher flood risk (weight 0.5)
    if "CSPD" in df.columns:
        clean = df["CSPD"].where(df.get("CSPD_QC", pd.Series(1, index=df.index)) == 1)
        score += 0.5 * normalize(clean.fillna(clean.median()))
        total_weight += 0.5

    # Pressure — higher pressure anomaly can indicate surge (weight 0.3)
    if "PRES" in df.columns:
        clean = df["PRES"].where(df.get("PRES_QC", pd.Series(1, index=df.index)) == 1)
        score += 0.3 * normalize(clean.fillna(clean.median()))
        total_weight += 0.3

    # Temperature — anomalously warm water can indicate unusual ocean state (weight 0.2)
    if "TEMP" in df.columns:
        clean = df["TEMP"].where(df.get("TEMP_QC", pd.Series(1, index=df.index)) == 1)
        score += 0.2 * normalize(clean.fillna(clean.median()))
        total_weight += 0.2

    if 0 < total_weight < 1.0:
        score = score / total_weight

    return score.clip(0, 1)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "dataset.csv"
    df = pd.read_csv(path)
    df["risk_score"] = compute_risk_score(df)
    print(df[["risk_score"]].describe())
    out = path.replace(".csv", "_with_risk.csv")
    df.to_csv(out, index=False)
    print(f"Saved to {out}")
