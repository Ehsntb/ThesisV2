import os,re,glob,math
import pandas as pd, numpy as np

rows=[]; pat=re.compile(r"results/delay/csv/(?P<cfg>.+?)_s(?P<seed>\d+)\.csv$")
def parse_cfg(s):
    m=re.match(r"(NoSec|Secure|Attack)(\d+)_record", s); return (m.group(1), int(m.group(2))) if m else (None,None)

for p in sorted(glob.glob("results/delay/csv/*.csv")):
    m=pat.match(p)
    if not m: continue
    cfg, seed = m.group("cfg"), int(m.group("seed"))
    scen, N = parse_cfg(cfg)
    if scen is None: continue
    df=pd.read_csv(p)
    col="value" if "value" in df.columns else ("vecvalue" if "vecvalue" in df.columns else None)
    if col is None or df.empty: continue
    vals_ms = df[col].astype(float).to_numpy()*1000.0  # اگر واحدت ثانیه است
    if vals_ms.size==0: continue
    rows.append(dict(config=cfg, scenario=scen, N=N, seed=seed,
                     median_ms=float(np.median(vals_ms)),
                     p95_ms=float(np.percentile(vals_ms,95)),
                     count=int(vals_ms.size)))

by_seed=pd.DataFrame(rows).sort_values(["scenario","N","seed"])
os.makedirs("results", exist_ok=True)
by_seed.to_csv("results/table_4_6_delay_by_run.csv", index=False)

def ci95_med(a, it=6000):
    if len(a)==0: return (math.nan, math.nan)
    rng=np.random.default_rng(12345)
    boots=[np.median(rng.choice(a, size=len(a), replace=True)) for _ in range(it)]
    return (float(np.percentile(boots,2.5)), float(np.percentile(boots,97.5)))

out=[]
for (sc,N), g in by_seed.groupby(["scenario","N"]):
    medv=g["median_ms"].values; p95v=g["p95_ms"].values
    med,(lo_m,hi_m)=float(np.median(medv)),ci95_med(medv)
    p95,(lo_p,hi_p)=float(np.median(p95v)),ci95_med(p95v)
    out.append(dict(scenario=sc, N=int(N),
                    MedianDelay_ms=med, CI95_Median_low_ms=lo_m, CI95_Median_high_ms=hi_m,
                    P95Delay_ms=p95, CI95_P95_low_ms=lo_p, CI95_P95_high_ms=hi_p,
                    runs=int(g["seed"].nunique()), samples=int(g["count"].sum())))

agg=pd.DataFrame(out).sort_values(["N","scenario"])

def dperc(a,b): 
    return float("nan") if (b in (None,0) or (isinstance(b,float) and math.isnan(b))) else 100.0*(a-b)/b

final=[]
for N in sorted(agg["N"].unique()):
    block=agg[agg["N"]==N].set_index("scenario")
    if {"Secure","NoSec"}.issubset(block.index):
        dmed=dperc(block.loc["Secure","MedianDelay_ms"], block.loc["NoSec","MedianDelay_ms"])
        dp95=dperc(block.loc["Secure","P95Delay_ms"],    block.loc["NoSec","P95Delay_ms"])
    else:
        dmed=dp95=float("nan")
    for sc in ["NoSec","Secure","Attack"]:
        if sc in block.index:
            row=block.loc[sc].to_dict(); row["scenario"]=sc
            row["DeltaMedian_Sec_vs_NoSec_percent"]=dmed if sc=="Secure" else float("nan")
            row["DeltaP95_Sec_vs_NoSec_percent"]=dp95 if sc=="Secure" else float("nan")
            final.append(row)

pd.DataFrame(final).sort_values(["N","scenario"]).to_csv("results/table_4_6_delay.csv", index=False)
print("OK -> results/table_4_6_delay.csv | results/table_4_6_delay_by_run.csv")