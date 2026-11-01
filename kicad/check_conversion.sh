#!/bin/sh
# Netlist acceptance test for an Eagle-to-KiCad conversion.
#
# usage: check_conversion.sh <root.kicad_sch> <Eagle .sch> [ignored refs] [workdir]
#
# Exports the KiCad netlist, reads both schematics to JSON and prints the
# comparison. The headline is the "Eagle nets:" line; the last argument is a
# directory the JSON and the full report are kept in (default: a temp dir).
set -e
here=$(cd "$(dirname "$0")" && pwd)
sch=$1; eagle=$2; ignore=${3:-}; work=${4:-$(mktemp -d)}
mkdir -p "$work"
kicad-cli sch export netlist --format kicadxml -o "$work/netlist.xml" "$sch" >"$work/netlist.log" 2>&1
python3 "$here/eagle_nets.py" "$eagle" "$work/eagle.json" >"$work/eagle.log"
python3 "$here/kicad_nets.py" "$work/netlist.xml" "$work/kicad.json" >"$work/kicad.log"
if [ -n "$ignore" ]; then
  python3 "$here/compare_nets.py" "$work/eagle.json" "$work/kicad.json" --ignore "$ignore" >"$work/compare.out"
else
  python3 "$here/compare_nets.py" "$work/eagle.json" "$work/kicad.json" >"$work/compare.out"
fi
grep '^== Eagle nets:' "$work/compare.out"
grep -A1 'Eagle-connected pins missing from KiCad entirely' "$work/compare.out" | tail -1
grep 'KiCad unconnected but Eagle connected' "$work/compare.out"
echo "full report: $work/compare.out"
