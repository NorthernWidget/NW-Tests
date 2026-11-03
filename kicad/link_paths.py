"""Give every board footprint the path to its schematic symbol, from the netlist export.

usage: link_paths.py <netlist.xml> <board.kicad_pcb> [--values] [--fields]

Make the XML with: kicad-cli sch export netlist --format kicadxml -o <netlist.xml> <root.kicad_sch>

What Update PCB from Schematic writes when it re-links by reference: for a
footprint whose reference matches one component, (path "<sheet tstamps><symbol
tstamp>") with (sheetname) and (sheetfile) from the component's properties.
A reference with no component (a logo, a mounting hole) is left alone and
listed. --values sets the footprint's Value property to the symbol's; --fields
copies the component's other fields (DIGIKEY, MPN, ...) as footprint
properties, sets the footprint's Description to the symbol's, and marks the
footprint excluded from the BOM when the symbol is. The schematic parity check compares all three. Re-save with
kicad-cli pcb upgrade afterwards.
"""
import sys,re,uuid,xml.etree.ElementTree as ET
a=sys.argv[1:]; values='--values' in a; fields='--fields' in a; a=[x for x in a if not x.startswith('--')]
xml,pcb=a
comps={}
for c in ET.parse(xml).getroot().find('components').findall('comp'):
    sp=c.find('sheetpath'); ts=c.findtext('tstamps') or ''
    props={p.get('name'):p.get('value') for p in c.findall('property')}
    attrs=[a for a in ('exclude_from_bom','exclude_from_board','dnp') if a in props]
    fe=c.find('fields'); flds={f.get('name'):(f.text or '') for f in (fe if fe is not None else [])}
    comps[c.get('ref')]=dict(attrs=attrs,path=(sp.get('tstamps') if sp is not None else '/')+ts.split()[0],sheetname=props.get('Sheetname',''),sheetfile=props.get('Sheetfile',''),value=c.findtext('value') or '',fields=flds)
t=open(pcb).read(); linked=0; skipped=[]; nv=0; nf=0
SKIP_FIELDS={'Footprint','Datasheet','Description','Reference','Value'}
def sub(m):
    global linked,nv,nf
    b=m.group(0); ref=re.search(r'\(property "Reference" "([^"]*)"',b).group(1); c=comps.get(ref)
    if not c: skipped.append(ref); return b
    b=re.sub(r'^\t\t\((?:path|sheetname|sheetfile) "[^"]*"\)\n','',b,flags=re.M)
    ins='\t\t(path "%s")\n\t\t(sheetname "%s")\n\t\t(sheetfile "%s")\n'%(c['path'],c['sheetname'],c['sheetfile'])
    mm=re.search(r'^\t\t\((?:attr |fp_line|fp_poly|fp_circle|fp_arc|fp_rect|fp_text|pad|model|embedded_fonts)',b,re.M)
    b=b[:mm.start()]+ins+b[mm.start():]; linked+=1
    if values:
        b,n=re.subn(r'\(property "Value" "[^"]*"','(property "Value" "%s"'%c['value'].replace('"','\\"'),b,count=1); nv+=n
    if fields:
        desc=c['fields'].get('Description')
        if desc is not None: b=re.sub(r'\(property "Description" "[^"]*"','(property "Description" "%s"'%desc.replace('"','\\"'),b,count=1)
        if 'exclude_from_bom' in c['attrs']:
            if '\t\t(attr ' in b:
                if 'exclude_from_bom' not in b: b=re.sub(r'^\t\t\(attr ([^)]*)\)',r'\t\t(attr \1 exclude_from_bom)',b,count=1,flags=re.M)
            else:
                mm=re.search(r'^\t\t\((?:fp_line|fp_poly|fp_circle|fp_arc|fp_rect|fp_text|pad|model|embedded_fonts)',b,re.M); b=b[:mm.start()]+'\t\t(attr exclude_from_bom)\n'+b[mm.start():]
        have=set(re.findall(r'\(property "([^"]+)"',b))
        extra=''.join('\t\t(property "%s" "%s"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(hide yes)\n\t\t\t(uuid "%s")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'%(k,v.replace('"','\\"'),uuid.uuid4()) for k,v in c['fields'].items() if k not in SKIP_FIELDS and k not in have)
        if extra:
            last=list(re.finditer(r'^\t\t\(property "[^"]*" "(?:[^"\\]|\\.)*"\n.*?^\t\t\)\n',b,re.S|re.M))[-1]
            b=b[:last.end()]+extra+b[last.end():]; nf+=extra.count('\t\t(property')
    return b
t2=re.sub(r'^\t\(footprint "([^"]+)"\n.*?^\t\)\n',sub,t,flags=re.S|re.M)
open(pcb,'w').write(t2)
print('linked %d footprints; values set %d; fields added %d; no symbol: %s'%(linked,nv,nf,skipped))
