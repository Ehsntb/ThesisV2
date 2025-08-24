import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure plots directory exists
os.makedirs("plots", exist_ok=True)

# Load CSV
df = pd.read_csv("../results/energy_delay.csv")

# Define style
plt.style.use("seaborn-v0_8-whitegrid")

# Function to plot a specific metric
def plot_metric(metric_col, ylabel, filename):
    plt.figure(figsize=(8, 5))
    for scenario in df['Scenario'].unique():
        subset = df[df['Scenario'] == scenario]
        plt.plot(subset['Nodes'], subset[metric_col], marker='o', label=scenario)
    
    plt.title(ylabel)
    plt.xlabel("Number of Nodes")
    plt.ylabel(ylabel)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{filename}")
    plt.close()
    print(f"[✔] Saved: {filename}")

# Plot 1: Avg Energy Sensor
plot_metric("AvgEnergySensor(mJ)", "Average Sensor Energy (mJ)", "avg_sensor_energy.png")

# Plot 2: Avg Energy Gateway
plot_metric("AvgEnergyGateway(mJ)", "Average Gateway Energy (mJ)", "avg_gateway_energy.png")

# Plot 3: Average Delay
plot_metric("AvgDelay(s)", "Average Packet Delay (s)", "avg_delay.png")

# Plot 4: Drop Rate
plot_metric("DropRate(%)", "Packet Drop Rate (%)", "drop_rate.png")