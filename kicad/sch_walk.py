"""Read a .kicad_sch as geometry: wires, labels, junctions, no-connects, and every
symbol pin placed at its sheet position.

    python3 sch_walk.py <sheet.kicad_sch> <x_mm> <y_mm>     # what touches that point

    from sch_walk import Sheet
    s = Sheet('Okapi_2.kicad_sch'); s.syms['R36']; s.at_point((337.82, 88.9))

A wire end that at_point reports as touching nothing but its own wire is a
dangling end; one that touches a second wire's interior without a junction is a
crossing. ERC's JSON gives the connected end of a dangling wire, not the free
one, so diagnose from here.
"""
import math,sys
from sexp import parse,kids,kid
def near(a,b,t=1e-3): return abs(a[0]-b[0])<t and abs(a[1]-b[1])<t
def on_seg(p,a,b,t=0.01):
    ax,ay=a; bx,by=b; px,py=p
    L=math.hypot(bx-ax,by-ay)
    if L<1e-9: return False
    cross=abs((bx-ax)*(py-ay)-(by-ay)*(px-ax))/L
    dot=((px-ax)*(bx-ax)+(py-ay)*(by-ay))/L
    return cross<t and -t<=dot<=L+t
def place(x,y,rot,mirror,px,py):
    r=math.radians(rot); cx,cy=px*math.cos(r)-py*math.sin(r), px*math.sin(r)+py*math.cos(r)
    if mirror=='x': cy=-cy
    if mirror=='y': cx=-cx
    return (round(x+cx,3),round(y-cy,3))
class Sheet:
    def __init__(self,f):
        self.f=f; self.t=parse(open(f).read())
        self.wires=[]
        for w in kids(self.t,'wire'):
            a,b=[(float(q[1]),float(q[2])) for q in kids(kid(w,'pts'),'xy')]; self.wires.append((a,b))
        self.labels=[]
        for k in ('global_label','label','hierarchical_label'):
            for l in kids(self.t,k):
                at=kid(l,'at'); self.labels.append((k,l[1],(float(at[1]),float(at[2]))))
        self.juncs=[(float(kid(j,'at')[1]),float(kid(j,'at')[2])) for j in kids(self.t,'junction')]
        self.ncs=[(float(kid(j,'at')[1]),float(kid(j,'at')[2])) for j in kids(self.t,'no_connect')]
        libp={}
        for s in kids(kid(self.t,'lib_symbols'),'symbol'):
            out=[]
            for u in kids(s,'symbol'):
                for p in kids(u,'pin'):
                    at=kid(p,'at'); out.append((kid(p,'name')[1],kid(p,'number')[1],float(at[1]),float(at[2])))
            libp[s[1]]=out
        self.pins=[]; self.syms={}
        for s in kids(self.t,'symbol'):
            at=kid(s,'at'); ref=[p[2] for p in kids(s,'property') if p[1]=='Reference'][0]
            lib=kid(s,'lib_id')[1]; mir=kid(s,'mirror'); mir=mir[1] if mir else None
            x,y=float(at[1]),float(at[2]); rot=float(at[3]) if len(at)>3 else 0
            self.syms[ref]=(lib,x,y,rot,mir)
            for name,num,px,py in libp.get(lib,[]):
                self.pins.append((ref,num,name,place(x,y,rot,mir,px,py)))
    def at_point(self,P,exclude=None):
        out=[]
        for r,n,nm,e in self.pins:
            if near(e,P): out.append(('pin',r+'.'+n))
        for k,n,a in self.labels:
            if near(a,P): out.append((k,n))
        for j in self.juncs:
            if near(j,P): out.append(('junction',''))
        for j in self.ncs:
            if near(j,P): out.append(('no_connect',''))
        for w in self.wires:
            if exclude is not None and w==exclude: continue
            if on_seg(P,w[0],w[1]): out.append(('wire',''))
        return out
if __name__=='__main__':
    s=Sheet(sys.argv[1]); P=(float(sys.argv[2]),float(sys.argv[3]))
    for kind,name in s.at_point(P): print(kind,name)
