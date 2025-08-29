#!/usr/bin/env python3
import os, re, numpy as np, pandas as pd

RESULTS = "results"
CFG_CSV = os.path.join(RESULTS, "summary_by_config.csv")
if not os.path.isfile(CFG_CSV):
    raise SystemExit(f"❌ {CFG_CSV} not found. Run scripts/summarize_and_plot.py first.")

df = pd.read_csv(CFG_CSV)
# ستون‌های میانگین/انحراف معیار
delay = df.pivot_table(index="nodes", columns="mode", values="mean_EndToEndDelay_s_mean")*1000.0
drops = df.pivot_table(index="nodes", columns="mode", values="GW_Dropped_mean")
energy= df.pivot_table(index="nodes", columns="mode", values="GW_BatteryRemaining_mJ_mean")

def fmt_md(table, title, unit):
    s = [f"### {title} ({unit})", "", "| Nodes | NoSec | Secure | Attack |", "|---:|---:|---:|---:|"]
    for n in sorted(table.index):
        row = table.loc[n]
        s.append(f"| {n} | {row.get('NoSec',np.nan):.3f} | {row.get('Secure',np.nan):.3f} | {row.get('Attack',np.nan):.3f} |")
    s.append("")
    return "\n".join(s)

def fmt_tex(table, title, unit, label):
    s  = [r"\begin{table}[h]", r"\centering", rf"\caption{{{title} ({unit})}}", rf"\label{{{label}}}",
          r"\begin{tabular}{rccc}", r"\toprule", r"Nodes & NoSec & Secure & Attack \\ \midrule"]
    for n in sorted(table.index):
        row = table.loc[n]
        s.append(f"{n} & {row.get('NoSec',np.nan):.3f} & {row.get('Secure',np.nan):.3f} & {row.get('Attack',np.nan):.3f} \\\\")
    s += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(s)

md = []
md.append(fmt_md(delay, "Mean End-to-End Delay vs Nodes", "ms"))
md.append(fmt_md(drops, "Gateway Drops vs Nodes", "count"))
md.append(fmt_md(energy,"Gateway Energy Remaining vs Nodes", "mJ"))
with open(os.path.join(RESULTS,"tables.md"),"w") as f: f.write("\n".join(md))

with open(os.path.join(RESULTS,"table_delay.tex"),"w")  as f: f.write(fmt_tex(delay, "Mean End-to-End Delay vs Nodes", "ms", "tab:delay"))
with open(os.path.join(RESULTS,"table_drops.tex"),"w")  as f: f.write(fmt_tex(drops, "Gateway Drops vs Nodes", "count", "tab:drops"))
with open(os.path.join(RESULTS,"table_energy.tex"),"w") as f: f.write(fmt_tex(energy,"Gateway Energy Remaining vs Nodes", "mJ", "tab:energy"))

print("✅ Wrote results/tables.md, table_delay.tex, table_drops.tex, table_energy.tex")
