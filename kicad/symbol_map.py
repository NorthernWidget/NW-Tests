"""Measure how a project's placed symbols map onto a symbol library before swapping them.

usage: symbol_map.py <root.kicad_sch> <library.kicad_sym> <old nickname> [--strip PREFIX,...]

For every placed symbol from <old nickname> across the project's sheets: the
library symbol of the same name (prefixes stripped), and whether its pins
agree with the sheet's embedded definition in number, name, position and
length. Prints the counts (same pins and geometry; same numbers, names
differ; geometry differs; pin sets differ; no library symbol; power symbols)
and lists everything but the first group. A swap is a pure change of
definition only for the first two groups; the others need rewiring, a lift
into the library, or a decision.
"""
import re,sys,os,glob,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from sexp import parse,kids,kid
a=sys.argv[1:]; strip=[]
if '--strip' in a: i=a.index('--strip'); strip=a[i+1].split(','); del a[i:i+2]
root,lib,old=a; d=os.path.dirname(os.path.abspath(root))
def pins(sym):
    out=[]
    for u in kids(sym,'symbol'):
        for p in kids(u,'pin'):
            at=kid(p,'at'); out.append((kid(p,'number')[1],kid(p,'name')[1],round(float(at[1]),2),round(float(at[2]),2),int(float(at[3])) if len(at)>3 else 0,round(float(kid(p,'length')[1]),2)))
    return sorted(out)
L={s[1]:s for s in kids(parse(open(lib).read()),'symbol')}
placed=collections.Counter(); emb={}
for f in sorted(glob.glob(os.path.join(d,'*.kicad_sch'))):
    t=parse(open(f).read())
    for s in kids(kid(t,'lib_symbols') or ['lib_symbols'],'symbol'): emb[s[1]]=s
    for s in kids(t,'symbol'):
        ref=[p[2] for p in kids(s,'property') if p[1]=='Reference'][0]; lid=kid(s,'lib_id')[1]
        if lid.split(':')[0]==old: placed[(lid,ref.startswith('#'))]+=1
def cand(name):
    n=name.split(':',1)[1]
    for c in [n]+[n[len(p):] for p in strip if n.startswith(p)]:
        if c in L: return c
rows=collections.Counter(); detail=collections.defaultdict(list)
for (lid,power),n in placed.items():
    c=cand(lid); e=emb.get(lid)
    if power: rows['power symbol']+=n; detail['power symbol'].append((lid,n)); continue
    if c is None: rows['no library symbol']+=n; detail['no library symbol'].append((lid,n)); continue
    pe,pl=pins(e),pins(L[c])
    if pe==pl: rows['same pins and geometry']+=n
    elif [(p[0],)+p[2:] for p in pe]==[(p[0],)+p[2:] for p in pl]: rows['same numbers and geometry, names differ']+=n; detail['names differ'].append((lid,c,n,[(x[1],y[1]) for x,y in zip(pe,pl) if x[1]!=y[1]][:4]))
    elif sorted(p[0] for p in pe)==sorted(p[0] for p in pl): rows['same numbers, geometry differs']+=n; detail['geometry differs'].append((lid,c,n))
    else: rows['pin sets differ']+=n; detail['pin sets differ'].append((lid,c,n,len(pe),len(pl)))
print('placed from %s: %d'%(old,sum(placed.values())),dict(rows))
for k in ('names differ','geometry differs','pin sets differ','no library symbol','power symbol'):
    if detail[k]: print('==',k); [print('  ',x) for x in detail[k]]
