"""Read an Eagle 9 schematic (.sch, XML) and write its pin-level netlist as JSON.

usage: eagle_nets.py <Eagle .sch> <out.json>

Every pinref on every sheet is resolved through the library connects to a
(part, gate, pin, pad) tuple. The JSON holds parts, nets, partpins and the
counts printed below; compare_nets.py reads it.
"""
import xml.etree.ElementTree as ET, json, sys, collections
E=sys.argv[1]
t=ET.parse(E); r=t.getroot()
# library connects: lib -> deviceset -> device -> (gate,pin)->pad
conn={}
pins_per_sym={}  # lib,symbol -> list of pin names
for lib in r.iter('library'):
    ln=lib.get('name')
    for sym in lib.iter('symbol'):
        pins_per_sym[(ln,sym.get('name'))]=[(p.get('name'),p.get('direction','io')) for p in sym.findall('pin')]
    for ds in lib.iter('deviceset'):
        gates={g.get('name'):g.get('symbol') for g in ds.find('gates').findall('gate')}
        for dev in ds.find('devices').findall('device'):
            m={}
            for c in dev.findall('connects/connect'):
                m[(c.get('gate'),c.get('pin'))]=c.get('pad')
            conn[(ln,ds.get('name'),dev.get('name'))]=(gates,m,dev.get('package'))
parts={}
for p in r.find('drawing/schematic/parts').findall('part'):
    parts[p.get('name')]=dict(lib=p.get('library'),ds=p.get('deviceset'),dev=p.get('device'),value=p.get('value'))
# nets
nets=collections.defaultdict(set)  # net -> set of (part,gate,pin,pad)
sheets=r.find('drawing/schematic/sheets').findall('sheet')
nsheets=len(sheets)
pinref_count=0
for si,sh in enumerate(sheets,1):
    for n in sh.findall('nets/net'):
        for seg in n.findall('segment'):
            for pr in seg.findall('pinref'):
                part=pr.get('part'); gate=pr.get('gate'); pin=pr.get('pin')
                pi=parts[part]
                gates,m,pkg=conn[(pi['lib'],pi['ds'],pi['dev'])]
                pad=m.get((gate,pin))
                for pd in (pad.split() if pad else [None]): nets[n.get("name")].add((part,gate,pin,pd))
                pinref_count+=1
# total pins = sum over parts of pins in all gates of their symbols
total_pins=0; total_pads=0
partpins={}
for name,pi in parts.items():
    gates,m,pkg=conn[(pi['lib'],pi['ds'],pi['dev'])]
    pl=[]
    for g,symn in gates.items():
        for pn,d in pins_per_sym[(pi['lib'],symn)]:
            for pd in (m.get((g,pn)).split() if m.get((g,pn)) else [None]): pl.append((g,pn,pd,d))
    partpins[name]=pl
    total_pins+=len(pl); total_pads+=len(set(m.values()))
out=dict(parts=parts,nets={k:sorted(v) for k,v in nets.items()},partpins=partpins,nsheets=nsheets,pinref_count=pinref_count,total_pins=total_pins,total_pads=total_pads)
json.dump(out,open(sys.argv[2],'w'),indent=0)
print('Eagle: sheets',nsheets,'parts',len(parts),'nets',len(nets),'pinrefs',pinref_count,'symbol pins',total_pins,'pads(connected)',total_pads)
print('anonymous N$ nets',sum(1 for k in nets if k.startswith('N$')))
unconnected=[(p,g,pn,pad) for p,pl in partpins.items() for (g,pn,pad,d) in pl if not any((p,g,pn,pad) in v for v in nets.values())]
print('Eagle pins with no net',len(unconnected))
nopad=[(p,g,pn) for p,pl in partpins.items() for (g,pn,pad,d) in pl if pad is None]
print('Eagle pins with no pad (schematic-only)',len(nopad), nopad[:20])
