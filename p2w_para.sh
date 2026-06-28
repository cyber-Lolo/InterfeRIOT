#!/bin/bash
# bash p2w_para.sh run 1 3800 18 5
set -euo pipefail

NAME=$1
START=$2
END=$3
MAX_JOBS=${4:-18}
N_LABELS=${5:-5}

mkdir -p "$NAME/p2w"

for ((label=0; label<N_LABELS; label++)); do
    mkdir -p "$NAME/p2w/p-$label"
done

seq "$START" "$END" \
  | xargs -P "$MAX_JOBS" -I {} python3 p2w.py "$NAME" {}