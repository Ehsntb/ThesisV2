

#!/usr/bin/env bash
# run-sweeps.sh — parameter sweeps (freshness window & replay interval)
set -euo pipefail
BIN="./out/clang-release/LightIoTSimulation"
INI="run_sweep.ini"
NED=".:ned"
ENV_MODE="Cmdenv"
OMNETPP_ROOT=""
DO_BUILD=1
SPEC="all"  # all | window | replay | comma-separated list

WIN_CFGS=(Attack50_win0p5 Attack50_win1 Attack50_win2 Attack50_win3 Attack50_win5)
REP_CFGS=(Attack50_replay0p5 Attack50_replay1 Attack50_replay2p5)
ALL_CFGS=("${WIN_CFGS[@]}" "${REP_CFGS[@]}")

print_help(){ cat <<EOF
Usage: $0 [options]
  --env {cmdenv|qtenv}   Runtime UI (default: cmdenv)
  --configs SPEC         all | window | replay | comma-separated list
  --build/--no-build     Build (default: build)
  --omnetpp PATH         OMNeT++ root (source PATH/setenv)
  --ini FILE             INI file (default: run_sweep.ini)
  --ned PATH             NED path (default: .:ned)
  --bin PATH             Binary path
  --list                 List known sweep configs and exit
  -h, --help             Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env) shift; ENV_MODE="${1:-Cmdenv}"; ENV_MODE="${ENV_MODE^^}";;
    --configs) shift; SPEC="${1:-all}";;
    --build) DO_BUILD=1;;
    --no-build) DO_BUILD=0;;
    --omnetpp) shift; OMNETPP_ROOT="${1:-}";;
    --ini) shift; INI="${1:-$INI}";;
    --ned) shift; NED="${1:-$NED}";;
    --bin) shift; BIN="${1:-$BIN}";;
    --list) printf '%s\n' "${ALL_CFGS[@]}"; exit 0;;
    -h|--help) print_help; exit 0;;
    *) echo "[ERR] Unknown option $1"; print_help; exit 1;;
  esac; shift
done

[[ "$ENV_MODE" == "QTENNV" ]] && ENV_MODE="Qtenv"; [[ "$ENV_MODE" == "CMDENV" ]] && ENV_MODE="Cmdenv"

ensure(){
  if command -v opp_makemake >/dev/null 2>&1; then return; fi
  local c=("$OMNETPP_ROOT" "$HOME/omnetpp-6.1" "/opt/omnetpp-6.1" "/usr/local/omnetpp-6.1")
  for r in "${c[@]}"; do [[ -r "$r/setenv" ]] && { echo "==> Sourcing $r/setenv"; source "$r/setenv"; break; }; done
  command -v opp_makemake >/dev/null 2>&1 || { echo "[ERR] OMNeT++ env missing"; exit 1; }
}

expand(){ local spec="$1"; local -n out=$2; out=(); IFS=',' read -r -a t <<< "$spec"; for s in "${t[@]}"; do case "$s" in all) out+=("${ALL_CFGS[@]}");; window) out+=("${WIN_CFGS[@]}");; replay) out+=("${REP_CFGS[@]}");; *) out+=("$s");; esac; done; }

CFG=(); expand "$SPEC" CFG
[[ ${#CFG[@]} -gt 0 ]] || { echo "[ERR] No sweep configs"; exit 1; }

if [[ $DO_BUILD -eq 1 ]]; then
  ensure; echo "==> Building"; rm -rf out Makefile; opp_makemake -f --deep -o LightIoTSimulation -O out; make -j"$(nproc)"
else
  [[ "$ENV_MODE" == "Qtenv" || -n "$OMNETPP_ROOT" ]] && ensure || true
fi

mkdir -p results

echo "==> Running sweeps: ${CFG[*]}"
for c in "${CFG[@]}"; do
  echo "==== $c ===="
  "$BIN" -u "$ENV_MODE" -n "$NED" -f "$INI" -c "$c" || true
  echo "==== done $c ===="
fi

OUTCSV="results/summary_sweeps.csv"
echo "Config,Nodes,Mode,Window_s,ReplayInterval_s,Cloud_TotalReceived,GW_Received,GW_Forwarded,GW_Dropped,GW_Battery_mJ,Sensor_AvgBattery_mJ,Cloud_AvgDelay_s,Fake_AttacksSent" > "$OUTCSV"

for CFGNAME in "${CFG[@]}"; do
  SCA=$(ls -t results/${CFGNAME}-*.sca 2>/dev/null | head -n1 || true); [[ -z "$SCA" ]] && { echo "[WARN] no sca for $CFGNAME"; continue; }
  CR=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="Cloud_TotalReceived"{print $4}' "$SCA")
  GR=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_Received"{print $4}' "$SCA")
  GF=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_Forwarded"{print $4}' "$SCA")
  GD=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_Dropped"{print $4}' "$SCA")
  GE=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_BatteryRemaining_mJ"{print $4}' "$SCA")
  AD=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="Cloud_AvgEndToEndDelay_s"{print $4}' "$SCA")
  FA=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="Fake_AttacksSent"{print $4}' "$SCA")
  SB=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="Sensor_BatteryRemaining_mJ"{s+=$4;n++} END{if(n>0)printf "%.4f",s/n}' "$SCA")
  NODES="50"; MODE="Attack"
  WIN=""; REP=""
  if [[ "$CFGNAME" =~ ^Attack50_win([0-9p]+)$ ]]; then WIN=${BASH_REMATCH[1]//p/.}; fi
  if [[ "$CFGNAME" =~ ^Attack50_replay([0-9p]+)$ ]]; then REP=${BASH_REMATCH[1]//p/.}; fi
  echo "$CFGNAME,$NODES,$MODE,${WIN:-},${REP:-},${CR:-},${GR:-},${GF:-},${GD:-},${GE:-},${SB:-},${AD:-},${FA:-}" >> "$OUTCSV"
done

# Plot
python3 scripts/plot_sweeps.py results/summary_sweeps.csv || echo "[WARN] plotting skipped (missing pandas/matplotlib?)"

echo "== DONE =="