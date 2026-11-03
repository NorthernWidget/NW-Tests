"""Move placed symbols from one symbol library to another, name for name.

usage: swap_symbols.py <sheet.kicad_sch> <library.kicad_sym> <old nickname> <new nickname> [--only NAME,NAME] [--strip PREFIX,...]

For every placed symbol whose lib_id is <old>:<name> and whose name (after
--strip prefixes) exists in the library, the lib_id becomes <new>:<name>, the
library's definition is copied into the sheet's lib_symbols under that name
(units keep their bare names), and the old definition goes when nothing on
the sheet names it any more. The placed instance keeps every property and
its pin uuids (a power symbol takes the library's value, which names its
net): this is a swap of definition only, so it is right only where
the pins' numbers and positions agree, which `symbol_map.py` measures first.
Re-save with kicad-cli sch upgrade, then the netlist check, ERC and the
round trip.
"""
import sys,re
a=sys.argv[1:]; only=None; strip=[]
if '--only' in a: i=a.index('--only'); only=set(a[i+1].split(',')); del a[i:i+2]
if '--strip' in a: i=a.index('--strip'); strip=a[i+1].split(','); del a[i:i+2]
sheet,lib,old,new=a
L=open(lib).read()
libsyms={m.group(1):m.group(0) for m in re.finditer(r'^\t\(symbol "([^"]+)"\n.*?^\t\)\n',L,re.S|re.M)}
S=open(sheet).read()
def target(name):
    for c in [name]+[name[len(p):] for p in strip if name.startswith(p)]:
        if c in libsyms: return c
    return None
swapped={}; n=0
def sub(m):
    global n
    b=m.group(0); lid=re.search(r'\(lib_id "([^"]+)"\)',b).group(1)
    nick,name=lid.split(':',1)
    if nick!=old: return b
    t=target(name)
    if t is None or (only and t not in only): return b
    swapped[name]=t; n+=1
    b=b.replace('(lib_id "%s")'%lid,'(lib_id "%s:%s")'%(new,t),1)
    if re.search(r'^\t\t\(power\)',libsyms[t],re.M):   # a power symbol's net is its value: take the library's
        v=re.search(r'\(property "Value" "([^"]*)"',libsyms[t]).group(1)
        b=re.sub(r'\(property "Value" "[^"]*"','(property "Value" "%s"'%v,b,count=1)
    return b
S=re.sub(r'^\t\(symbol\n\t\t\(lib_id "[^"]+"\)\n.*?^\t\)\n',sub,S,flags=re.S|re.M)
# the sheet's library copies: add the new, drop the old that nothing names
i=S.index('\t(lib_symbols\n'); j=S.index('\n\t)\n',i)+1
block=S[i:j]
for name,t in swapped.items():
    if '(symbol "%s:%s"'%(new,t) in block: continue
    copy=re.sub(r'^\t\(symbol "'+re.escape(t)+'"','\t(symbol "%s:%s"'%(new,t),libsyms[t],count=1)
    block+= '\n'.join('\t'+l if l else l for l in copy.rstrip('\n').split('\n'))+'\n'
for name in swapped:
    if '(lib_id "%s:%s")'%(old,name) in S: continue
    block=re.sub(r'^\t\t\(symbol "'+re.escape(old+':'+name)+r'"\n.*?^\t\t\)\n','',block,count=1,flags=re.S|re.M)
S=S[:i]+block+S[j:]
open(sheet,'w').write(S)
print('%s: %d symbols moved to %s (%d names)'%(sheet.split('/')[-1],n,new,len(swapped)))
