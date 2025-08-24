

#!/usr/bin/env python3
import argparse, glob, os, re, math
from statistics import mean, pstdev
import numpy as np
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--configs', type=str, default='', help='space-separated list of configs (e.g., "Secure50_CI Attack50_CI")')
parser.add_argument('--out', type=str, default='results/ci_summary.csv')
args = parser.parse_args()

configs = args.configs.split()
if not configs:
    # autodetect *_CI-*.sca
    scas = glob.glob('results/*_CI-*.sca')
    configs = sorted({ re.sub(r'-\\d+\\.sca$','', os.path.basename(p)) for p in scas })

metrics = [
    'Cloud_TotalReceived',
    'GW_Received','GW_Forwarded','GW_Dropped',
    'GW_Dropped_HMAC','GW_Dropped_Stale','GW_Dropped_Duplicate',
    'GW_BatteryRemaining_mJ',
    'Cloud_AvgEndToEndDelay_s',
    'Fake_AttacksSent'
]

# helper: pull value(s) from .sca
numre = re.compile(r'^scalar\s+\S+\s+(\S+)\s+([+-]?[0-9]*\.?[0-9]+([eE][+-]?[0-9]+)?)')

def parse_sca(path):
    vals = { m: None for m in metrics }
    sensor_batts = []
    with open(path, 'r', errors='ignore') as f:
        for line in f:
            m = numre.match(line)
            if not m: continue
            name, val = m.group(1), float(m.group(2))
            if name == 'Sensor_BatteryRemaining_mJ':
                sensor_batts.append(val)
            elif name in vals and vals[name] is None:
                vals[name] = val
    if sensor_batts:
        vals['Sensor_AvgBattery_mJ'] = float(np.mean(sensor_batts))
    else:
        vals['Sensor_AvgBattery_mJ'] = None
    return vals

# derive nodes/mode from config name
rg_secure = re.compile(r'^Secure(\d+)_CI$')
rg_nosec  = re.compile(r'^NoSec(\d+)_CI$')
rg_attack = re.compile(r'^Attack(\d+)_CI$')

def derive_info(cfg):
    nodes, mode = '', ''
    m = rg_secure.match(cfg)
    if m: return int(m.group(1)), 'Secure'
    m = rg_nosec.match(cfg)
    if m: return int(m.group(1)), 'NoSec'
    m = rg_attack.match(cfg)
    if m: return int(m.group(1)), 'Attack'
    return None, ''

rows = []
for cfg in configs:
    scas = sorted(glob.glob(f'results/{cfg}-*.sca'))
    if not scas:
        continue
    runs = [parse_sca(p) for p in scas]
    n = len(runs)
    def agg(key):
        xs = [r[key] for r in runs if r.get(key) is not None]
        if not xs:
            return (None,None)
        m = float(np.mean(xs))
        # 95% CI (normal approx); use sample std
        if len(xs) > 1:
            s = float(np.std(xs, ddof=1))
            ci = 1.96 * s / math.sqrt(len(xs))
        else:
            ci = 0.0
        return (m, ci)

    nodes, mode = derive_info(cfg)
    row = {
        'Config': cfg,
        'Nodes': nodes,
        'Mode': mode,
        'n_runs': n,
    }
    for mname in metrics + ['Sensor_AvgBattery_mJ']:
        mean_ci = agg(mname)
        row[f'{mname}_mean'] = None if mean_ci[0] is None else round(mean_ci[0], 6)
        row[f'{mname}_ci95'] = None if mean_ci[1] is None else round(mean_ci[1], 6)
    rows.append(row)

os.makedirs(os.path.dirname(args.out), exist_ok=True)
pd.DataFrame(rows).to_csv(args.out, index=False)
print(f"Wrote {args.out} with {len(rows)} rows")