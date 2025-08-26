#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# --- OMNeT++ env detection ---
if [[ -z "${OMNETPP_ROOT:-}" ]]; then
  for guess in "$HOME/Omnet++/omnetpp-6.1" "/opt/omnetpp-6.1" ; do
    if [[ -f "$guess/setenv" ]]; then
      # shellcheck disable=SC1090
      source "$guess/setenv"
      break
    fi
  done
fi
if [[ -z "${OMNETPP_ROOT:-}" ]]; then
  echo "WARNING: OMNeT++ env not loaded. If build fails, run:"
  echo "  source /path/to/omnetpp-6.1/setenv"
fi

ensure_build() {
  if [[ ! -x out/clang-release/LightIoTSimulation ]]; then
    echo "==> Building project..."
    rm -rf out Makefile
    opp_makemake -f --deep -o LightIoTSimulation -O out -e cc
    make -j"$(nproc)"
  fi
}

choose_ui() {
  echo "Select UI:"
  select ui in "Cmdenv (Terminal)" "Qtenv (GUI)"; do
    case $REPLY in
      1) UI="Cmdenv"; break ;;
      2) UI="Qtenv"; break ;;
      *) echo "Invalid";;
    esac
  done
}

choose_group() {
  echo "Select scenario group:"
  select g in "Secure" "NoSec" "Attack" "All"; do
    case $REPLY in
      1) GROUP="Secure"; break ;;
      2) GROUP="NoSec"; break ;;
      3) GROUP="Attack"; break ;;
      4) GROUP="All"; break ;;
      *) echo "Invalid";;
    esac
  done
}

choose_nodes() {
  echo "Select node count:"
  select n in "5" "20" "50" "all"; do
    case $REPLY in
      1) NODES=(5); break ;;
      2) NODES=(20); break ;;
      3) NODES=(50); break ;;
      4) NODES=(5 20 50); break ;;
      *) echo "Invalid";;
    esac
  done
}

run_config() {
  local cfg="$1" ui="$2"
  echo; echo "==> Running $cfg with -u $ui"
  ./out/clang-release/LightIoTSimulation -u "$ui" -n . -f run_record.ini -c "$cfg"
}

main() {
  choose_ui
  choose_group
  choose_nodes
  ensure_build
  mkdir -p results

  declare -a CONFIGS=()
  for nn in "${NODES[@]}"; do
    case "$GROUP" in
      Secure) CONFIGS+=("Secure${nn}_record");;
      NoSec)  CONFIGS+=("NoSec${nn}_record");;
      Attack) CONFIGS+=("Attack${nn}_record");;
      All)    CONFIGS+=("Secure${nn}_record" "NoSec${nn}_record" "Attack${nn}_record");;
    esac
  done

  for cfg in "${CONFIGS[@]}"; do
    run_config "$cfg" "$UI"
  done

  echo; echo "==> Done. See ./results/"
}
main "$@"
