import pandas as pd
import matplotlib.pyplot as plt
import os

# Change this to the ambiguous CSV you want to plot
FILE = "captured_data/105_20260907163133.csv"

df = pd.read_csv(FILE)

plt.figure(figsize=(9, 4))

for axis in ["X", "Y", "Z"]:
    plt.plot(df["timestamp"], df[axis], label=axis)

plt.title("Ambiguous Transition Sample")
plt.xlabel("Time")
plt.ylabel("Acceleration")
plt.legend()
plt.xticks(rotation=30)
plt.tight_layout()

output_name = "ambiguous_graph.png"
plt.savefig(output_name, dpi=150)
plt.show()

image_file = os.path.splitext(FILE)[0] + ".jpg"

print(f"Saved graph: {output_name}")
print(f"Matching webcam image: {image_file}")
