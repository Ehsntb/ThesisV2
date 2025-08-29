#!/usr/bin/env python3
import re, os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

RESULTS = "results"
RUN_CSV = os.path.join(RESULTS, "summary_by_run.csv")
CFG_CSV = os.path.join(RESULTS, "summary_by_config.csv")

if not os.path.isfile(RUN_CSV):
    sys.exit(f"❌ {RUN_CSV} not found. Run scripts/run_all.py first.")

df = pd.read_csv(RUN_CSV)

# استخراج mode و تعداد نود از نام کانفیگ، مثل: Secure50_record
def parse_cfg(cfg):
    m = re.match(r"(Secure|NoSec|Attack)(\d+)_record$", str(cfg))
    if not m:
        return ("Other", np.nan)
    return (m.group(1), int(m.group(2)))

df[["mode","nodes"]] = df["config"].apply(lambda c: pd.Series(parse_cfg(c)))

# میانگین و انحراف معیار روی تکرارها
metrics = [
    "GW_Received","GW_Forwarded","GW_Dropped",
    "GW_Dropped_HMAC","GW_Dropped_Stale","GW_Dropped_Duplicate",
    "Cloud_TotalReceived","Cloud_AvgDelay_s","mean_EndToEndDelay_s",
    "GW_BatteryRemaining_mJ","Sensor_EnergyRemaining_mJ"
]
for col in metrics:
    if col not in df.columns:
        df[col] = np.nan

g = df.groupby(["mode","nodes"], as_index=False)
mean_df = g[metrics].mean().rename(columns={m:f"{m}_mean" for m in metrics})
std_df  = g[metrics].std().rename(columns={m:f"{m}_std"  for m in metrics})
final = mean_df.merge(std_df, on=["mode","nodes"], how="left").sort_values(["mode","nodes"])

final.to_csv(CFG_CSV, index=False)
print(f"📄 Wrote {CFG_CSV}  (rows={len(final)})")

# ---------- نمودارها ----------
os.makedirs(RESULTS, exist_ok=True)

def plot_delay_ms(dfm, out):
    plt.figure()
    for mode in ["NoSec","Secure","Attack"]:
        sub = dfm[dfm["mode"]==mode].sort_values("nodes")
        if sub.empty: continue
        x = sub["nodes"].to_list()
        y = (sub["mean_EndToEndDelay_s_mean"]*1000.0).to_list()  # ms
        plt.plot(x, y, marker="o", label=mode)
    plt.title("End-to-End Delay vs Nodes (ms)")
    plt.xlabel("Nodes")
    plt.ylabel("Mean E2E Delay (ms)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"🖼  {out}")

def plot_drops(dfm, out):
    plt.figure()
    for mode in ["NoSec","Secure","Attack"]:
        sub = dfm[dfm["mode"]==mode].sort_values("nodes")
        if sub.empty: continue
        x = sub["nodes"].to_list()
        y = sub["GW_Dropped_mean"].to_list()
        plt.plot(x, y, marker="s", label=mode)
    plt.title("Gateway Drops vs Nodes")
    plt.xlabel("Nodes")
    plt.ylabel("Dropped Messages (mean)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"🖼  {out}")

def plot_gateway_energy(dfm, out):
    plt.figure()
    for mode in ["NoSec","Secure","Attack"]:
        sub = dfm[dfm["mode"]==mode].sort_values("nodes")
        if sub.empty: continue
        x = sub["nodes"].to_list()
        y = sub["GW_BatteryRemaining_mJ_mean"].to_list()
        plt.plot(x, y, marker="^", label=mode)
    plt.title("Gateway Energy Remaining vs Nodes (mJ)")
    plt.xlabel("Nodes")
    plt.ylabel("Energy Remaining (mJ)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"🖼  {out}")

plot_delay_ms(final, os.path.join(RESULTS,"chart_delay_vs_nodes_ms.png"))
plot_drops(final, os.path.join(RESULTS,"chart_drops_vs_nodes.png"))
plot_gateway_energy(final, os.path.join(RESULTS,"chart_gateway_energy_vs_nodes.png"))
