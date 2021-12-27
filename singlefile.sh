#!/bin/bash
#this file is a adaptation of the https://factoriobox.1au.us/scripts/benchmark.sh skript and for license one has to check https://factoriobox.1au.us/scripts/benchmark.sh. 
set -o pipefail
run() {
  test_bin() {
    command -v "$1" > /dev/null
  }
  get_realpath() {
    echo "$(cd "$(dirname "$1")"; pwd -P)/$(basename "$1")"
  }
  : "${HOST:="https://factoriobox.1au.us"}"
  : "${BENCH_TICKS:=100}"
  : "${BENCH_RUNS:=1}"
  if [ -z "$FACTORIO_BIN" ]; then
    FACTORIO_BIN=../bin/x64/factorio
    if ! test_bin "$FACTORIO_BIN"; then
      FACTORIO_BIN=./factorio;
      if ! test_bin "$FACTORIO_BIN"; then
        FACTORIO_BIN=factorio;
        if ! test_bin "$FACTORIO_BIN"; then
          FACTORIO_BIN="$HOME/.local/share/Steam/steamapps/common/Factorio/bin/x64/factorio";
        fi
      fi
    fi
  fi
  if ! test_bin "$FACTORIO_BIN"; then
    echo "Could not locate the Factorio binary. Validate it is in your path, installed via Steam, or CD to it."
    return 1
  fi
  if ! test_bin lshw; then
    echo "Please install lshw to get hardware information"
    return 1
  fi
  echo "Please sudo to run lshw and get hardware information"
  LSHW=$(LC_ALL=C sudo lshw)
  if ! FACTORIO_VERSION=$("$FACTORIO_BIN" --version | head -n 1); then
    echo "Factorio exited with non-zero exit code"
#    return 1
  fi
  echo "Found $FACTORIO_VERSION at $(get_realpath "$FACTORIO_BIN")"
  FACTORIO_VERSION_SHORT=$(echo "$FACTORIO_VERSION" | awk '{print $2}')
  : "${URL:="$HOST/map-version/$FACTORIO_VERSION_SHORT"}"
  if [ -z "$MAP" ]; then
    MAP=$(mktemp)
    echo "Downloading map..."
    curl --progress-bar -o "$MAP" "$URL"
  fi
  MAP_HASH=$(sha256sum "$MAP" | awk '{print $1}')
  echo "Running benchmark..."
  exec 5>&1
  if ! FACTORIO_LOG=$(stdbuf -oL "$FACTORIO_BIN" --mod-directory /dev/null --benchmark "$MAP" --benchmark-ticks $BENCH_TICKS --benchmark-runs $BENCH_RUNS --benchmark-verbose all --benchmark-sanitize | tee >(egrep "t|Performed" >&5)) ||
    ! UPS=$(awk -v ticks="$BENCH_TICKS" 'BEGIN{min = -1} $1=="Performed"{if (min == -1 || $5 < min) min = $5} END{print 1000 * ticks / min}' <<< $FACTORIO_LOG); then
    echo Benchmark failed
    echo "$FACTORIO_LOG"
    return 1
  fi
  echo "Map benchmarked at $UPS UPS"
#  CPU=$(echo "$LSHW" | awk '/^     \*-cpu/{p=1;next}/^     \*/{p=0}p' | grep -v "serial" | sed "s/^[ \t]*//")
#  MEMORY=$(echo "$LSHW" | awk '/^     \*-memory/{p=1;next}/^     \*/{p=0}p' | grep -v "serial" | sed "s/^[ \t]*//")
#  echo "Share your benchmark at: $HOST/result/"$(curl --progress-bar --data-binary @- <<< "v2 linux
#$MAP_HASH
#$FACTORIO_VERSION
#$BENCH_TICKS
#$BENCH_RUNS
#$(grep -Po 'Performed \d+ updates in \d+\.\d+ ms' <<< $FACTORIO_LOG)
#$(grep "^[^ ]" <<< $FACTORIO_LOG)
#$CPU
#$MEMORY
#$(LC_ALL=C lscpu)" -X POST -s -S "$HOST/result")
}
run

