import os, sys, re, statistics, glob

def parse_sca(path):
    scalars = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if not line.startswith('scalar '): 
                continue
            # scalar <module> <name> <value> [attr...]
            parts = line.strip().split()
            if len(parts) < 4: 
                continue
            module = parts[1]
            name   = parts[2]
            try:
                value  = float(parts[3])
            except:
                continue
            scalars.append((module, name, value))
    return scalars

def pick(scalars, names, agg='sum'):
    vals = [v for _,n,v in scalars if n in names]
    if not vals:
        return 0.0
    if agg == 'sum':
        return float(sum(vals))
    if agg == 'avg':
        return float(sum(vals)/len(vals))
    if agg == 'max':
        return float(max(vals))
    return float(sum(vals))

def first(scalars, names, default=0.0):
    for _,n,v in scalars:
        if n in names:
            return float(v)
    return float(default)

def infer_cfg(fname):
    import os, re
    base = os.path.basename(fname)
    cfg  = os.path.splitext(base)[0]
    mode  = 'Unknown'
    nodes = ''
    # اسم‌های کانفیگ رو case-insensitive بگیر (پایان با _record)
    m = re.match(r'(?i)^(Secure|NoSec|Attack)(\d+)_record$', cfg)
    if m:
        mode_map = {'secure': 'Secure', 'nosec': 'NoSec', 'attack': 'Attack'}
        mode  = mode_map[m.group(1).lower()]
        nodes = m.group(2)
    return cfg, nodes, mode

def main(indir, outcsv):
    sca_files = sorted(glob.glob(os.path.join(indir, '*.sca')))
    if not sca_files:
        print(f"ERROR: no .sca in {indir}")
        sys.exit(1)

    rows = []
    for sca in sca_files:
        scalars = parse_sca(sca)
        cfg, nodes, mode = infer_cfg(sca)

        # Cloud
        cloud_total = first(scalars, ["Cloud_TotalReceived","cloud_total_received","Cloud_Received"], 0.0)
        cloud_delay = first(scalars, ["Cloud_AvgDelay_s","Cloud_AverageDelay","cloud_avg_delay_s"], 0.0)

        # Gateway: پشتیبانی از نام‌های قدیم/جدید
        gw_recv   = first(scalars, ["GW_Received","totalProcessed","gw_received"], 0.0)
        gw_fwd    = first(scalars, ["GW_Forwarded","totalAccepted","gw_forwarded"], 0.0)
        gw_drop   = first(scalars, ["GW_Dropped","totalDropped","gw_dropped"], 0.0)
        gw_d_hmac = first(scalars, ["GW_Dropped_HMAC","totalDroppedHmac","gw_dropped_hmac"], 0.0)
        gw_d_stal = first(scalars, ["GW_Dropped_Stale","totalDroppedReplay","gw_dropped_stale","totalDroppedStale"], 0.0)
        gw_d_dup  = first(scalars, ["GW_Dropped_Duplicate","totalDroppedDup","gw_dropped_duplicate"], 0.0)
        gw_batt   = first(scalars, ["GW_Battery_mJ","GW_BatteryRemaining_mJ","energyGW_mJ","gw_battery_mJ"], 0.0)

        # اگر Received صفر بود ولی بقیه داریم، خودش را بازسازی کن
        if gw_recv == 0.0 and (gw_fwd>0.0 or gw_drop>0.0 or gw_d_hmac>0.0 or gw_d_stal>0.0 or gw_d_dup>0.0):
            gw_recv = gw_fwd + max(gw_drop, (gw_d_hmac + gw_d_stal + gw_d_dup))

        # Sensor: میانگین انرژی باقی‌مانده
        sensor_vals = [v for _,n,v in scalars if n in ("Sensor_EnergyRemaining_mJ","Sensor_Energy_mJ")]
        sensor_avg  = float(sum(sensor_vals)/len(sensor_vals)) if sensor_vals else 0.0

        # Fake
        fake_sent   = first(scalars, ["Fake_AttacksSent","AttacksSent","fake_attacks"], 0.0)

        rows.append({
            "Config": os.path.splitext(os.path.basename(sca))[0],
            "Nodes": nodes,
            "Mode": mode,
            "Cloud_TotalReceived": cloud_total,
            "GW_Received": gw_recv,
            "GW_Forwarded": gw_fwd,
            "GW_Dropped": gw_drop,
            "GW_Dropped_HMAC": gw_d_hmac,
            "GW_Dropped_Stale": gw_d_stal,
            "GW_Dropped_Duplicate": gw_d_dup,
            "GW_Battery_mJ": gw_batt,
            "Sensor_AvgBattery_mJ": sensor_avg,
            "Cloud_AvgDelay_s": cloud_delay,
            "Fake_AttacksSent": fake_sent,
        })

    # نوشتن CSV
    cols = ["Config","Nodes","Mode","Cloud_TotalReceived","GW_Received","GW_Forwarded","GW_Dropped",
            "GW_Dropped_HMAC","GW_Dropped_Stale","GW_Dropped_Duplicate",
            "GW_Battery_mJ","Sensor_AvgBattery_mJ","Cloud_AvgDelay_s","Fake_AttacksSent"]

    with open(outcsv, 'w', encoding='utf-8') as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r[c]) for c in cols) + "\n")

    print(f"OK: wrote {outcsv} with {len(rows)} rows")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python analyze_results.py <results_dir> <out.csv>")
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
