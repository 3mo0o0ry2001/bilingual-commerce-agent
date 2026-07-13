import pandas as pd

pd.set_option("display.max_colwidth", 200)

df = pd.read_csv("data/raw/fra_perfumes.csv")
print("Total rows:", len(df))
print("Columns:", list(df.columns))
print()

print("--- Sample record (row 0) ---")
row = df.iloc[0]
for col in df.columns:
    print(f"{col}: {row[col]}")
    print()

print("--- Gender value counts ---")
print(df["Gender"].value_counts().head(10))

print("\n--- Null counts ---")
print(df.isnull().sum())