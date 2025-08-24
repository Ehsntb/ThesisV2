

#!/usr/bin/env bash
# run-ci.sh — Multi-seed CI runs (95% CI) for key configs
set -euo pipefail

# Defaults
BIN="./out/clang-release/LightIoTSimulation"
INI="run_record.ini"
NED=".:ned"
ENV_MODE="Cmdenv"   # Cmdenv | Qtenv (CI توصیه می‌شود Cmdenv)
OMNETPP_ROOT=""     # --omnetpp /path/to/omnetpp-6.1 (to source setenv)
DO_BUILD=1
CONFIG_SPEC="all"   # all | ci50 | ci100 | comma-separated list

ALL_CI=(Secure50_CI NoSec50_CI Attack50_CI Secure100_CI NoSec100_CI Attack100_CI)
CI50=(Secure50_CI NoSec50_CI Attack50_CI)
CI100=(Secure100_CI NoSec100_CI Attack100_CI)

print_help(){ cat <<EOF
Usage: $0 [options]
  --env {cmdenv|qtenv}      Runtime UI (default: cmdenv)
  --configs SPEC            all | ci50 | ci100 | comma-separated list of *_CI
  --build / --no-build      Build project (default: build)
  --omnetpp PATH            OMNeT++ root; will source PATH/setenv
  --ini FILE                INI file (default: run_record.ini)
  --ned PATH                NED path (default: .:ned)
  --bin PATH                Binary (default: $BIN)
  --list                    List CI configs and exit
  -h, --help                Show help
Examples:
  $0 --configs all --omnetpp /home/ubuntu/Omnet++/omnetpp-6.1
  $0 --configs ci50 --no-build
EOF
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env) shift; ENV_MODE="${1:-Cmdenv}"; ENV_MODE="${ENV_MODE^^}";;
    --configs) shift; CONFIG_SPEC="${1:-all}";;
    --build) DO_BUILD=1;;
    --no-build) DO_BUILD=0;;
    --omnetpp) shift; OMNETPP_ROOT="${1:-}";;
    --ini) shift; INI="${1:-$INI}";;
    --ned) shift; NED="${1:-$NED}";;
    --bin) shift; BIN="${1:-$BIN}";;
    --list) printf '%s\n' "${ALL_CI[@]}"; exit 0;;
    -h|--help) print_help; exit 0;;
    *) echo "[ERR] Unknown option $1"; print_help; exit 1;;
  esac; shift
done

# Normalize env
[[ "$ENV_MODE" == "QTENNV" ]] && ENV_MODE="Qtenv"
[[ "$ENV_MODE" == "CMDENV" ]] && ENV_MODE="Cmdenv"

ensure_omnetpp_env(){
  if command -v opp_makemake >/dev/null 2>&1; then return; fi
  local candidates=()
  [[ -n "$OMNETPP_ROOT" ]] && candidates+=("$OMNETPP_ROOT")
  candidates+=("$HOME/omnetpp-6.1" "/opt/omnetpp-6.1" "/usr/local/omnetpp-6.1" "$HOME/omnetpp" "/opt/omnetpp" "/usr/local/omnetpp")
  for root in "${candidates[@]}"; do
    if [[ -r "$root/setenv" ]]; then echo "==> Sourcing $root/setenv"; source "$root/setenv"; break; fi
  done
  command -v opp_makemake >/dev/null 2>&1 || { echo "[ERR] OMNeT++ not loaded; use --omnetpp"; exit 1; }
}

expand_configs(){
  local spec="$1"; local -n out=$2; out=(); IFS=',' read -r -a toks <<< "$spec"
  for t in "${toks[@]}"; do
    case "$t" in
      all) out+=("${ALL_CI[@]}");;
      ci50) out+=("${CI50[@]}");;
      ci100) out+=("${CI100[@]}");;
      *) out+=("$t");;
    esac
  done
  # dedup
  local seen=(); local tmp=(); for c in "${out[@]}"; do [[ -z "${seen[$c]+x}" ]] && tmp+=("$c") && seen[$c]=1; done; out=("${tmp[@]}")
}

CONFIGS=(); expand_configs "$CONFIG_SPEC" CONFIGS
[[ ${#CONFIGS[@]} -gt 0 ]] || { echo "[ERR] No configs"; exit 1; }

# Build
if [[ $DO_BUILD -eq 1 ]]; then
  ensure_omnetpp_env
  echo "==> Building"
  rm -rf out Makefile
  opp_makemake -f --deep -o LightIoTSimulation -O out
  make -j"$(nproc)"
else
  # Still ensure runtime env for Qtenv
  [[ "$ENV_MODE" == "Qtenv" || -n "$OMNETPP_ROOT" ]] && ensure_omnetpp_env || true
fi

mkdir -p results

# Run
echo "==> CI Runs: ${CONFIGS[*]} (env=$ENV_MODE)"
for c in "${CONFIGS[@]}"; do
  echo "\n==== Running $c ===="
  "$BIN" -u "$ENV_MODE" -n "$NED" -f "$INI" -c "$c" || true
  echo "==== Done $c ===="
done

# Analyze
echo "==> Analyzing CI results"
python3 scripts/analyze_ci.py --configs "${CONFIGS[*]}" --out results/ci_summary.csv || {
  echo "[WARN] analyze_ci.py failed (missing pandas?) — install with: pip install pandas numpy"; exit 1; }

column -s, -t < results/ci_summary.csv | sed -n '1p;/Secure50_CI/p;/NoSec50_CI/p;/Attack50_CI/p;/Secure100_CI/p;/NoSec100_CI/p;/Attack100_CI/p'

echo "== DONE =="