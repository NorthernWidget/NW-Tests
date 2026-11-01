"""Read a KiCad XML netlist export and write it as JSON.

usage: kicad_nets.py <netlist.xml> <out.json>

Make the XML with: kicad-cli sch export netlist --format kicadxml -o <netlist.xml> <root.kicad_sch>
"""
import xml.etree.ElementTree as ET, json, sys, collections
r=ET.parse(sys.argv[1]).getroot()
comps={}
for c in r.find('components').findall('comp'):
    comps[c.get('ref')]=dict(value=(c.findtext('value') or ''),footprint=(c.findtext('footprint') or ''),libsource=c.find('libsource').get('part') if c.find('libsource') is not None else '', lib=c.find('libsource').get('lib') if c.find('libsource') is not None else '')
nets={}
nodes=0
for n in r.find('nets').findall('net'):
    s=set()
    for nd in n.findall('node'):
        s.add((nd.get('ref'),nd.get('pin'),nd.get('pinfunction','')))
        nodes+=1
    nets[n.get('name')]=sorted(s)
json.dump(dict(comps=comps,nets=nets),open(sys.argv[2],'w'),indent=0)
print('KiCad netlist: comps',len(comps),'nets',len(nets),'nodes',nodes)
print('nets with 1 node',sum(1 for v in nets.values() if len(v)==1))
print('unnamed Net-( nets',sum(1 for k in nets if k.startswith('Net-')))
