#!/usr/bin/env python3
import argparse, os, sys, subprocess, shlex, tempfile, csv, re, time
from datetime import datetime

# ---------- تنظیمات پیش‌فرض ----------
OMNET_ROOT_DEFAULT = "/Users/ehsntb/Downloads/omnetpp-6.2.0"
PROJECT_DIR = os.path.abspath(os.getcwd())
SIM = os.path.join(PROJECT_DIR, "out/clang-release/LightIoTSimulation")
INI = "run_record.ini"
NED = ".:ned"
RESULTS = "results"

CORE_CONFIGS = [
    "Secure5_record","Secure20_record","Secure50_record",
    "NoSec5_record","NoSec20_record","NoSec50_record",
    "Attack5_record","Attack20_record","Attack50_record",
]
OTHER_CONFIGS = [
    "AttackOnNoSec50_record","Attack50_window3s_record",
    "Secure50_hmacOnly","Secure50_freshOnly","Secure50_dupOnly",
    "Secure50_bloom","Attack50_bloom",
    "Secure100_record","NoSec100_record","Attack100_record",
    "AttackOnNoSec100_record",
]

def bash(cmd, env_profile=None, cwd=None):
    """run a bash -lc 'cmd', optionally sourcing env_profile first"""
    full = cmd if not env_profile else f"source '{env_profile}'; {cmd}"
    # print("DBG:", full)
    res = subprocess.run(["bash","-lc", full], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if res.returncode != 0:
        print(res.stdout)
        raise SystemExit(f"❌ Command failed: {cmd}")
    return res.stdout

def ensure_env(omnet_root):
    envfile = os.path.join(omnet_root, "setenv")
    if not os.path.isfile(envfile):
        raise SystemExit(f"❌ setenv not found at: {envfile}")
    return envfile

def ensure_build(envfile):
    if not os.path.exists(SIM):
        print("ℹ️ Building project...")
        if os.path.exists(os.path.join(PROJECT_DIR, "Makefile")):
            bash("rm -f Makefile", envfile, PROJECT_DIR)
        bash("rm -rf out", envfile, PROJECT_DIR)
        bash("opp_makemake -f --deep -o LightIoTSimulation -O out", envfile, PROJECT_DIR)
        jobs = os.cpu_count() or 8
        bash(f"make -j{jobs}", envfile, PROJECT_DIR)
    else:
        print("✔️  Build exists:", SIM)

def run_configs(envfile, configs, reps):
    os.makedirs(RESULTS, exist_ok=True)
    for cfg in configs:
        for rep in range(reps):
            scalar = os.path.join(RESULTS, f"{cfg}-rep{rep}.sca")
            vector = os.path.join(RESULTS, f"{cfg}-rep{rep}.vec")
            cmd = (
              f"'{SIM}' -u Cmdenv -n '{NED}' -f '{INI}' -c {cfg} "
              f"--seed-set {rep} "
              f"--output-scalar-file '{scalar}' "
              f"--output-vector-file '{vector}'"
            )
            print(f"→ {cfg} (rep={rep})")
            out = bash(cmd, envfile, PROJECT_DIR)
            # کوچک نگه داشتن خروجی، فقط خط آخر را چاپ می‌کنیم
            last = out.strip().splitlines()[-1] if out.strip().splitlines() else ""
            print("   done.", last)

def find_scavetool(omnet_root):
    # اول از PATH
    for name in ("opp_scavetool","scavetool"):
        path = shutil.which(name)
        if path: return path
    # بعد از omnet_root/bin
    cand = os.path.join(omnet_root,"bin","opp_scavetool")
    if os.path.isfile(cand): return cand
    # آخر: تلاش با opp_run --help (وجود محیط)
    raise SystemExit("❌ opp_scavetool not found. Make sure setenv is sourced from a full OMNeT++ install.")

def export_csvs(envfile, omnet_root):
    # از PATH استفاده نکن؛ مسیر مطمئن باینری را بگیر
    scv = os.path.join(omnet_root,"bin","opp_scavetool")
    if not os.path.isfile(scv):
        raise SystemExit(f"❌ opp_scavetool not found at {scv}")

    # همهٔ فایل‌های تولید شده
    sca_files = sorted([os.path.join(RESULTS,f) for f in os.listdir(RESULTS) if f.endswith(".sca") and "-rep" in f])
    vec_files = sorted([os.path.join(RESULTS,f) for f in os.listdir(RESULTS) if f.endswith(".vec") and "-rep" in f])
    if not sca_files:
        raise SystemExit("❌ No .sca files found under results/. Did the runs complete?")

    scalars_all = os.path.join(RESULTS, "scalars_all.csv")
    vectors_all = os.path.join(RESULTS, "vectors_all.csv")
    # پاک‌سازی خروجی‌های قبلی
    for f in (scalars_all, vectors_all):
        if os.path.exists(f): os.remove(f)

    print("ℹ️ Exporting scalars ->", scalars_all)
    first = True
    for sca in sca_files:
        tmp = os.path.join(RESULTS, "_tmp_scalars.csv")
        cmd = f"'{scv}' export -T s -F CSV-S -o '{tmp}' '{sca}'"
        bash(cmd, envfile, PROJECT_DIR)
        with open(tmp,"r", newline="") as fin, open(scalars_all,"a", newline="") as fout:
            for i,line in enumerate(fin):
                if not first and i==0: continue  # skip header
                fout.write(line)
        os.remove(tmp)
        first = False

    print("ℹ️ Exporting vectors ->", vectors_all)
    # نگاشت sca->vec با نام پایه
    base2vec = {os.path.splitext(os.path.basename(v))[0]: v for v in vec_files}
    first = True
    for sca in sca_files:
        base = os.path.splitext(os.path.basename(sca))[0]
        vec = base2vec.get(base)
        if not vec:
            print(f"⚠️  missing .vec for {sca}, skipping vector export")
            continue
        tmp = os.path.join(RESULTS, "_tmp_vectors.csv")
        cmd = f"'{scv}' export -T v -F CSV-R -o '{tmp}' '{sca}' '{vec}'"
        bash(cmd, envfile, PROJECT_DIR)
        with open(tmp,"r", newline="") as fin, open(vectors_all,"a", newline="") as fout:
            for i,line in enumerate(fin):
                if not first and i==0: continue  # skip header
                fout.write(line)
        os.remove(tmp)
        first = False

    print("✔️  CSVs written.")

def analyze_summary():
    try:
        import pandas as pd
        import numpy as np
        import re
    except ImportError:
        print("❌ pandas/numpy not installed. Run:  pip install pandas numpy")
        return

    scalars = os.path.join(RESULTS, "scalars_all.csv")
    vectors = os.path.join(RESULTS, "vectors_all.csv")
    if not os.path.isfile(scalars):
        print("❌ scalars_all.csv not found.")
        return

    # --- خواندن اسکالرها (CSV-S: ستون 'type' ندارد) ---
    df_s = pd.read_csv(scalars)  # expected columns: run,module,name,attrname,attrvalue,value
    def split_run(r):
        m = re.match(r"(.+?)-(\d+)-", str(r))
        if m:
            return m.group(1), int(m.group(2))
        return str(r), -1
    df_s[['config','rep']] = df_s['run'].apply(lambda r: pd.Series(split_run(r)))

    # اگر چند مقدار با نام یکسان از ماژول‌های مختلف داریم، میانگین بگیریم
    g = df_s.groupby(['run','config','rep','name'], as_index=False)['value'].mean()
    piv = g.pivot_table(index=['run','config','rep'], columns='name', values='value', aggfunc='mean').reset_index()

    # --- بردار تاخیر سرتاسری از vectors_all.csv (اگه موجود بود) ---
    mean_vec = None
    if os.path.isfile(vectors):
        v = pd.read_csv(vectors)
        # vectors_all.csv معمولاً ستون 'type' دارد، ولی اگر نداشت، ادامه می‌دهیم
        if 'type' in v.columns:
            v = v[v['type'].astype(str).str.lower()=='vector'].copy()
        v[['config','rep']] = v['run'].apply(lambda r: pd.Series(split_run(r)))
        v = v[v['name'].astype(str) == 'EndToEndDelay_s'].copy()

        def avg_series_to_float(series):
            s = " ".join(map(str, series))
            vals = [float(x) for x in s.split()] if s else []
            return float(np.mean(vals)) if vals else np.nan

        mean_vec = v.groupby(['run','config','rep'], as_index=False)['vecvalue'] \
                    .apply(avg_series_to_float) \
                    .rename(columns={'vecvalue':'mean_EndToEndDelay_s'})

    final = piv
    if mean_vec is not None:
        final = final.merge(mean_vec, on=['run','config','rep'], how='left')

    # ترتیب ستون‌ها
    order = ['config','rep','GW_Received','GW_Forwarded','GW_Dropped','GW_Dropped_HMAC','GW_Dropped_Stale','GW_Dropped_Duplicate',
             'Cloud_TotalReceived','Cloud_AvgDelay_s','mean_EndToEndDelay_s','GW_BatteryRemaining_mJ','Sensor_EnergyRemaining_mJ','run']
    cols = [c for c in order if c in final.columns] + [c for c in final.columns if c not in order]
    final = final[cols]

    out = os.path.join(RESULTS, "summary_by_run.csv")
    final.to_csv(out, index=False)
    print(f"📄 Wrote {out}  (rows={len(final)})")

    
def main():
    ap = argparse.ArgumentParser(description="Run OMNeT++ configs, export CSV, and summarize results.")
    ap.add_argument("--omnet-root", default=OMNET_ROOT_DEFAULT, help="Path to omnetpp-6.2.0")
    ap.add_argument("--set", default="core", choices=["core","all","custom"], help="Which config set to run")
    ap.add_argument("--configs", nargs="*", default=[], help="Used with --set custom")
    ap.add_argument("--reps", type=int, default=3, help="Repetitions per config")
    args = ap.parse_args()

    envfile = ensure_env(args.omnet_root)
    ensure_build(envfile)

    if args.set == "core":
        configs = CORE_CONFIGS
    elif args.set == "all":
        configs = CORE_CONFIGS + OTHER_CONFIGS
    else:
        if not args.configs:
            raise SystemExit("❌ --set custom needs --configs cfg1 cfg2 ...")
        configs = args.configs

    run_configs(envfile, configs, args.reps)
    export_csvs(envfile, args.omnet_root)
    analyze_summary()
    print("✅ Done.")

if __name__ == "__main__":
    import shutil
    main()
