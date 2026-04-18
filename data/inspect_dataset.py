import pandas as pd
import sys

df = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "dataset.csv")
print("=== SHAPE ===", df.shape)
print("\n=== COLUMNS ===")
print(df.dtypes)
print("\n=== HEAD ===")
print(df.head(3))
print("\n=== NULL COUNTS ===")
print(df.isnull().sum())
print("\n=== NUMERIC STATS ===")
print(df.describe())
