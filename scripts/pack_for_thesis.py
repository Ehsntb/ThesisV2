#!/usr/bin/env python3
import os, shutil, time, glob, json
BASE = "results"
stamp = time.strftime("%Y%m%d-%H%M")
OUT = f"thesis_artifacts_{stamp}"
os.makedirs(OUT, exist_ok=True)

# فایل‌های کلیدی
keep = [
  "summary_by_run.csv","summary_by_config.csv","summary_advanced_by_config.csv",
  "table2_delay_by_nodes.csv","table2_drops_by_nodes.csv","table2_energy_per_msg_by_nodes.csv",
  "chart2_delay_ms.png","chart2_drops.png","chart2_energy_per_msg.png","chart2_throughput.png",
  "chart2_detection_rate.png","chart2_drop_breakdown_5n.png","chart2_drop_breakdown_20n.png","chart2_drop_breakdown_50n.png",
  "chart2_bloom_energy.png","chart2_window_sensitivity.png",
  "chart_delay_vs_nodes_ms.png","chart_drops_vs_nodes.png","chart_gateway_energy_vs_nodes.png"
]
copied = []
for k in keep:
    src = os.path.join(BASE,k)
    if os.path.isfile(src):
        shutil.copy2(src, os.path.join(OUT,k))
        copied.append(k)

# یک README کوتاه
readme = f"""# Thesis Artifacts ({stamp})

This bundle contains summary CSVs and figures ready for the thesis.

## CSVs
- summary_by_run.csv: all runs (per repetition)
- summary_by_config.csv: means/std by mode & nodes
- summary_advanced_by_config.csv: advanced metrics (throughput, energy/msg, detection rate)
- table2_*_by_nodes.csv: per-nodes tables for LaTeX/Markdown

## Figures
- chart2_delay_ms.png, chart2_drops.png, chart2_energy_per_msg.png, chart2_throughput.png
- chart2_detection_rate.png, chart2_drop_breakdown_{5,20,50}n.png
- chart2_bloom_energy.png, chart2_window_sensitivity.png
"""
with open(os.path.join(OUT,"README.txt"),"w") as f: f.write(readme)

print(f"📦 Packed {len(copied)} files into {OUT}/")
