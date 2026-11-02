#!/bin/sh
# Does KiCad save this board back byte-identically?
#
# usage: roundtrip_pcb.sh <board.kicad_pcb>
#
# Copies the board, runs kicad-cli pcb upgrade (KiCad's own parser and
# serializer) on the copy and compares. A board that comes back changed holds
# something KiCad itself would not have written: an angle as -90 where KiCad
# writes 270, items in an order KiCad sorts differently. Exit 0 identical, 1 not.
set -e
src=$1; tmp=$(mktemp --suffix=.kicad_pcb)
cp "$src" "$tmp"
kicad-cli pcb upgrade --force "$tmp" >/dev/null 2>&1 || { echo "kicad-cli could not load $src"; rm -f "$tmp"; exit 2; }
if cmp -s "$src" "$tmp"; then echo "$(basename "$src")  identical"; rm -f "$tmp"; exit 0
else echo "$(basename "$src")  differs: $(diff "$src" "$tmp" | grep -c '^[<>]') lines; copy kept at $tmp"; exit 1; fi
