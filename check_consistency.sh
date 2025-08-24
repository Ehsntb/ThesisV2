


#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob
OK=0; FAIL=0
for SCA in results/*.sca; do
  CFG=$(basename "$SCA" | sed 's/-[0-9][0-9]*\.sca$//')
  GR=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_Received"{print $4}' "$SCA")
  GF=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_Forwarded"{print $4}' "$SCA")
  GD=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_Dropped"{print $4}' "$SCA")
  CR=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="Cloud_TotalReceived"{print $4}' "$SCA")
  GE=$(awk 'BEGIN{FS="[ \t]+"} $1=="scalar"&&$3=="GW_BatteryRemaining_mJ"{print $4}' "$SCA")
  ERR=0
  [[ "$GF" == "$CR" ]] || { echo "[FAIL][$CFG] GW_Forwarded=$GF != Cloud_TotalReceived=$CR"; ERR=1; }
  [[ $((GR)) -eq $((GF + GD)) ]] || { echo "[FAIL][$CFG] GW_Received=$GR != Forwarded+Dropped=$((GF+GD))"; ERR=1; }
  awk -v ge="$GE" 'BEGIN{if (!(ge>=-1e-6 && ge<=5000+1e-6)) {exit 1}}' || { echo "[FAIL][$CFG] GW_Battery out of [0,5000]: $GE"; ERR=1; }
  if [[ $ERR -eq 0 ]]; then echo "[OK]   $CFG"; ((OK++)); else ((FAIL++)); fi
done
echo "SUMMARY: OK=$OK FAIL=$FAIL"
[[ $FAIL -eq 0 ]] || exit 1