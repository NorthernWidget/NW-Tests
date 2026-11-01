#!/bin/sh
# Render every sheet of a schematic to SVG and to PNG at a known scale.
#
# usage: render.sh <root.kicad_sch> <outdir> [dpi]
#
# At the default 600 dpi one millimeter of sheet is 23.622 px, which crop.py
# relies on. Needs kicad-cli and inkscape.
set -e
sch=$1; out=$2; dpi=${3:-600}
mkdir -p "$out/svg"
kicad-cli sch export svg --no-background-color -o "$out/svg" "$sch" >"$out/svg.log" 2>&1
for s in "$out"/svg/*.svg; do
  b=$(basename "$s" .svg)
  inkscape "$s" --export-type=png --export-dpi="$dpi" --export-filename="$out/$b.png" >/dev/null 2>&1
  echo "$out/$b.png"
done
