"""Count what a KiCad board holds and dump its pad-to-net table.

usage: pcb_stats.py <board.kicad_pcb> <outdir>

Writes kicad_pcb_padnets.json, kicad_pcb_fps.json and kicad_pcb_nets.json into
<outdir> and prints segment, via, zone, footprint and graphics counts.
"""
import sys,json,collections,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from sexp import *
S=sys.argv[2].rstrip('/')+'/'
p=parse(open(sys.argv[1]).read())
segs=kids(p,'segment'); print('segments',len(segs),'by layer',collections.Counter(kid(s,'layer')[1] for s in segs))
print('arcs',len(kids(p,'arc')),'vias',len(kids(p,'via')))
zs=kids(p,'zone'); print('zones',len(zs))
for z in zs:
    print('   net',(kid(z,'net') or [0,'(none)'])[1],'layer',kid(z,'layer',kid(z,'layers'))[1:],'filled',len(kids(z,'filled_polygon')),'keepout' if kid(z,'keepout') else '')
fps=kids(p,'footprint'); print('footprints',len(fps))
gr=collections.Counter()
for k in ('gr_line','gr_arc','gr_circle','gr_poly','gr_rect','gr_text'):
    for g in kids(p,k): gr[(k,kid(g,'layer')[1])]+=1
print('board graphics',dict(gr))
fg=collections.Counter(); refs={}; padnets={}; npads=0; nonet=0
for f in fps:
    ref=[x for x in kids(f,'property') if x[1]=='Reference'][0][2]
    refs[ref]=(f[1],kid(f,'layer')[1],bool(kid(f,'path')),bool(kid(f,'sheetname')))
    for k in ('fp_line','fp_arc','fp_circle','fp_poly','fp_rect','fp_text'):
        for g in kids(f,k): fg[(k,kid(g,'layer')[1])]+=1
    for pd in kids(f,'pad'):
        npads+=1; nn=kid(pd,'net'); padnets[ref+'|'+pd[1]]=nn[1] if nn else ''
print('footprint graphics',dict(fg))
print('refs',len(refs),'layers',collections.Counter(v[1] for v in refs.values()),'libs',collections.Counter(v[0].split(':')[0] if ':' in v[0] else '(none)' for v in refs.values()),'with path',sum(v[2] for v in refs.values()))
print('pads',npads,'with net',sum(1 for v in padnets.values() if v))
nets=kids(p,'net'); print('pcb nets',len(nets))
json.dump(padnets,open(S+'kicad_pcb_padnets.json','w')); json.dump({r:v[0] for r,v in refs.items()},open(S+'kicad_pcb_fps.json','w'))
json.dump([n[2] for n in nets],open(S+'kicad_pcb_nets.json','w'))
st=kid(p,'setup'); print('setup keys',[x[0] for x in st if isinstance(x,list)])
print('stackup' , kid(st,'stackup'))
