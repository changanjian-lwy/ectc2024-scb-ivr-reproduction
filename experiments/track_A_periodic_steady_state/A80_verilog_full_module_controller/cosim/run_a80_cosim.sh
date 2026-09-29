#!/bin/zsh
# A80 co-simulation cases (full module controller from zero); needs the OSS CAD Suite on PATH.
cd "${0:A:h}" || exit 1
export PATH="$HOME/tools/oss-cad-suite/bin:$PATH"
for c in "$@"; do
  python3 run_cosim.py cfg_$c.json > log_$c.txt 2>&1 &
done
wait
grep -h 'co-sim done' log_*.txt
