#!/bin/bash
# usage: bash run_parallel.sh <name> <max_jobs>
NAME=$1
START=$2
END=$3
MAX_JOBS=${4:-18}

seq "$START" "$END" \
  | xargs -P "$MAX_JOBS" -I {} python3 p2w.py "$NAME" {}