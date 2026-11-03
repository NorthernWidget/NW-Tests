"""Place a library symbol on a sheet, as the GUI would.

usage: place_symbol.py <sheet.kicad_sch> <root.kicad_sch> <library.kicad_sym> <nickname> <symbol> <reference> <x_mm> <y_mm> [--value V]

Copies the symbol's definition into the sheet's lib_symbols as
<nickname>:<symbol> (once), appends a placed instance at (x, y) with the
reference, the library's value (or --value), footprint, datasheet and
description, the library's BOM/simulation/position flags, and an instance
record for the project path (root uuid, then the sheet's uuid when the sheet
is not the root). Adds the library to sym-lib-table beside the sheet if it is
not there, at a path relative to ${KIPRJMOD}. Re-save with kicad-cli sch
upgrade afterwards and run ERC, the netlist check and the round trip.
"""
import sys,os,re,uuid
a=sys.argv[1:]; value=None
if '--value' in a: i=a.index('--value'); value=a[i+1]; del a[i:i+2]
sheet,root,lib,nick,name,ref,x,y=a; x=float(x); y=float(y)
L=open(lib).read()
m=re.search(r'^\t\(symbol "'+re.escape(name)+r'"\n.*?^\t\)\n',L,re.S|re.M); assert m,'no symbol '+name
sym=m.group(0)
# the sheet's copy carries the library-qualified name on the top symbol only; its units keep the bare name
libcopy=re.sub(r'^\t\(symbol "'+re.escape(name)+'"','\t(symbol "%s:%s"'%(nick,name),sym,count=1)
libcopy='\n'.join('\t'+l if l else l for l in libcopy.rstrip('\n').split('\n'))+'\n'
S=open(sheet).read()
if '(symbol "%s:%s"'%(nick,name) not in S:
    if '\t(lib_symbols)\n' in S: S=S.replace('\t(lib_symbols)\n','\t(lib_symbols\n'+libcopy+'\t)\n',1)
    else:
        i=S.index('\t(lib_symbols\n'); j=S.index('\n\t)\n',i)+1
        S=S[:j]+libcopy+S[j:]
flags=''.join(re.findall(r'\t\t\((?:exclude_from_sim|in_bom|on_board|in_pos_files) \w+\)\n',sym)).replace('\t\t(','\t\t(')
props=[]
for pname,pval in re.findall(r'\t\t\(property "([^"]+)" "((?:[^"\\]|\\.)*)"',sym):
    if pname.startswith('ki_'): continue   # a library-side flag, not a field of the placed symbol
    if pname=='Reference': pval=ref
    elif pname=='Value': pval=value if value is not None else pval
    hide='\n\t\t\t(hide yes)' if pname not in ('Reference','Value') else ''
    at=re.search(r'\t\t\(property "%s" "(?:[^"\\]|\\.)*"\n\t\t\t\(at (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)\)'%re.escape(pname),sym)
    px,py,pa=(float(at.group(1)),float(at.group(2)),at.group(3)) if at else (0,0,'0')
    props.append('\t\t(property "%s" "%s"\n\t\t\t(at %s %s %s)%s\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'%(pname,pval,('%.4f'%(x+px)).rstrip('0').rstrip('.'),('%.4f'%(y-py)).rstrip('0').rstrip('.'),pa,hide))
R=open(root).read(); ruuid=re.search(r'^\t\(uuid "([^"]+)"\)',R,re.M).group(1)
path='/'+ruuid
if os.path.abspath(sheet)!=os.path.abspath(root):
    suuid=re.search(r'^\t\(uuid "([^"]+)"\)',S,re.M).group(1); path+='/'+suuid
proj=os.path.basename(root)[:-len('.kicad_sch')]
inst='\t(symbol\n\t\t(lib_id "%s:%s")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n%s\t\t(dnp no)\n\t\t(uuid "%s")\n%s\t\t(instances\n\t\t\t(project "%s"\n\t\t\t\t(path "%s"\n\t\t\t\t\t(reference "%s")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n'%(nick,name,('%g'%x),('%g'%y),flags,uuid.uuid4(),''.join(props),proj,path,ref)
i=S.index('\t(sheet_instances\n') if '\t(sheet_instances\n' in S else S.rindex('\n)')+1
S=S[:i]+inst+S[i:]
open(sheet,'w').write(S)
d=os.path.dirname(os.path.abspath(sheet)); tbl=os.path.join(d,'sym-lib-table'); T=open(tbl).read() if os.path.exists(tbl) else '(sym_lib_table\n\t(version 7)\n)\n'
if '(name "%s")'%nick not in T:
    rel=os.path.relpath(os.path.abspath(lib),d)
    T=T.replace('\n)','\n\t(lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s")(options "")(descr ""))\n)'%(nick,rel),1); open(tbl,'w').write(T)
print('placed %s as %s at (%s, %s) on %s; path %s'%(name,ref,x,y,os.path.basename(sheet),path))
