import pandas as pd
import numpy as np
import sys


def normalize(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(np.zeros(len(series)))
    return (series - lo) / (hi - lo)


def compute_risk_score(df: pd.DataFrame) -> pd.Series:
    """
    Fill in weights and column names after running inspect_dataset.py.
    Target: normalized 0.0–1.0 float where 1.0 = maximum flood risk.
    """
    score = pd.Series(np.zeros(len(df)), index=df.index)

    # --- ADAPT THESE after seeing dataset columns ---
    # Example structure: (column_name, weight)
    # Weights should sum to 1.0
    candidates = [
        ("tide_level",   0.4),
        ("wave_height",  0.3),
        ("storm_surge",  0.3),
    ]

    total_weight = 0.0
    for col, weight in candidates:
        if col in df.columns:
            score += weight * normalize(df[col])
            total_weight += weight

    # Rescale if some columns were missing
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
