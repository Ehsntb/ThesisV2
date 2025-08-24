import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure plots directory exists
os.makedirs("plots", exist_ok=True)

# Load CSV
df = pd.read_csv("../results/stats_summary.csv")

# Extract Node count from Scenario string for sorting
df["Nodes"] = df["Scenario"].str.extract(r"(\d+)").astype(int)

# Define style
plt.style.use("seaborn-v0_8-whitegrid")

# Function to plot a specific metric
def plot_summary_metric(metric_col, ylabel, filename):
    plt.figure(figsize=(8, 5))
    for mode in df["Mode"].unique():
        subset = df[df["Mode"] == mode].sort_values("Nodes")
        plt.plot(subset["Nodes"], subset[metric_col], marker='o', label=mode)

    plt.title(ylabel)
    plt.xlabel("Number of Nodes")
    plt.ylabel(ylabel)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"plots/{filename}")
    plt.close()
    print(f"[✔] Saved: {filename}")

# Plot 1: Total Energy
plot_summary_metric("AvgEnergyTotal(mJ)", "Total Energy (mJ)", "summary_energy.png")

# Plot 2: Average Delay
plot_summary_metric("AvgDelay(s)", "Average Delay (s)", "summary_delay.png")

# Plot 3: Drop Rate
plot_summary_metric("DropRate(%)", "Drop Rate (%)", "summary_droprate.png")