#!/usr/bin/env bash
# run_all.sh
#
# Auto-detects all Yk values (from the p-0 measured-data directory) and
# all consecutive parity triplets, then runs every (triplet, Yk) job in
# parallel. Optionally restrict to a Y range and/or a frame range.
#
# Usage:
#   ./run_all.sh --input-dir /main/file [--main-dir /main]
#                 [--out-dir /main/file/ri] [--jobs 8]
#                 [--mul-start 0.5] [--mul-stop 1.5] [--mul-step 0.001]
#                 [--y-start 1] [--y-end 5]
#                 [--frame-start N] [--frame-end N]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKER="${SCRIPT_DIR}/run_one_triplet.sh"

MAIN_DIR="${PWD}"
INPUTDIR=""
OUT_DIR=""
JOBS=8
MUL_START=0.5
MUL_STOP=1.5
MUL_STEP=0.001
Y_START=""
Y_END=""
FRAME_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --main-dir) MAIN_DIR="$2"; shift 2 ;;
    --input-dir|--inputdir) INPUTDIR="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --jobs) JOBS="$2"; shift 2 ;;
    --mul-start) MUL_START="$2"; shift 2 ;;
    --mul-stop) MUL_STOP="$2"; shift 2 ;;
    --mul-step) MUL_STEP="$2"; shift 2 ;;
    --y-start) Y_START="$2"; shift 2 ;;
    --y-end) Y_END="$2"; shift 2 ;;
    --frame-start) FRAME_ARGS+=(--frame-start "$2"); shift 2 ;;
    --frame-end) FRAME_ARGS+=(--frame-end "$2"); shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$INPUTDIR" ]]; then
  echo "Usage: $0 --input-dir DIR [--main-dir DIR] [--out-dir DIR] [--jobs N] [--mul-start F] [--mul-stop F] [--mul-step F] [--y-start N] [--y-end N] [--frame-start N] [--frame-end N]" >&2
  exit 1
fi

if [[ -z "$OUT_DIR" ]]; then
  OUT_DIR="${INPUTDIR}/ri"
fi

# Auto-detect number of parity directories -> triplet range i = 0..N-3
N=$(find "${INPUTDIR}/p2w" -maxdepth 1 -mindepth 1 -type d -name 'p-*' | wc -l)
if (( N < 3 )); then
  echo "Need at least 3 parity directories under ${INPUTDIR}/p2w, found ${N}" >&2
  exit 1
fi
MAX_I=$(( N - 3 ))

# Auto-detect Y values from p-0 filenames like p2w_p-0_1211.csv
Y_LIST_ALL=()
while IFS= read -r path; do
  base=$(basename "$path")
  if [[ "$base" =~ ^p2w_p-0_([0-9]+)\.csv$ ]]; then
    Y_LIST_ALL+=("${BASH_REMATCH[1]}")
  fi
done < <(find "${INPUTDIR}/p2w/p-0" -maxdepth 1 -type f -name 'p2w_p-0*.csv' | sort -V)

if (( ${#Y_LIST_ALL[@]} == 0 )); then
  echo "No Y files found under ${INPUTDIR}/p2w/p-0" >&2
  exit 1
fi

Y_LIST=()
for Yname in "${Y_LIST_ALL[@]}"; do
  if [[ -n ${Y_START:-} ]] && (( 10#$Yname < 10#$Y_START )); then continue; fi
  if [[ -n ${Y_END:-} ]] && (( 10#$Yname > 10#$Y_END )); then continue; fi
  Y_LIST+=("$Yname")
done

if (( ${#Y_LIST[@]} == 0 )); then
  echo "No Y values left after applying --y-start/--y-end filter (available: ${Y_LIST_ALL[*]})" >&2
  exit 1
fi

# Apply --y-start/--y-end (inclusive) filter, comparing the numeric part of Yk
Y_LIST=()
for Yname in "${Y_LIST_ALL[@]}"; do
  num="${Yname#Y}"
  if [[ -n "$Y_START" && "$num" -lt "$Y_START" ]]; then continue; fi
  if [[ -n "$Y_END" && "$num" -gt "$Y_END" ]]; then continue; fi
  Y_LIST+=("$Yname")
done

if (( ${#Y_LIST[@]} == 0 )); then
  echo "No Y values left after applying --y-start/--y-end filter (available: ${Y_LIST_ALL[*]})" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
echo "Using ${#Y_LIST[@]} Y position(s): ${Y_LIST[*]}"
echo "Detected ${N} parity directories -> triplets i=0..${MAX_I}"
echo "Running all (triplet, Y) jobs with up to ${JOBS} parallel workers"

export MAIN_DIR INPUTDIR OUT_DIR MUL_START MUL_STOP MUL_STEP WORKER
FRAME_ARGS_STR="${FRAME_ARGS[*]:-}"
export FRAME_ARGS_STR

# Build the full (idx, Y) job list and run it flattened, so parallelism
# is shared across both dimensions rather than nested.
{
  for Yname in "${Y_LIST[@]}"; do
    for i in $(seq 0 "$MAX_I"); do
      printf '%s\t%s\n' "$i" "$Yname"
    done
  done
} | xargs -P "$JOBS" -L 1 bash -c \
  '"$WORKER" --main-dir "$MAIN_DIR" --input-dir "$INPUTDIR" --idx "$1" --Y "$2" --out-dir "$OUT_DIR" \
     --mul-start "$MUL_START" --mul-stop "$MUL_STOP" --mul-step "$MUL_STEP" \
     $FRAME_ARGS_STR' _
