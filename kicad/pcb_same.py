"""Is a board functionally and geometrically the same as another (before/after a re-body)?

    pcb_same.py <before.kicad_pcb> <after.kicad_pcb>

Compares, through KiCad's pcbnew module: every footprint's placement (position,
rotation, side, footprint name); every pad (net, position, size, shape, rotation,
drill, type, layers, corner ratio); every track and via; and the board's zones.
Prints one line per group with "identical: True/False" and the first keys that
differ. Put the board's .kicad_pro beside a saved copy, or KiCad reads default rules.
"""
import pcbnew,sys
def snap(p):
    b=pcbnew.LoadBoard(p); fp={}; pads={}
    for f in b.GetFootprints():
        r=f.GetReference(); q=f.GetPosition()
        fp[r]=(q.x,q.y,round(f.GetOrientationDegrees(),6),f.IsFlipped(),str(f.GetFPID().GetLibItemName()))
        for i,pd in enumerate(f.Pads()):
            p0=pd.GetPosition(); s=pd.GetSize(pcbnew.F_Cu); d=pd.GetDrillSize()
            k=(r,pd.GetNumber(),p0.x,p0.y)
            pads[k]=(pd.GetNetname(),s.x,s.y,int(pd.GetShape(pcbnew.F_Cu)),round(pd.GetOrientationDegrees(),6),d.x,d.y,int(pd.GetDrillShape()),int(pd.GetAttribute()),pd.GetLayerSet().FmtHex(),round(pd.GetRoundRectRadiusRatio(pcbnew.F_Cu),6))
    trk=sorted((t.GetClass(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y,(t.GetWidth(pcbnew.F_Cu) if t.GetClass()=="PCB_VIA" else t.GetWidth()),t.GetLayer(),t.GetNetname()) for t in b.GetTracks())
    zones=sorted((z.GetNetname(),z.GetLayerSet().FmtHex(),z.GetNumCorners(),z.GetIsRuleArea()) for z in b.Zones())
    return fp,pads,trk,zones
a=snap(sys.argv[1]); c=snap(sys.argv[2])
for name,x,y in zip(('footprint placements','pads (net, position, size, shape, rotation, drill, type, layers)','tracks and vias','board zones'),a,c):
    same=x==y
    print(f'{name}: {len(x)} before, {len(y)} after, identical: {same}')
    if not same and isinstance(x,dict):
        ks=set(x)^set(y); print('  keys differ',list(ks)[:6]); print('  values differ',[k for k in set(x)&set(y) if x[k]!=y[k]][:6])
