run_toto_parallel() {
  local max_jobs=0 from= to= extra=
  local f i p

  while (($#)); do
    case $1 in
      -j|--jobs) max_jobs=$2; shift 2 ;;
      --from)    from=$2; shift 2 ;;
      --to)      to=$2; shift 2 ;;
      --arg)     extra=$2; shift 2 ;;
      *)
        echo "usage: run_toto_parallel [-j N] [--from N [--to N]] [--arg 'IntY=[a,b]']"
        return 1
        ;;
    esac
  done

  [[ -n $from && -z $to ]] && to=$from

  shopt -s nullglob

  if [[ -n $from ]]; then
    for ((i=from; i<=to; i++)); do
      printf -v p '%09d' "$i"
      f="Retiga_${p}.tif"
      [[ -e $f ]] || continue

      if [[ -n $extra ]]; then
        MMVII ExtractFranges "$f" "$extra" &
      else
        MMVII ExtractFranges "$f" &
      fi

      (( max_jobs > 0 )) && while (( $(jobs -r | wc -l) >= max_jobs )); do sleep .1; done
    done
  else
    for f in Retiga_*.tif; do
      if [[ -n $extra ]]; then
        MMVII ExtractFranges "$f" "$extra" &
      else
        MMVII ExtractFranges "$f" &
      fi

      (( max_jobs > 0 )) && while (( $(jobs -r | wc -l) >= max_jobs )); do sleep .1; done
    done
  fi

  wait
}
