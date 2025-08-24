


#!/usr/bin/env bash
set -euo pipefail
BIN="./out/clang-release/LightIoTSimulation"
INI="run_record.ini"
NED=".:ned"
ENV_MODE="Cmdenv"
OMNETPP_ROOT="${1:-/home/ubuntu/Omnet++/omnetpp-6.1}"

# Ensure env
if ! command -v opp_makemake >/dev/null 2>&1; then
  if [[ -r "$OMNETPP_ROOT/setenv" ]]; then source "$OMNETPP_ROOT/setenv"; else echo "[ERR] setenv not found"; exit 1; fi
fi

# Build
rm -rf out Makefile
opp_makemake -f --deep -o LightIoTSimulation -O out
make -j"$(nproc)"

# Runs
"$BIN" -u "$ENV_MODE" -n "$NED" -f "$INI" -c Secure50_bloom
"$BIN" -u "$ENV_MODE" -n "$NED" -f "$INI" -c Secure100_bloom
"$BIN" -u "$ENV_MODE" -n "$NED" -f "$INI" -c Attack50_bloom