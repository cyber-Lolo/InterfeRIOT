#!/usr/bin/env bash
# run_triplets.sh
#
# For a given Y position, runs the thickness/refractive-index computation
# in parallel over every consecutive parity triplet:
#   (p-0,p-1,p-2), (p-1,p-2,p-3), (p-2,p-3,p-4), ...
# The number of triplets is auto-detected from how many p-i directories
# exist under <inputdir>/p2w.
#
# Usage:
#   ./run_triplets.sh --input-dir /main/file --Y Y1 [--main-dir /main] \
#                      [--out-dir /main/file/ri] [--jobs 4] \
#                      [--mul-start 0.5] [--mul-stop 1.5] [--mul-step 0.001] \
#                      [--frame-start N] [--frame-end N]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKER="${SCRIPT_DIR}/run_one_triplet.sh"

MAIN_DIR="${PWD}"
INPUTDIR=""
Y=""
OUT_DIR=""
JOBS=4
MUL_START=0.5
MUL_STOP=1.5
MUL_STEP=0.001
FRAME_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --main-dir) MAIN_DIR="$2"; shift 2 ;;
    --input-dir|--inputdir) INPUTDIR="$2"; shift 2 ;;
    --Y) Y="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --jobs) JOBS="$2"; shift 2 ;;
    --mul-start) MUL_START="$2"; shift 2 ;;
    --mul-stop) MUL_STOP="$2"; shift 2 ;;
    --mul-step) MUL_STEP="$2"; shift 2 ;;
    --frame-start) FRAME_ARGS+=(--frame-start "$2"); shift 2 ;;
    --frame-end) FRAME_ARGS+=(--frame-end "$2"); shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$INPUTDIR" || -z "$Y" ]]; then
  echo "Usage: $0 --input-dir DIR --Y Yk [--main-dir DIR] [--out-dir DIR] [--jobs N] [--mul-start F] [--mul-stop F] [--mul-step F] [--frame-start N] [--frame-end N]" >&2
  exit 1
fi

if [[ -z "$OUT_DIR" ]]; then
  OUT_DIR="${INPUTDIR}/ri"
fi

N=$(find "${INPUTDIR}/p2w" -maxdepth 1 -mindepth 1 -type d -name 'p-*' | wc -l)
if (( N < 3 )); then
  echo "Need at least 3 parity directories under ${INPUTDIR}/p2w, found ${N}" >&2
  exit 1
fi
MAX_I=$(( N - 3 ))

mkdir -p "$OUT_DIR"
echo "Running triplets i=0..${MAX_I} for ${Y} with up to ${JOBS} parallel jobs"

export MAIN_DIR INPUTDIR Y OUT_DIR MUL_START MUL_STOP MUL_STEP WORKER
FRAME_ARGS_STR="${FRAME_ARGS[*]:-}"
export FRAME_ARGS_STR

seq 0 "$MAX_I" | xargs -P "$JOBS" -I{} bash -c \
  '"$WORKER" --main-dir "$MAIN_DIR" --input-dir "$INPUTDIR" --idx "$1" --Y "$Y" --out-dir "$OUT_DIR" \
     --mul-start "$MUL_START" --mul-stop "$MUL_STOP" --mul-step "$MUL_STEP" \
     $FRAME_ARGS_STR' _ {}
