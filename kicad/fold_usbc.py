"""fold_usbc.py <kicad.json> <out.json> <REF>: fold REF's split USB-C pads back to Eagle's combined numbers
(A1,B12 -> A1B12; B1,A12 -> B1A12; A4,B9 -> A4B9; B4,A9 -> B4A9), so the Eagle comparison sees one pin per pad."""
import json,sys
MAP={'A1':'A1B12','B12':'A1B12','B1':'B1A12','A12':'B1A12','A4':'A4B9','B9':'A4B9','B4':'B4A9','A9':'B4A9'}
k=json.load(open(sys.argv[1])); ref=sys.argv[3]; seen=0
for name,pins in k['nets'].items():
    out=[]
    for p in pins:
        if p[0]==ref and p[1] in MAP: p=[p[0],MAP[p[1]]]+p[2:]; seen+=1
        if not any(q[0]==p[0] and q[1]==p[1] for q in out): out.append(p)
    k['nets'][name]=out
json.dump(k,open(sys.argv[2],'w')); print('folded',seen,'pins of',ref)
