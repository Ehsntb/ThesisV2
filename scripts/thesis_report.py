#!/usr/bin/env python3
import os, re, math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

RESULTS = "results"
RUN = os.path.join(RESULTS, "summary_by_run.csv")
if not os.path.isfile(RUN):
    raise SystemExit(f"❌ {RUN} not found. Run scripts/run_all.py first.")

df = pd.read_csv(RUN)

# استخراج mode/nodes از نام کانفیگ (Secure|NoSec|Attack)(\d+)_record یا نام‌های ویژه
def parse_cfg(c):
    m = re.match(r"(Secure|NoSec|Attack)(\d+)_record$", str(c))
    if m: return m.group(1), int(m.group(2))
    # ویژه‌ها
    if c == "Attack50_window3s_record": return "AttackWindow3s", 50
    if c == "AttackOnNoSec50_record":   return "AttackOnNoSec",   50
    if c == "AttackOnNoSec100_record":  return "AttackOnNoSec",   100
    if c == "Secure50_bloom":           return "SecureBloom",     50
    if c == "Attack50_bloom":           return "AttackBloom",     50
    if c == "Secure50_hmacOnly":        return "HmacOnly",        50
    if c == "Secure50_freshOnly":       return "FreshOnly",       50
    if c == "Secure50_dupOnly":         return "DupOnly",         50
    return "Other", np.nan

df[["mode","nodes"]] = df["config"].apply(lambda c: pd.Series(parse_cfg(c)))

# ثابت‌ها
SIM_TIME_S = 10.0
GATEWAY_INIT_MJ = 5000.0

# مقادیر اشتقاقی
for col in ["GW_Received","GW_Forwarded","GW_Dropped","GW_Dropped_HMAC","GW_Dropped_Stale","GW_Dropped_Duplicate",
            "Cloud_TotalReceived","Cloud_AvgDelay_s","mean_EndToEndDelay_s",
            "GW_BatteryRemaining_mJ","Sensor_EnergyRemaining_mJ","Fake_AttacksSent"]:
    if col not in df.columns:
        df[col] = np.nan

df["throughput_cloud_msgps"] = df["Cloud_TotalReceived"] / SIM_TIME_S
df["energy_consumed_mJ"]     = GATEWAY_INIT_MJ - df["GW_BatteryRemaining_mJ"]
df["energy_per_forwarded_mJ"] = df["energy_consumed_mJ"] / df["GW_Forwarded"].replace(0, np.nan)

# نرخ کشف حمله
detect_num = df[["GW_Dropped_HMAC","GW_Dropped_Stale","GW_Dropped_Duplicate"]].sum(axis=1)
df["detection_rate"] = np.where(df["Fake_AttacksSent"].fillna(0) > 0,
                                np.clip(detect_num / df["Fake_AttacksSent"], 0, 1),
                                np.nan)

# --- خلاصه میانگین/انحراف معیار به ازای mode/nodes ---
metrics = ["Cloud_AvgDelay_s","mean_EndToEndDelay_s","GW_Dropped","throughput_cloud_msgps",
           "energy_per_forwarded_mJ","detection_rate",
           "GW_Dropped_HMAC","GW_Dropped_Stale","GW_Dropped_Duplicate"]
g = df.groupby(["mode","nodes"], as_index=False)
mean_df = g[metrics].mean().rename(columns={m:f"{m}_mean" for m in metrics})
std_df  = g[metrics].std().rename(columns={m:f"{m}_std"  for m in metrics})
final = mean_df.merge(std_df, on=["mode","nodes"], how="left").sort_values(["mode","nodes"])
final.to_csv(os.path.join(RESULTS,"summary_advanced_by_config.csv"), index=False)

# ---------- نمودارها ----------
os.makedirs(RESULTS, exist_ok=True)

def line_by_mode(dfm, ycol, title, ylabel, outfile, order=("NoSec","Secure","Attack")):
    plt.figure()
    for mode in order:
        sub = dfm[dfm["mode"]==mode].dropna(subset=["nodes", ycol]).sort_values("nodes")
        if sub.empty: continue
        plt.plot(sub["nodes"], sub[ycol], marker="o", label=mode)
    plt.title(title); plt.xlabel("Nodes"); plt.ylabel(ylabel)
    plt.grid(True, linestyle="--", alpha=0.5); plt.legend(); plt.tight_layout()
    plt.savefig(outfile, dpi=150); plt.close(); print("🖼 ", outfile)

# تاخیر (ms)
final["E2E_ms_mean"] = final["mean_EndToEndDelay_s_mean"]*1000.0
line_by_mode(final, "E2E_ms_mean", "End-to-End Delay vs Nodes", "Mean E2E Delay (ms)",
             os.path.join(RESULTS,"chart2_delay_ms.png"))

# Drop در Gateway
line_by_mode(final, "GW_Dropped_mean", "Gateway Drops vs Nodes", "Drops (mean)",
             os.path.join(RESULTS,"chart2_drops.png"))

# انرژی/پیام
line_by_mode(final, "energy_per_forwarded_mJ_mean", "Energy per Forwarded Message vs Nodes", "mJ / msg",
             os.path.join(RESULTS,"chart2_energy_per_msg.png"))

# Throughput
line_by_mode(final, "throughput_cloud_msgps_mean", "Cloud Throughput vs Nodes", "msgs/s",
             os.path.join(RESULTS,"chart2_throughput.png"))

# نرخ کشف حمله (Attack)
plt.figure()
sub = final[final["mode"].isin(["Attack","AttackBloom","AttackOnNoSec","AttackWindow3s"])].dropna(subset=["nodes","detection_rate_mean"]).sort_values(["mode","nodes"])
for mode in sub["mode"].unique():
    d = sub[sub["mode"]==mode]
    plt.plot(d["nodes"], d["detection_rate_mean"], marker="o", label=mode)
plt.title("Detection Rate vs Nodes (Attack*)"); plt.xlabel("Nodes"); plt.ylabel("Detection Rate")
plt.ylim(0,1.05); plt.grid(True, linestyle="--", alpha=0.5); plt.legend(); plt.tight_layout()
plt.savefig(os.path.join(RESULTS,"chart2_detection_rate.png"), dpi=150); plt.close(); print("🖼 ", os.path.join(RESULTS,"chart2_detection_rate.png"))

# Breakdown Drop برای Attack (stacked bar در 50/100 نود اگر باشد)
att = final[final["mode"].isin(["Attack","AttackBloom","AttackOnNoSec","AttackWindow3s"])].copy()
for nodes in sorted(att["nodes"].dropna().unique()):
    d = att[att["nodes"]==nodes]
    if d.empty: continue
    x = np.arange(len(d))
    h = d["GW_Dropped_HMAC_mean"].fillna(0).to_numpy()
    s = d["GW_Dropped_Stale_mean"].fillna(0).to_numpy()
    u = d["GW_Dropped_Duplicate_mean"].fillna(0).to_numpy()
    plt.figure()
    plt.bar(x, h, label="HMAC")
    plt.bar(x, s, bottom=h, label="Stale")
    plt.bar(x, u, bottom=h+s, label="Duplicate")
    plt.xticks(x, d["mode"]); plt.title(f"Drop Breakdown @ {int(nodes)} nodes")
    plt.ylabel("Drops (mean)"); plt.legend(); plt.tight_layout()
    out = os.path.join(RESULTS, f"chart2_drop_breakdown_{int(nodes)}n.png")
    plt.savefig(out, dpi=150); plt.close(); print("🖼 ", out)

# مقایسه Bloom vs Set (Secure/Attack، 50 نود)
comp = final[final["nodes"]==50]
plt.figure()
labels = []
vals = []
for mode in ["Secure","SecureBloom","Attack","AttackBloom"]:
    d = comp[comp["mode"]==mode]
    if d.empty: continue
    labels.append(mode)
    vals.append(float(d["energy_per_forwarded_mJ_mean"]))
plt.bar(np.arange(len(vals)), vals)
plt.xticks(np.arange(len(vals)), labels)
plt.title("Bloom vs Set @50 nodes (Energy per Msg)"); plt.ylabel("mJ/msg"); plt.tight_layout()
out = os.path.join(RESULTS, "chart2_bloom_energy.png"); plt.savefig(out, dpi=150); plt.close(); print("🖼 ", out)

# پنجره تازگی 1s vs 3s (Attack50)
comp2 = final[(final["nodes"]==50) & (final["mode"].isin(["Attack","AttackWindow3s"]))]
plt.figure()
for metric, ylabel in [("detection_rate_mean", "Detection Rate"), ("E2E_ms_mean","E2E Delay (ms)"), ("GW_Dropped_mean","Drops")]:
    if comp2.empty: break
plt.figure()
if not comp2.empty:
    x = np.arange(len(comp2))
    plt.bar(x, comp2["detection_rate_mean"])
    plt.xticks(x, comp2["mode"]); plt.ylim(0,1.05)
    plt.title("Freshness Window Sensitivity @50 nodes"); plt.ylabel("Detection Rate")
    plt.tight_layout()
    out = os.path.join(RESULTS, "chart2_window_sensitivity.png"); plt.savefig(out, dpi=150); plt.close(); print("🖼 ", out)

# ---------- جدول‌های Markdown/LaTeX ----------
def table_md(dfm, cols, title, unit, path):
    s = [f"### {title} ({unit})", "", "| Nodes | " + " | ".join(cols) + " |", "|---:|"+ "|".join([":---:"]*len(cols)) +"|"]
    for n in sorted(dfm["nodes"].dropna().unique()):
        row = dfm[dfm["nodes"]==n]
        vals = []
        for c in cols:
            vals.append(f"{row.iloc[0][c]:.3f}" if (not row.empty and pd.notna(row.iloc[0][c])) else "—")
        s.append(f"| {int(n)} | " + " | ".join(vals) + " |")
    with open(path,"w") as f: f.write("\n".join(s))

import pandas as pd
# سه جدول رایج:
delay_tbl = final.pivot_table(index="nodes", columns="mode", values="E2E_ms_mean")
drops_tbl = final.pivot_table(index="nodes", columns="mode", values="GW_Dropped_mean")
epm_tbl   = final.pivot_table(index="nodes", columns="mode", values="energy_per_forwarded_mJ_mean")

delay_tbl.to_csv(os.path.join(RESULTS,"table2_delay_by_nodes.csv"))
drops_tbl.to_csv(os.path.join(RESULTS,"table2_drops_by_nodes.csv"))
epm_tbl.to_csv(os.path.join(RESULTS,"table2_energy_per_msg_by_nodes.csv"))

print("✅ Wrote CSV tables: table2_*_by_nodes.csv")
print("✅ Done.")
