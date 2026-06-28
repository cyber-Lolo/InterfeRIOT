#!/usr/bin/env bash
# run_all.sh
#
# Launch all consecutive fringe-pair + frame jobs for the per-frame layout.
#
# Usage:
#   ./run_all.sh --input-dir DIR [--main-dir DIR] [--out-dir DIR] [--jobs N]
#                [--mul-start F] [--mul-stop F] [--mul-step F]
#                [--max-fringe N]
#                [--frame-start N] [--frame-end N]
#
# --max-fringe N means: use measured folders p-0 through p-N inclusive.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/ri_ot.py"

MAIN_DIR="${PWD}"
INPUTDIR=""
OUT_DIR=""
JOBS=8
MUL_START=0.5
MUL_STOP=1.5
MUL_STEP=0.001
MAX_FRINGE=""
FRAME_START=""
FRAME_END=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --main-dir) MAIN_DIR="$2"; shift 2 ;;
    --input-dir|--inputdir) INPUTDIR="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --jobs) JOBS="$2"; shift 2 ;;
    --mul-start) MUL_START="$2"; shift 2 ;;
    --mul-stop) MUL_STOP="$2"; shift 2 ;;
    --mul-step) MUL_STEP="$2"; shift 2 ;;
    --max-fringe) MAX_FRINGE="$2"; shift 2 ;;
    --frame-start) FRAME_START="$2"; shift 2 ;;
    --frame-end) FRAME_END="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$INPUTDIR" ]]; then
  echo "Usage: $0 --input-dir DIR [--main-dir DIR] [--out-dir DIR] [--jobs N] [--mul-start F] [--mul-stop F] [--mul-step F] [--max-fringe N] [--frame-start N] [--frame-end N]" >&2
  exit 1
fi

if [[ -z "$OUT_DIR" ]]; then
  OUT_DIR="${INPUTDIR}/ri"
fi

P2W_DIR="${INPUTDIR}/p2w"
if [[ ! -d "$P2W_DIR" ]]; then
  echo "Missing directory: $P2W_DIR" >&2
  exit 1
fi

N=$(find "$P2W_DIR" -maxdepth 1 -mindepth 1 -type d -name 'p-*' | wc -l | tr -d ' ')
if (( N < 2 )); then
  echo "Need at least 2 fringe directories under $P2W_DIR, found $N" >&2
  exit 1
fi

if [[ -n "$MAX_FRINGE" ]]; then
  if (( MAX_FRINGE < 1 )); then
    echo "--max-fringe must be >= 1" >&2
    exit 1
  fi
  if (( MAX_FRINGE >= N )); then
    echo "--max-fringe=${MAX_FRINGE} but only p-0..p-$((N-1)) exist" >&2
    exit 1
  fi
  MAX_I=$((MAX_FRINGE - 1))
else
  MAX_I=$((N - 2))
fi

FRAMES=()
while IFS= read -r path; do
  base="${path##*/}"
  if [[ "$base" =~ ^p2w_p-0_([0-9]+)\.csv$ ]]; then
    frame="${BASH_REMATCH[1]}"
    if [[ -n "$FRAME_START" ]] && (( 10#$frame < 10#$FRAME_START )); then
      continue
    fi
    if [[ -n "$FRAME_END" ]] && (( 10#$frame > 10#$FRAME_END )); then
      continue
    fi
    FRAMES+=("$frame")
  fi
done < <(find "$P2W_DIR/p-0" -maxdepth 1 -type f -name 'p2w_p-0_*.csv' | sort)

if (( ${#FRAMES[@]} == 0 )); then
  echo "No frames found under $P2W_DIR/p-0 after applying frame filters." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
for ((i=0; i<=MAX_I; i++)); do
  mkdir -p "$OUT_DIR/p-${i}_p-$((i + 1))"
done

export MAIN_DIR INPUTDIR OUT_DIR MUL_START MUL_STOP MUL_STEP PY_SCRIPT

echo "Detected ${#FRAMES[@]} frame(s)"
echo "Detected ${N} fringe directories -> pairs i=0..${MAX_I}"
echo "Running all (pair, frame) jobs with up to ${JOBS} parallel workers"

{
  for frame in "${FRAMES[@]}"; do
    for ((i=0; i<=MAX_I; i++)); do
      printf '%s\t%s\n' "$i" "$frame"
    done
  done
} | xargs -P "$JOBS" -L 1 bash -c '
  idx="$1"
  frame="$2"
  pair="p-${idx}_p-$((idx + 1))"
  out="${OUT_DIR}/${pair}/ri_${pair}_${frame}.csv"
  python3 "${PY_SCRIPT}" \
    --main-dir "${MAIN_DIR}" \
    --inputdir "${INPUTDIR}" \
    --idx "${idx}" \
    --frame "${frame}" \
    --mul-start "${MUL_START}" \
    --mul-stop "${MUL_STOP}" \
    --mul-step "${MUL_STEP}" \
    --out "${out}"
' _