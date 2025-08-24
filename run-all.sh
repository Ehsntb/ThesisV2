

#!/usr/bin/env bash
# run-all.sh — Build, run, aggregate, and plot OMNeT++ experiments
# Usage examples:
#   ./run-all.sh                          # build + run default set (all) with Cmdenv, aggregate & plot
#   ./run-all.sh --env qtenv --configs Secure5_record   # run a single config with GUI
#   ./run-all.sh --no-build --configs ablation          # skip build, run ablation configs only
#   ./run-all.sh --list                                 # list known configs

set -euo pipefail

### Defaults
BIN="./out/clang-release/LightIoTSimulation"
INI="run_record.ini"
NED=".:ned"
ENV_MODE="Cmdenv"         # Cmdenv | Qtenv
DO_BUILD=1                 # 1=yes, 0=no
DO_AGGREGATE=1             # extract scalars to CSV
DO_PLOTS=1                 # make figures with python if available
CLEAN_RESULTS=0            # remove previous results/* before run
CONFIG_SPEC="all"          # which configs to run (keywords or list)
JOBS=1                     # future: parallel runs (not used for Qtenv)
OMNETPP_ROOT=""           # optional: path to omnetpp-6.1 root; if set, we source $OMNETPP_ROOT/setenv

### Known configs (keep in desired default order)
ALL_CONFIGS=(
  Secure5_record Secure20_record Secure50_record
  NoSec5_record NoSec20_record NoSec50_record
  Attack5_record Attack20_record Attack50_record
  AttackOnNoSec50_record
  Attack50_window3s_record
  Secure50_hmacOnly Secure50_freshOnly Secure50_dupOnly
)

SECURE_CONFIGS=(Secure5_record Secure20_record Secure50_record)
NOSEC_CONFIGS=(NoSec5_record NoSec20_record NoSec50_record)
ATTACK_CONFIGS=(Attack5_record Attack20_record Attack50_record)
SENSITIVITY_CONFIGS=(AttackOnNoSec50_record Attack50_window3s_record)
ABLATION_CONFIGS=(Secure50_hmacOnly Secure50_freshOnly Secure50_dupOnly)

print_help() {
  cat <<EOF
Usage: $0 [options]

Options:
  -e, --env {cmdenv|qtenv}   Select runtime UI (default: cmdenv)
  -c, --configs SPEC          Which configs to run. SPEC can be:
                             all | secure | nosec | attack | sensitivity | ablation
                             or a comma-separated list of config names.
  -b, --build / --no-build    Build the project before running (default: build)
      --aggregate/--no-aggregate  Aggregate results to CSV (default: aggregate)
      --plots/--no-plots      Generate figures with Python (default: plots)
      --clean-results         Remove results/* before running
  -j, --jobs N                (Reserved) parallel jobs for Cmdenv (default: 1)
  -i, --ini FILE              INI file to use (default: run_record.ini)
  -n, --ned PATH              NED path (default: .:ned)
      --omnetpp PATH           OMNeT++ root directory (will source PATH/setenv)
      --bin PATH              Simulation binary (default: $BIN)
  -l, --list                  List known configs and exit
  -h, --help                  Show this help and exit

Examples:
  $0 --env cmdenv --configs all
  $0 --env qtenv  --configs Secure5_record
  $0 --configs ablation --no-plots
EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -e|--env)
      shift; ENV_MODE="${1:-Cmdenv}"; ENV_MODE="${ENV_MODE^^}";;
    -c|--configs)
      shift; CONFIG_SPEC="${1:-all}";;
    -b|--build) DO_BUILD=1;;
    --no-build) DO_BUILD=0;;
    --aggregate) DO_AGGREGATE=1;;
    --no-aggregate) DO_AGGREGATE=0;;
    --plots) DO_PLOTS=1;;
    --no-plots) DO_PLOTS=0;;
    --clean-results) CLEAN_RESULTS=1;;
    -j|--jobs) shift; JOBS="${1:-1}";;
    -i|--ini) shift; INI="${1:-$INI}";;
    -n|--ned) shift; NED="${1:-$NED}";;
    --bin) shift; BIN="${1:-$BIN}";;
    --omnetpp) shift; OMNETPP_ROOT="${1:-}";;
    -l|--list)
      echo "Known configs:"; printf '  %s\n' "${ALL_CONFIGS[@]}"; exit 0;;
    -h|--help) print_help; exit 0;;
    *) echo "[WARN] Unknown option: $1"; print_help; exit 1;;
  esac
  shift
done

# Normalize env
if [[ "$ENV_MODE" == "QTENNV" ]]; then ENV_MODE="Qtenv"; fi
if [[ "$ENV_MODE" == "CMDENV" ]]; then ENV_MODE="Cmdenv"; fi
if [[ "$ENV_MODE" != "Cmdenv" && "$ENV_MODE" != "Qtenv" ]]; then
  echo "[ERR] --env must be cmdenv or qtenv"; exit 1
fi

# Expand config spec into an array CONFIGS
expand_configs() {
  local spec="$1"; local -n OUTARR=$2
  IFS=',' read -r -a toks <<< "$spec"
  OUTARR=()
  for t in "${toks[@]}"; do
    case "${t}" in
      all) OUTARR+=("${ALL_CONFIGS[@]}") ;;
      secure) OUTARR+=("${SECURE_CONFIGS[@]}") ;;
      nosec) OUTARR+=("${NOSEC_CONFIGS[@]}") ;;
      attack) OUTARR+=("${ATTACK_CONFIGS[@]}") ;;
      sensitivity) OUTARR+=("${SENSITIVITY_CONFIGS[@]}") ;;
      ablation) OUTARR+=("${ABLATION_CONFIGS[@]}") ;;
      *) OUTARR+=("${t}") ;;
    esac
  done
  # de-duplicate while preserving order
  local seen=()
  local out=()
  for c in "${OUTARR[@]}"; do
    [[ -z "$c" ]] && continue
    if [[ -z "${seen[$c]+x}" ]]; then out+=("$c"); seen[$c]=1; fi
  done
  OUTARR=("${out[@]}")
}

CONFIGS=()
expand_configs "$CONFIG_SPEC" CONFIGS

ensure_omnetpp_env() {
  # If opp_makemake already available, nothing to do
  if command -v opp_makemake >/dev/null 2>&1; then return; fi

  # Build candidate roots: explicit flag first, then common locations
  local candidates=()
  [[ -n "$OMNETPP_ROOT" ]] && candidates+=("$OMNETPP_ROOT")
  candidates+=(
    "$HOME/omnetpp-6.1"
    "/opt/omnetpp-6.1"
    "/usr/local/omnetpp-6.1"
    "$HOME/omnetpp"
    "/opt/omnetpp"
    "/usr/local/omnetpp"
  )

  for root in "${candidates[@]}"; do
    if [[ -r "$root/setenv" ]]; then
      echo "==> Sourcing OMNeT++ env: $root/setenv"
      # shellcheck source=/dev/null
      source "$root/setenv"
      break
    fi
  done

  if ! command -v opp_makemake >/dev/null 2>&1; then
    echo "[ERR] OMNeT++ environment not loaded. Provide --omnetpp /path/to/omnetpp-6.1 or 'source /path/to/omnetpp-6.1/setenv' before running."
    exit 1
  fi
}

if [[ ${#CONFIGS[@]} -eq 0 ]]; then echo "[ERR] No configs to run"; exit 1; fi

# Build (optional)
if [[ $DO_BUILD -eq 1 ]]; then
  ensure_omnetpp_env
  echo "==> Building project"
  rm -rf out Makefile
  opp_makemake -f --deep -o LightIoTSimulation -O out
  make -j"${JOBS}"
else
  echo "==> Skipping build (use --build to enable)"
  # Even without build, Qtenv or runtime libs may require setenv; source if path provided
  if [[ "$ENV_MODE" == "Qtenv" || -n "$OMNETPP_ROOT" ]]; then
    ensure_omnetpp_env || true
  fi
fi

# Clean results (optional)
if [[ $CLEAN_RESULTS -eq 1 ]]; then
  echo "==> Cleaning results/*"
  rm -rf results
fi
mkdir -p results

# Run configs
echo "==> Running configs (${#CONFIGS[@]}): ${CONFIGS[*]}"
for c in "${CONFIGS[@]}"; do
  echo "\n==== Running $c (env=$ENV_MODE) ===="
  "$BIN" -u "$ENV_MODE" -n "$NED" -f "$INI" -c "$c" || true
  # For Cmdenv we proceed automatically; for Qtenv the user must close GUI per run.
  # We capture only start/end lines to keep output readable.
  echo "==== Done $c ===="
done

# Aggregate scalars to CSV
if [[ $DO_AGGREGATE -eq 1 ]]; then
  echo "==> Aggregating scalars to CSV"
  OUTCSV="results/summary_all_record.csv"
  echo "Config,Nodes,Mode,Cloud_TotalReceived,GW_Received,GW_Forwarded,GW_Dropped,GW_Dropped_HMAC,GW_Dropped_Stale,GW_Dropped_Duplicate,GW_Battery_mJ,Sensor_AvgBattery_mJ,Cloud_AvgDelay_s,Fake_AttacksSent" > "$OUTCSV"

  for CFG in "${CONFIGS[@]}"; do
    # pick newest .sca for this config
    SCA=$(ls -t results/${CFG}-*.sca 2>/dev/null | head -n1 || true)
    if [[ -z "${SCA:-}" ]]; then echo "[WARN] No .sca for $CFG"; continue; fi

    CR=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="Cloud_TotalReceived"{print $4}' "$SCA")
    GR=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_Received"{print $4}' "$SCA")
    GF=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_Forwarded"{print $4}' "$SCA")
    GD=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_Dropped"{print $4}' "$SCA")
    GDH=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_Dropped_HMAC"{print $4}' "$SCA")
    GDS=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_Dropped_Stale"{print $4}' "$SCA")
    GDD=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_Dropped_Duplicate"{print $4}' "$SCA")
    GE=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_BatteryRemaining_mJ"{print $4}' "$SCA")
    AD=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="Cloud_AvgEndToEndDelay_s"{print $4}' "$SCA")
    FA=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="Fake_AttacksSent"{print $4}' "$SCA")
    SB=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="Sensor_BatteryRemaining_mJ"{s+=$4;n++} END{if(n>0)printf "%.4f",s/n}' "$SCA")

    # Derive Nodes and Mode from name
    NODES=""; MODE=""
    if [[ "$CFG" =~ ^Secure([0-9]+)_record$ ]]; then NODES="${BASH_REMATCH[1]}"; MODE="Secure"; fi
    if [[ -z "$NODES" && "$CFG" =~ ^NoSec([0-9]+)_record$ ]]; then NODES="${BASH_REMATCH[1]}"; MODE="NoSec"; fi
    if [[ -z "$NODES" && "$CFG" =~ ^Attack([0-9]+)_record$ ]]; then NODES="${BASH_REMATCH[1]}"; MODE="Attack"; fi
    if [[ "$CFG" == "AttackOnNoSec50_record" ]]; then NODES="50"; MODE="Attack-NoSec"; fi
    if [[ "$CFG" == "Attack50_window3s_record" ]]; then NODES="50"; MODE="Attack-Window3s"; fi
    if [[ "$CFG" == "Secure50_hmacOnly" ]]; then NODES="50"; MODE="Ablation-hmacOnly"; fi
    if [[ "$CFG" == "Secure50_freshOnly" ]]; then NODES="50"; MODE="Ablation-freshOnly"; fi
    if [[ "$CFG" == "Secure50_dupOnly" ]]; then NODES="50"; MODE="Ablation-dupOnly"; fi

    echo "$CFG,$NODES,$MODE,${CR:-},${GR:-},${GF:-},${GD:-},${GDH:-},${GDS:-},${GDD:-},${GE:-},${SB:-},${AD:-},${FA:-}" >> "$OUTCSV"
  done

  # Deduplicate by Config if needed
  awk -F, 'NR==1{print; next} !seen[$1]++' "$OUTCSV" > results/_tmp.csv && mv results/_tmp.csv "$OUTCSV"
  echo "==> Wrote $OUTCSV"
  column -s, -t < "$OUTCSV" | sed -n '1p;/Secure50_/p;/Attack50_/p;/AttackOnNoSec50_record/p;/Attack50_window3s_record/p'
fi

# Plot figures (optional)
if [[ $DO_PLOTS -eq 1 ]]; then
  if python3 -c 'import pandas, matplotlib' >/dev/null 2>&1; then
    echo "==> Generating figures"
    python3 - <<'PY'
import pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
csv = Path("results/summary_all_record.csv")
df = pd.read_csv(csv)
for c in ["Nodes","Cloud_TotalReceived","GW_Received","GW_Forwarded","GW_Dropped","GW_Dropped_HMAC","GW_Dropped_Stale","GW_Dropped_Duplicate","GW_Battery_mJ","Sensor_AvgBattery_mJ","Cloud_AvgDelay_s","Fake_AttacksSent"]:
    if c in df.columns: df[c]=pd.to_numeric(df[c], errors="coerce")

mode_order=["NoSec","Secure","Attack"]; nodes=[5,20,50]
base=df[df["Mode"].isin(mode_order)].copy()
base["Nodes"]=pd.Categorical(base["Nodes"], nodes, ordered=True)
base["Mode"]=pd.Categorical(base["Mode"], mode_order, ordered=True)
base=base.sort_values(["Mode","Nodes"])  
out=Path("results"); out.mkdir(exist_ok=True)

# Delay (ms)
plt.figure()
for m in mode_order:
    s=base[base["Mode"]==m]
    plt.plot(s["Nodes"], s["Cloud_AvgDelay_s"]*1000, marker="o", label=m)
plt.xlabel("Nodes"); plt.ylabel("Avg End-to-End Delay (ms)"); plt.title("Delay vs Nodes (ms)")
plt.legend(); plt.grid(True, linestyle="--", alpha=0.4); plt.tight_layout()
plt.savefig(out/"chart_delay_vs_nodes_ms.png", dpi=160)

# Battery
plt.figure()
for m in mode_order:
    s=base[base["Mode"]==m]
    plt.plot(s["Nodes"], s["GW_Battery_mJ"], marker="o", label=m)
plt.xlabel("Nodes"); plt.ylabel("Gateway Battery Remaining (mJ)"); plt.title("Gateway Battery vs Nodes")
plt.legend(); plt.grid(True, linestyle="--", alpha=0.4); plt.tight_layout()
plt.savefig(out/"chart_gateway_energy_vs_nodes.png", dpi=160)

# Drops
plt.figure()
for m in mode_order:
    s=base[base["Mode"]==m]
    plt.plot(s["Nodes"], s["GW_Dropped"], marker="o", label=m)
plt.xlabel("Nodes"); plt.ylabel("Gateway Drops (count)"); plt.title("Drops vs Nodes")
plt.legend(); plt.grid(True, linestyle="--", alpha=0.4); plt.tight_layout()
plt.savefig(out/"chart_drops_vs_nodes.png", dpi=160)

# Sensitivity (bar)
sens=df[df["Mode"].isin(["Attack-NoSec","Attack-Window3s"])].copy().set_index("Mode")
if not sens.empty:
    def bar(col, ylabel, title, fname, scale=1.0):
        plt.figure(); y=(sens[col]*scale)
        y.plot(kind="bar")
        plt.ylabel(ylabel); plt.title(title)
        for i,v in enumerate(y.values):
            try: v=float(v); plt.text(i, v, f"{v:.3g}", ha="center", va="bottom")
            except: pass
        plt.tight_layout(); plt.savefig(out/fname, dpi=160)
    bar("GW_Dropped", "Drops (count)", "Sensitivity: Drops", "chart_sensitivity_drops.png")
    bar("GW_Battery_mJ", "Gateway Battery (mJ)", "Sensitivity: Battery", "chart_sensitivity_battery.png")
    bar("Cloud_TotalReceived", "Cloud Received (pkts)", "Sensitivity: Cloud Received", "chart_sensitivity_cloud.png")
    bar("Cloud_AvgDelay_s", "Avg Delay (ms)", "Sensitivity: Avg Delay (ms)", "chart_sensitivity_delay_ms.png", scale=1000)

# Ablation (stacked bars of drop causes)
abl = df[df["Mode"].str.contains("Ablation-", na=False)].copy()
if not abl.empty:
    abl = abl.set_index("Mode")[ ["GW_Dropped_HMAC","GW_Dropped_Stale","GW_Dropped_Duplicate"] ]
    abl.plot(kind="bar", stacked=True)
    plt.ylabel("Drops (count)"); plt.title("Ablation (50 nodes): Drop Breakdown")
    plt.tight_layout(); plt.savefig(out/"chart_ablation_drop_breakdown.png", dpi=160)

print("All charts saved.")
PY
  else
    echo "[WARN] Python pandas/matplotlib not available — skipping plots. Install with: pip install pandas matplotlib"
  fi
fi

echo "== DONE =="