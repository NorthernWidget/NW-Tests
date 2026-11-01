#!/bin/sh
# Does KiCad save this schematic back byte-identically?
#
# usage: roundtrip.sh <root.kicad_sch>
#
# Copies the project directory, runs kicad-cli sch upgrade (KiCad's own parser
# and serializer) on the copy, and compares every sheet with the original. A
# sheet that comes back changed holds something KiCad itself would not have
# written. Exit status is the number of sheets that differ.
set -e
sch=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
dir=$(dirname "$sch")
tmp=$(mktemp -d)
cp "$dir"/*.kicad_* "$tmp"/
[ -f "$dir/sym-lib-table" ] && cp "$dir/sym-lib-table" "$tmp"/
[ -f "$dir/fp-lib-table" ] && cp "$dir/fp-lib-table" "$tmp"/
(cd "$tmp" && kicad-cli sch upgrade --force "$(basename "$sch")" >upgrade.log 2>&1) || { cat "$tmp/upgrade.log"; exit 99; }
n=0
for f in "$dir"/*.kicad_sch; do
  b=$(basename "$f")
  if cmp -s "$f" "$tmp/$b"; then
    printf '%-24s identical\n' "$b"
  else
    printf '%-24s differs: %s lines\n' "$b" "$(diff "$f" "$tmp/$b" | grep -c '^[<>]')"
    n=$((n+1))
  fi
done
echo "copy kept at $tmp"
exit $n
