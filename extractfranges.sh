#!/usr/bin/env bash
#
# run_toto_parallel launches MMVII ExtractFranges in parallel over Retiga_*.tif files.
#
# Usage:
#   run_toto_parallel [-j N] [--from N [--to N]] [--arg 'KEY=VAL'] ... [-- EXTRA_ARGS...]
#
# Options:
#   -j, --jobs N        max number of parallel jobs (0 = unlimited)
#   --from N [--to N]   process only Retiga_%09d.tif in range [from,to] (to defaults to from)
#   --arg 'KEY=VAL'      one MMVII extra argument; repeatable, e.g.
#                          --arg 'IntY=[980,1220]' --arg 'MinWidth=0'
#   --                    everything after this is passed verbatim to MMVII,
#                          e.g. -- 'IntY=[980,1220]' MinWidth=0 BorderMinWidth=0
#
# --arg and `--` can both be used; all collected extra arguments are appended,
# in order, to the MMVII ExtractFranges command line for every file.

run_toto_parallel() {
  local max_jobs=0 from= to=
  local -a extra_args=()
  local f i p

  while (($#)); do
    case $1 in
      -j|--jobs) max_jobs=$2; shift 2 ;;
      --from)    from=$2; shift 2 ;;
      --to)      to=$2; shift 2 ;;
      --arg)     extra_args+=("$2"); shift 2 ;;
      --)
        shift
        extra_args+=("$@")
        break
        ;;
      *)
        echo "usage: run_toto_parallel [-j N] [--from N [--to N]] [--arg 'KEY=VAL'] ... [-- EXTRA_ARGS...]"
        return 1
        ;;
    esac
  done

  [[ -n $from && -z $to ]] && to=$from
  shopt -s nullglob

  _run_one() {
    local file=$1
    if ((${#extra_args[@]})); then
      MMVII ExtractFranges "$file" "${extra_args[@]}" &
    else
      MMVII ExtractFranges "$file" &
    fi
    (( max_jobs > 0 )) && while (( $(jobs -r | wc -l) >= max_jobs )); do sleep .1; done
  }

  if [[ -n $from ]]; then
    for ((i=from; i<=to; i++)); do
      printf -v p '%09d' "$i"
      f="Retiga_${p}.tif"
      [[ -e $f ]] || continue
      _run_one "$f"
    done
  else
    for f in Retiga_*.tif; do
      _run_one "$f"
    done
  fi

  wait
}

# Allow the script to be run directly, forwarding all its args.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  run_toto_parallel "$@"
fi