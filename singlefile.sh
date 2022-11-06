#!/bin/bash
#this file is a adaptation of the https://factoriobox.1au.us/scripts/benchmark.sh skript and for license one has to check https://factoriobox.1au.us/scripts/benchmark.sh. 
set -o pipefail
run() {
  : "${HOST:="https://factoriobox.1au.us"}"
  : "${BENCH_TICKS:=1000}"
  : "${BENCH_RUNS:=1}"
  FACTORIO_BIN=factorio/bin/x64/factorio

  echo "Running benchmark..."
  exec 5>&1
  if ! FACTORIO_LOG=$(stdbuf -oL "$FACTORIO_BIN" --mod-directory /dev/null --benchmark "$MAP" --benchmark-ticks $BENCH_TICKS --benchmark-runs $BENCH_RUNS --benchmark-verbose all --benchmark-sanitize | tee >(egrep "t|Performed" >&5)) ||
    ! UPS=$(awk -v ticks="$BENCH_TICKS" 'BEGIN{min = -1} $1=="Performed"{if (min == -1 || $5 < min) min = $5} END{print 1000 * ticks / min}' <<< $FACTORIO_LOG); then
    echo Benchmark failed
    echo "$FACTORIO_LOG"
    return 1
  fi
  echo "Map benchmarked at $UPS UPS"

}
run

