import pandas as pd
import os
from datetime import datetime

DATA_FOLDER = "captured_data"
OUTPUT = "annotation_analysis.csv"

rows = []

for file in os.listdir(DATA_FOLDER):
    if not file.endswith(".csv"):
        continue

    path = os.path.join(DATA_FOLDER, file)
    df = pd.read_csv(path)

    # Filename format: sequence_yyyymmddHHMMss.csv
    stamp = file.split("_")[1].replace(".csv", "")
    t = datetime.strptime(stamp, "%Y%m%d%H%M%S")

    # Provisional label from experiment timeline
    # 0 = no activity, 1 = waving, 2 = shaking
    if t.hour == 16 and t.minute < 20:
        activity = 0
    elif t.hour == 16 and t.minute < 30:
        activity = 1
    else:
        activity = 2

    row = {
        "filename": file,
        "activity": activity
    }

    for axis in ["X", "Y", "Z"]:
        row[f"{axis}_mean"] = df[axis].mean()
        row[f"{axis}_std"] = df[axis].std()
        row[f"{axis}_min"] = df[axis].min()
        row[f"{axis}_max"] = df[axis].max()
        row[f"{axis}_range"] = df[axis].max() - df[axis].min()

    rows.append(row)

result = pd.DataFrame(rows)

if not result.empty:
    result["sequence"] = result["filename"].str.split("_").str[0].astype(int)
    result = result.sort_values("sequence").drop(columns="sequence")

result.to_csv(OUTPUT, index=False)

print(result.head())
print(f"\nSaved {OUTPUT}")
