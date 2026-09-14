#!/bin/bash
set -euo pipefail

# Reliable LTspice launcher for the macOS CrossOver-based application bundle.
# It bypasses macOS document association, which does not declare .cir/.net.

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <run|open> [netlist]" >&2
  exit 2
fi

mode="$1"
netlist="${2:-}"
wine_runner="/Applications/LTspice.app/Contents/SharedSupport/ltspice/bin/wine"

if [[ ! -x "$wine_runner" ]]; then
  echo "LTspice compatibility runner not found: $wine_runner" >&2
  exit 1
fi

if [[ -z "$netlist" || ! -f "$netlist" ]]; then
  echo "Netlist not found: $netlist" >&2
  exit 1
fi

netlist="$(cd "$(dirname "$netlist")" && pwd)/$(basename "$netlist")"

ltspice_exe='C:\Program Files\ADI\LTspice\LTspice.exe'

case "$mode" in
  run)
    # A bare "LTspice.exe" relies on the wine wrapper resolving it against
    # --workdir/PATH; this build's winewrapper.exe fails that resolution
    # ("cannot execute") even for a known-good netlist, so the fully
    # qualified Windows path is passed explicitly instead.
    exec "$wine_runner" --bottle default --wait-children \
      --workdir 'C:/Program Files/ADI/LTspice' \
      "$ltspice_exe" -b "$netlist"
    ;;
  open)
    exec "$wine_runner" --bottle default --no-wait \
      --workdir 'C:/Program Files/ADI/LTspice' \
      "$ltspice_exe" "$netlist"
    ;;
  *)
    echo "Unknown mode: $mode (expected run or open)" >&2
    exit 2
    ;;
esac
