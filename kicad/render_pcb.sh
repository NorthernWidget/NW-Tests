#!/bin/sh
# Render a board to SVG and to PNG at a known scale, in sheet coordinates.
#
# usage: render_pcb.sh <board.kicad_pcb> <out.png> [layers] [dpi]
#
# The page is the sheet, so a footprint's (at x y) in the file is the same
# number crop.py takes. Default layers: F.Cu, F.Paste, F.Mask, F.SilkS, F.Fab,
# F.CrtYd, Edge.Cuts; give "B.Cu,B.Mask,B.SilkS,Edge.Cuts" for the back. At 600
# dpi one millimeter is 23.622 px. Needs kicad-cli and inkscape.
set -e
pcb=$1; out=$2; layers=${3:-F.Cu,F.Paste,F.Mask,F.SilkS,F.Fab,F.CrtYd,Edge.Cuts}; dpi=${4:-600}
tmp=$(mktemp -d)
kicad-cli pcb export svg --layers "$layers" --page-size-mode 0 --exclude-drawing-sheet -o "$tmp/board.svg" "$pcb" >"$tmp/log" 2>&1
inkscape "$tmp/board.svg" --export-type=png --export-dpi="$dpi" --export-background=white -o "$out" >>"$tmp/log" 2>&1
echo "$out"; rm -rf "$tmp"
