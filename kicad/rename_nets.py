"""Rename a board's nets to the schematic's, matched through the pads they share.

usage: rename_nets.py <netlist.xml> <board.kicad_pcb> [--assign-unconnected] [--pads REF,REF]

An imported board keeps Eagle's net names (N$3, 5V_LP) where the schematic now
has KiCad's (Net-(U2-FB), /5V_LP), and the parity check reports every pad.
Each board net is matched to the schematic net that the same (reference, pad)
pairs carry; a board net whose pads fall in more than one schematic net, or a
schematic net that would take two board nets, is left alone and listed. The
net declarations and every (net ...) reference are renamed. Re-save with
kicad-cli pcb upgrade afterwards; the pad-net table changes only in names.
--pads REF,REF gives every pad of those footprints the schematic net of the
same (reference, pad) outright, whatever the board had: for a symbol whose
stacked pins were spread into separate nets, where the board's one net maps
to several schematic nets and the matching above leaves it alone.
"""
import sys,re,collections,xml.etree.ElementTree as ET
assign='--assign-unconnected' in sys.argv; xml,pcb=[a for a in sys.argv[1:] if not a.startswith('--')][:2]
pads_of=set(sys.argv[sys.argv.index('--pads')+1].split(',')) if '--pads' in sys.argv else set()
sch={}   # (ref,pad) -> schematic net name
for n in ET.parse(xml).getroot().find('nets').findall('net'):
    for node in n.findall('node'):
        name=n.get('name')
        if name.startswith('unconnected-('): name=name.replace('/','{slash}')   # KiCad escapes a slash in a pin name on the board; the export does not
        sch[(node.get('ref'),node.get('pin'))]=name
t=open(pcb).read()
board=collections.defaultdict(set)   # board net -> {schematic nets of its pads}
for m in re.finditer(r'^\t\(footprint "[^"]+"\n.*?^\t\)\n',t,re.S|re.M):
    b=m.group(0); ref=re.search(r'\(property "Reference" "([^"]*)"',b).group(1)
    for p in re.finditer(r'\(pad "([^"]*)"[^\n]*\n(?:(?!\t\t\)).*\n)*?\t\t\t\(net "([^"]*)"\)',b):
        s=sch.get((ref,p.group(1)))
        if s is not None: board[p.group(2)].add(s)
rename={}; held=[]
rev=collections.defaultdict(list)
for bn,ss in board.items():
    if len(ss)==1: rev[next(iter(ss))].append(bn)
    else: held.append((bn,sorted(ss)))
for sn,bns in rev.items():
    if len(bns)==1 and bns[0]!=sn: rename[bns[0]]=sn
    elif len(bns)>1: held.append((sn,bns))
n=0
def esc(s): return s.replace('\\','\\\\').replace('"','\\"')
for old,new in rename.items():
    t,k=re.subn(r'\(net (\d+ )?"%s"\)'%re.escape(old),lambda m:'(net %s"%s")'%(m.group(1) or '',esc(new)),t); n+=k
assigned=0; declared=0
if assign:
    known=set(re.findall(r'^\t\(net \d+ "([^"]*)"\)',t,re.M)); newnets=[]
    def pad(pm,ref):
        global assigned
        item=pm.group(0)
        if '(net "' in item: return item
        sn=sch.get((ref,pm.group(1)))
        if not sn: return item
        assigned+=1
        if sn not in known: known.add(sn); newnets.append(sn)
        return re.sub(r'(\(layers [^)]*\)\n)',lambda q:q.group(1)+'\t\t\t(net "%s")\n'%esc(sn),item,count=1)
    def padfix(m):
        blk=m.group(0); ref=re.search(r'\(property "Reference" "([^"]*)"',blk).group(1)
        return re.sub(r'^\t\t\(pad "([^"]*)"[^\n]*\n(?:(?!^\t\t\)).*\n)*?^\t\t\)\n',lambda pm:pad(pm,ref),blk,flags=re.M)
    t=re.sub(r'^\t\(footprint "[^"]+"\n.*?^\t\)\n',padfix,t,flags=re.S|re.M)
    decl=list(re.finditer(r'^\t\(net (\d+) "[^"]*"\)\n',t,re.M))   # KiCad 10 boards declare no net list; older ones do
    if newnets and decl:
        last=decl[-1]; k=int(last.group(1))
        t=t[:last.end()]+''.join('\t(net %d "%s")\n'%(k+i+1,esc(x)) for i,x in enumerate(newnets))+t[last.end():]; declared=len(newnets)
npads=0
if pads_of:
    def padset(m):
        global npads
        blk=m.group(0); ref=re.search(r'\(property "Reference" "([^"]*)"',blk).group(1)
        if ref not in pads_of: return blk
        def one(pm):
            global npads
            item=pm.group(0); sn=sch.get((ref,pm.group(1)))
            if not sn: return item
            if '(net "' in item: new=re.sub(r'\(net (\d+ )?"[^"]*"\)','(net "%s")'%esc(sn),item,count=1)
            else: new=re.sub(r'(\(layers [^)]*\)\n)',lambda q:q.group(1)+'\t\t\t(net "%s")\n'%esc(sn),item,count=1)
            if new!=item: npads+=1
            return new
        return re.sub(r'^\t\t\(pad "([^"]*)"[^\n]*\n(?:(?!^\t\t\)).*\n)*?^\t\t\)\n',one,blk,flags=re.M)
    t=re.sub(r'^\t\(footprint "[^"]+"\n.*?^\t\)\n',padset,t,flags=re.S|re.M)
open(pcb,'w').write(t)
if pads_of: print('pads set to their schematic net outright: %d (%s)'%(npads,' '.join(sorted(pads_of))))
print('renamed %d nets (%d references); left alone: %s%s'%(len(rename),n,held,'; pads given their schematic net: %d, nets declared: %d'%(assigned,declared) if assign else ''))
for old,new in sorted(rename.items())[:8]: print('  ',old,'->',new)
