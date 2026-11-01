"""Crop a rendered sheet to a window given in schematic millimeters.

usage: crop.py <sheet.png> <x_mm> <y_mm> <w_mm> <h_mm> <out.png> [--dpi 600] [--label TEXT]

Coordinates are KiCad's (origin top left, y down), the same numbers that appear
in (at x y) in the .kicad_sch file, so a window can be read straight off the
file. --label stamps a word along the top edge, for side-by-side variants.
"""
import sys,subprocess
a=[x for x in sys.argv[1:] if not x.startswith('--')]
dpi=600.0; label=None
for i,x in enumerate(sys.argv):
    if x=='--dpi': dpi=float(sys.argv[i+1])
    if x=='--label': label=sys.argv[i+1]
png,x,y,w,h,out=a[0],*map(float,a[1:5]),a[5]
p=dpi/25.4
geom='%dx%d+%d+%d'%(w*p,h*p,x*p,y*p)
cmd=['convert',png,'-crop',geom,'+repage']
if label: cmd+=['-gravity','north','-pointsize','40','-annotate','+0+5',label]
subprocess.run(cmd+[out],check=True)
print(out)
