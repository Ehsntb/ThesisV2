#!/usr/bin/env python3
import sys, re, os, csv, argparse

SCALAR_RE = re.compile(r'^scalar\s+(\S+)\s+(\S+)\s+([-+0-9.eE]+)')

def parse_sca(path):
    rows = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            m = SCALAR_RE.match(line.strip())
            if not m:
                continue
            module, name, val = m.group(1), m.group(2), float(m.group(3))
            rows.append((module, name, val))
    return rows

def infer_config_meta(filename):
    base = os.path.basename(filename)
    cfg = base.split('-')[0] if '-' in base else os.path.splitext(base)[0]
    mode, nodes = None, None
    m = re.match(r'([A-Za-z]+)(\d+)_record', cfg)
    if m:
        mode = m.group(1)
        nodes = int(m.group(2))
    else:
        mode = cfg
        nodes = None
    return cfg, mode, nodes

def main(argv):
    ap = argparse.ArgumentParser(description="Summarize OMNeT++ .sca scalars into a CSV.")
    ap.add_argument("results_dir", help="Path to results directory containing .sca files")
    ap.add_argument("out_csv", help="Output CSV path")
    args = ap.parse_args(argv)

    records = []
    for fname in sorted(os.listdir(args.results_dir)):
        if not fname.endswith(".sca"):
            continue
        sca_path = os.path.join(args.results_dir, fname)
        cfg, mode, nodes = infer_config_meta(fname)
        scalars = parse_sca(sca_path)

        agg = {
            "Config": cfg, "Mode": mode, "Nodes": nodes,
            "Cloud_TotalReceived": 0.0, "Cloud_AvgDelay_s": 0.0,
            "GW_Received": 0.0, "GW_Forwarded": 0.0, "GW_Dropped": 0.0,
            "GW_Dropped_HMAC": 0.0, "GW_Dropped_Stale": 0.0, "GW_Dropped_Duplicate": 0.0,
            "GW_Battery_mJ": 0.0, "Sensor_AvgBattery_mJ": 0.0, "Fake_AttacksSent": 0.0,
        }

        sensor_energies = []

        for module, name, val in scalars:
            # Cloud
            if module.endswith(".cloud") or module.endswith("CloudServer") or module.endswith("cloud"):
                if name == "Cloud_TotalReceived": agg["Cloud_TotalReceived"] = val
                elif name == "Cloud_AvgDelay_s": agg["Cloud_AvgDelay_s"] = val

            # Gateway
            if ".gateway" in module or module.endswith("gateway") or "GatewayNode" in module:
                if name == "GW_Received": agg["GW_Received"] = val
                elif name == "GW_Forwarded": agg["GW_Forwarded"] = val
                elif name == "GW_Dropped": agg["GW_Dropped"] = val
                elif name == "GW_Dropped_HMAC": agg["GW_Dropped_HMAC"] = val
                elif name == "GW_Dropped_Stale": agg["GW_Dropped_Stale"] = val
                elif name == "GW_Dropped_Duplicate": agg["GW_Dropped_Duplicate"] = val
                elif name == "GW_BatteryRemaining_mJ": agg["GW_Battery_mJ"] = val

            # Sensors
            if ".sensor[" in module or "SensorNode" in module:
                if name == "Sensor_EnergyRemaining_mJ":
                    sensor_energies.append(val)

            # FakeNode
            if ".fakeNode" in module or "FakeNode" in module:
                if name == "Fake_AttacksSent":
                    agg["Fake_AttacksSent"] = val

        if sensor_energies:
            agg["Sensor_AvgBattery_mJ"] = sum(sensor_energies) / len(sensor_energies)

        records.append(agg)

    fieldnames = [
        "Config","Nodes","Mode",
        "Cloud_TotalReceived","GW_Received","GW_Forwarded","GW_Dropped",
        "GW_Dropped_HMAC","GW_Dropped_Stale","GW_Dropped_Duplicate",
        "GW_Battery_mJ","Sensor_AvgBattery_mJ","Cloud_AvgDelay_s","Fake_AttacksSent"
    ]
    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        import csv
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in sorted(records, key=lambda x:(x.get("Mode",""), x.get("Nodes",0))):
            w.writerow(r)

    print(f"OK: wrote {args.out_csv} with {len(records)} rows")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))