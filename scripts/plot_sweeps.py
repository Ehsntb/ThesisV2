

#!/usr/bin/env python3
import sys, pandas as pd, matplotlib.pyplot as plt
from pathlib import Path

if len(sys.argv)<2:
    print("Usage: plot_sweeps.py results/summary_sweeps.csv"); sys.exit(0)
csv = Path(sys.argv[1])
if not csv.exists():
    print(f"[ERR] {csv} not found"); sys.exit(1)

df = pd.read_csv(csv)
for c in ["Cloud_TotalReceived","GW_Received","GW_Forwarded","GW_Dropped","GW_Battery_mJ","Sensor_AvgBattery_mJ","Cloud_AvgDelay_s","Fake_AttacksSent"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce')

out = Path('results'); out.mkdir(exist_ok=True)

# Window sweep
win = df[df['Config'].str.startswith('Attack50_win', na=False)].copy()
if not win.empty:
    win['Window_s'] = win['Window_s'].astype(str).str.replace('p','.', regex=False).astype(float)
    win = win.sort_values('Window_s')
    plt.figure(); plt.plot(win['Window_s'], win['GW_Dropped'], marker='o', label='Drops')
    plt.xlabel('Freshness Window (s)'); plt.ylabel('Drops'); plt.title('Drops vs Freshness Window (Attack50)'); plt.grid(True, linestyle='--', alpha=0.4); plt.tight_layout(); plt.savefig(out/"sweep_window_drops.png", dpi=160)
    plt.figure(); plt.plot(win['Window_s'], win['Cloud_AvgDelay_s']*1000, marker='o', label='Delay (ms)')
    plt.xlabel('Freshness Window (s)'); plt.ylabel('Avg Delay (ms)'); plt.title('Delay vs Freshness Window (Attack50)'); plt.grid(True, linestyle='--', alpha=0.4); plt.tight_layout(); plt.savefig(out/"sweep_window_delay_ms.png", dpi=160)
    plt.figure(); plt.plot(win['Window_s'], win['GW_Battery_mJ'], marker='o', label='GW Battery')
    plt.xlabel('Freshness Window (s)'); plt.ylabel('Gateway Battery (mJ)'); plt.title('Battery vs Freshness Window (Attack50)'); plt.grid(True, linestyle='--', alpha=0.4); plt.tight_layout(); plt.savefig(out/"sweep_window_battery.png", dpi=160)

# Replay sweep
rep = df[df['Config'].str.startswith('Attack50_replay', na=False)].copy()
if not rep.empty:
    rep['ReplayInterval_s'] = rep['ReplayInterval_s'].astype(str).str.replace('p','.', regex=False).astype(float)
    rep = rep.sort_values('ReplayInterval_s')
    plt.figure(); plt.plot(rep['ReplayInterval_s'], rep['GW_Dropped'], marker='o')
    plt.xlabel('Replay Interval (s)'); plt.ylabel('Drops'); plt.title('Drops vs Replay Interval (Attack50)'); plt.grid(True, linestyle='--', alpha=0.4); plt.tight_layout(); plt.savefig(out/"sweep_replay_drops.png", dpi=160)
    plt.figure(); plt.plot(rep['ReplayInterval_s'], rep['Cloud_AvgDelay_s']*1000, marker='o')
    plt.xlabel('Replay Interval (s)'); plt.ylabel('Avg Delay (ms)'); plt.title('Delay vs Replay Interval (Attack50)'); plt.grid(True, linestyle='--', alpha=0.4); plt.tight_layout(); plt.savefig(out/"sweep_replay_delay_ms.png", dpi=160)
    plt.figure(); plt.plot(rep['ReplayInterval_s'], rep['GW_Battery_mJ'], marker='o')
    plt.xlabel('Replay Interval (s)'); plt.ylabel('Gateway Battery (mJ)'); plt.title('Battery vs Replay Interval (Attack50)'); plt.grid(True, linestyle='--', alpha=0.4); plt.tight_layout(); plt.savefig(out/"sweep_replay_battery.png", dpi=160)

print("Sweep plots saved to results/")