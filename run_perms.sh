#!/usr/bin/env bash
set -euo pipefail
BIN=./out/clang-release/LightIoTSimulation
mkdir -p results

run_perm() {
  local cfg="$1" ord="$2" id
  case "$ord" in
    HFB) id=1 ;;
    HBF) id=2 ;;
    FHB) id=3 ;;
    FBH) id=4 ;;
    BHF) id=5 ;;
    BFH) id=6 ;;
    *) echo "bad order: $ord" >&2; exit 1 ;;
  esac

  "$BIN" -u Cmdenv -n .:ned -f run_record.ini -c "$cfg" -r 0 \
    --record-eventlog=false \
    --output-scalar-file="results/perms_${cfg}_${ord}.sca" \
    --output-vector-file="results/perms_${cfg}_${ord}.vec" \
    --"**.scalar-recording"=true \
    --"**.vector-recording"=true \
    --"**.result-recording-modes"=all \
    --"**.gateway.stageOrderId"="$id" \
    --"**.gateway.batteryInit_mJ"=10000000
}

for ord in HFB HBF FHB FBH BHF BFH; do run_perm Secure50_bloom "$ord"; done
for ord in HFB HBF FHB FBH BHF BFH; do run_perm Attack50_bloom "$ord"; done
