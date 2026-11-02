"""Point a converted project's footprint references at a shared library.

usage: relink.py <root.kicad_sch> <board.kicad_pcb> <eagle.brd> <nickname> <library.pretty>
                 [--alias OLD=NEW ...] [--strip SUFFIX ...] [--write-table]

Every board footprint and every schematic Footprint field, in every
.kicad_sch beside the root and in each sheet's embedded library symbols and in the project's own .kicad_sym
libraries, is rewritten to
<nickname>:<name>, where <name> is the element's Eagle package (from the
.brd, by reference) after --strip suffixes the importer added (`_528`) and
--alias renames the library made (SOT23-3@1=SOT23-3). A name the library does
not hold stops the run and is listed. --write-table writes the project's
fp-lib-table with the library at a path relative to ${KIPRJMOD}. The files are
edited in place with the smallest change (one string per footprint or field);
run check_conversion.sh, roundtrip.sh and ERC afterwards.
"""
import sys,os,re,xml.etree.ElementTree as ET
a=sys.argv[1:]; opts={'--alias':[],'--strip':[]}; flags=set(); pos=[]
i=0
while i<len(a):
    if a[i] in opts: opts[a[i]].append(a[i+1]); i+=2
    elif a[i].startswith('--'): flags.add(a[i]); i+=1
    else: pos.append(a[i]); i+=1
sch,pcb,brd,nick,pretty=pos
alias=dict(x.split('=',1) for x in opts['--alias'])
have=set(f[:-10] for f in os.listdir(pretty) if f.endswith('.kicad_mod'))
el={e.get('name'):e.get('package') for e in ET.parse(brd).getroot().iter('element')}
def target(ref,oldname):
    n=el.get(ref)
    if n is None:  # not an Eagle element (a KiCad-side addition): keep the old name
        n=oldname.split(':')[-1]
    for s in opts['--strip']:
        if n.endswith(s): n=n[:-len(s)]
    n=alias.get(n,n)
    return n
missing=set(); changed=0
# board
t=open(pcb).read(); out=[]
def fp_sub(m):
    global changed
    block=m.group(0); ref=re.search(r'\(property "Reference" "([^"]*)"',block).group(1)
    n=target(ref,m.group(1))
    if n not in have: missing.add((ref,n)); return block
    new='\t(footprint "%s:%s"\n'%(nick,n)
    if not block.startswith(new): changed+=1
    return new+block[len(m.group(0).split('\n',1)[0])+1:]
t2=re.sub(r'^\t\(footprint "([^"]+)"\n.*?^\t\)\n',fp_sub,t,flags=re.S|re.M)
nb=changed
# schematic sheets: the root and every sheet it names
d=os.path.dirname(os.path.abspath(sch)); sheets=sorted(os.path.join(d,f) for f in os.listdir(d) if f.endswith('.kicad_sch'))
ns=0; nl=0
def lib_sub(m):
    # the sheet's embedded library symbols carry a default Footprint too; map it by name
    global nl
    n=m.group(1).split(':')[-1]
    for suf in opts['--strip']:
        if n.endswith(suf): n=n[:-len(suf)]
    n=alias.get(n,n)
    if n not in have: return m.group(0)
    new='(property "Footprint" "%s:%s"'%(nick,n)
    if m.group(0)!=new: nl+=1
    return new
for f in sheets:
    s=open(f).read(); n0=changed
    def sym_sub(m):
        global changed
        block=m.group(0); r=re.search(r'\(property "Reference" "([^"]*)"',block); fpm=re.search(r'\(property "Footprint" "([^"]*)"',block)
        if not r or not fpm or fpm.group(1)=='' or r.group(1).startswith('#'): return block
        ref=r.group(1); n=target(ref,fpm.group(1))
        if n not in have: missing.add((ref,n)); return block
        new='(property "Footprint" "%s:%s"'%(nick,n)
        if fpm.group(0)!=new: changed+=1
        return block.replace(fpm.group(0),new,1)
    s2=re.sub(r'^\t\(symbol\n\t\t\(lib_id "[^"]+"\)\n.*?^\t\)\n',sym_sub,s,flags=re.S|re.M)
    lm=re.search(r'^\t\(lib_symbols\n.*?^\t\)\n',s2,re.S|re.M)
    if lm: s2=s2[:lm.start()]+re.sub(r'\(property "Footprint" "([^"]+)"',lib_sub,lm.group(0))+s2[lm.end():]
    if missing: continue
    if s2!=s: open(f,'w').write(s2)
    ns+=changed-n0
if missing:
    print('STOP: not in the library:',sorted(missing)); sys.exit(1)
# the project's own symbol libraries carry the same default Footprint fields; ERC compares placed symbols against them
nk=0
for f in sorted(os.listdir(d)):
    if not f.endswith('.kicad_sym'): continue
    t0=open(os.path.join(d,f)).read(); before=nl
    t1=re.sub(r'\(property "Footprint" "([^"]+)"',lib_sub,t0)
    nk+=nl-before; nl=before
    if t1!=t0: open(os.path.join(d,f),'w').write(t1)
open(pcb,'w').write(t2)
if '--write-table' in flags:
    rel=os.path.relpath(os.path.abspath(pretty),d)
    open(os.path.join(d,'fp-lib-table'),'w').write('(fp_lib_table\n\t(version 7)\n\t(lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s")(options "")(descr ""))\n)\n'%(nick,rel))
print('board footprints renamed: %d; schematic footprint fields rewritten: %d placed symbols, %d sheet library defaults, %d project symbol-library defaults'%(nb,ns,nl,nk))
