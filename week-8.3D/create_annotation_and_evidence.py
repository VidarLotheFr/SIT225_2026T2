import os
import shutil
import pandas as pd
import matplotlib.pyplot as plt

DATA_FOLDER = "captured_data"
ANALYSIS_FILE = "annotation_analysis.csv"
ANNOTATION_FILE = "annotation.csv"
EVIDENCE_FOLDER = "evidence"
EXAMPLES_PER_ACTIVITY = 3

ACTIVITY_NAMES = {
    0: "no_activity",
    1: "waving",
    2: "shaking"
}

analysis = pd.read_csv(ANALYSIS_FILE)

# 1. Clean 2-column annotation file
analysis[["filename", "activity"]].to_csv(ANNOTATION_FILE, index=False)
print(f"Created {ANNOTATION_FILE} ({len(analysis)} rows)")

# 2. Choose representative examples using median movement score
os.makedirs(EVIDENCE_FOLDER, exist_ok=True)

analysis["movement_score"] = analysis[["X_std", "Y_std", "Z_std"]].sum(axis=1)
selected = []

for activity, group in analysis.groupby("activity"):
    activity = int(activity)
    activity_name = ACTIVITY_NAMES.get(activity, f"activity_{activity}")
    median_score = group["movement_score"].median()

    examples = (
        group.assign(distance=(group["movement_score"] - median_score).abs())
        .sort_values("distance")
        .head(EXAMPLES_PER_ACTIVITY)
    )

    activity_folder = os.path.join(EVIDENCE_FOLDER, activity_name)
    os.makedirs(activity_folder, exist_ok=True)

    for number, (_, row) in enumerate(examples.iterrows(), start=1):
        csv_name = row["filename"]
        csv_path = os.path.join(DATA_FOLDER, csv_name)

        if not os.path.exists(csv_path):
            print(f"Missing CSV: {csv_path}")
            continue

        df = pd.read_csv(csv_path)

        plt.figure(figsize=(9, 4))
        for axis in ["X", "Y", "Z"]:
            plt.plot(df["timestamp"], df[axis], label=axis)

        plt.title(f"{activity_name.replace('_', ' ').title()} - Example {number}")
        plt.xlabel("Time")
        plt.ylabel("Acceleration")
        plt.legend()
        plt.xticks(rotation=30)
        plt.tight_layout()

        graph_path = os.path.join(
            activity_folder,
            f"{activity_name}_{number}_graph.png"
        )
        plt.savefig(graph_path, dpi=150)
        plt.close()

        image_name = os.path.splitext(csv_name)[0] + ".jpg"
        image_path = os.path.join(DATA_FOLDER, image_name)
        photo_path = ""

        if os.path.exists(image_path):
            photo_path = os.path.join(
                activity_folder,
                f"{activity_name}_{number}_photo.jpg"
            )
            shutil.copy2(image_path, photo_path)
        else:
            print(f"Missing image: {image_path}")

        selected.append({
            "activity": activity,
            "activity_name": activity_name,
            "source_csv": csv_name,
            "graph": graph_path,
            "photo": photo_path
        })

pd.DataFrame(selected).to_csv(
    os.path.join(EVIDENCE_FOLDER, "selected_examples.csv"),
    index=False
)

print("\nFinished.")
print(f"- {ANNOTATION_FILE}")
print(f"- {EVIDENCE_FOLDER}/")
