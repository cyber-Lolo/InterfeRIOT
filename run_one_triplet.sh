#!/usr/bin/env bash
# run_one_triplet.sh
# Worker invoked by xargs: runs one (idx, Y) job.
#
# Usage:
#   run_one_triplet.sh --input-dir DIR --idx I --Y Yk [--main-dir DIR] [--out-dir DIR] \
#     [--mul-start F] [--mul-stop F] [--mul-step F] \
#     [--frame-start N] [--frame-end N]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/ri_ot.py"

MAIN_DIR="${PWD}"
INPUTDIR=""
IDX=""
Y=""
OUT_DIR=""
MUL_START=0.5
MUL_STOP=1.5
MUL_STEP=0.001
FRAME_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --main-dir) MAIN_DIR="$2"; shift 2 ;;
    --input-dir|--inputdir) INPUTDIR="$2"; shift 2 ;;
    --idx) IDX="$2"; shift 2 ;;
    --Y) Y="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --mul-start) MUL_START="$2"; shift 2 ;;
    --mul-stop) MUL_STOP="$2"; shift 2 ;;
    --mul-step) MUL_STEP="$2"; shift 2 ;;
    --frame-start) FRAME_ARGS+=(--frame-start "$2"); shift 2 ;;
    --frame-end) FRAME_ARGS+=(--frame-end "$2"); shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$INPUTDIR" || -z "$IDX" || -z "$Y" ]]; then
  echo "Usage: $0 --input-dir DIR --idx I --Y Yk [--main-dir DIR] [--out-dir DIR] [--mul-start F] [--mul-stop F] [--mul-step F] [--frame-start N] [--frame-end N]" >&2
  exit 1
fi

if [[ -z "$OUT_DIR" ]]; then
  OUT_DIR="${INPUTDIR}/ri"
fi

I2=$((IDX + 1))
OUT_PATH="${OUT_DIR}/p-${IDX}_p-${I2}/ri_p-${IDX}_p-${I2}_${Y}.csv"

python3 "$PY_SCRIPT" \
  --main-dir "$MAIN_DIR" \
  --inputdir "$INPUTDIR" \
  --idx "$IDX" \
  --Y "$Y" \
  --mul-start "$MUL_START" \
  --mul-stop "$MUL_STOP" \
  --mul-step "$MUL_STEP" \
  "${FRAME_ARGS[@]}" \
  --out "$OUT_PATH"
