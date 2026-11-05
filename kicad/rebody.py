"""Replace every board footprint's body with its library footprint, keeping the placement.

usage: rebody.py <board.kicad_pcb> <nickname> <library.pretty> [--only REF,REF] [--report out.json]

For each footprint named <nickname>:<name>, the pads and graphics of the
instance are replaced by the library's, transformed to the instance: positions
are local already; angles gain the instance rotation; on the back side y is
mirrored, layers swap F/B, and pad and text angles become rotation minus the
library angle (derived from every back-side instance on two boards). Each pad
keeps the net the instance's pad of the same number had. The instance keeps
its placement, uuid, properties (reference, value, BOM fields), path and
attributes, in their order; KiCad's trailing items (embedded_fonts) stay last.
The library's (attr ...) line is the part's and is taken, with any
placement-only attribute the instance carried kept beside it.
New body items get fresh uuids, as KiCad gives on placement.

The report lists, per footprint, pads whose number exists on one side only
and pads whose position or size moved, so the places where tracks may now
miss or overlap are known before DRC is run. Afterwards: kicad-cli pcb upgrade
on a copy must return the file unchanged, and the pad-net table must be
identical by (reference, pad).
"""
import sys,os,re,uuid,json
BODY=('fp_line','fp_poly','fp_circle','fp_arc','fp_rect','fp_text','pad','model','zone','group')
def fmt(v):
    s=('%.6f'%v).rstrip('0').rstrip('.'); return '0' if s in ('-0','') else s   # KiCad writes up to six decimals and compares exactly
def items(block,depth):
    """Split a block into (head lines, [item texts], tail): items open at this tab depth; the block closes one depth up."""
    ind='\t'*depth; close='\t'*(depth-1)+')'
    lines=block.split('\n'); head=[]; its=[]; cur=None; tail=[]
    for i,l in enumerate(lines):
        if l==close:
            if cur: its.append(cur); cur=None
            tail=lines[i:]; break
        if l.startswith(ind+'('):
            if cur: its.append(cur)
            cur=[l]
        elif cur is not None: cur.append(l)
        else: head.append(l)
    if cur: its.append(cur)
    return head,['\n'.join(x) for x in its],'\n'.join(tail)
def kind(item): return re.match(r'\s*\((\S+)',item).group(1)
def swap_layers(t): return re.sub(r'"([FB])\.',lambda m:'"'+('B' if m.group(1)=='F' else 'F')+'.',t)
def transform(item,rot,back,pos=(0.0,0.0),copper=None):
    k=kind(item)
    if k=='zone':
        # A footprint zone's polygon is written in board coordinates (pads and graphics are local):
        # mirror for the back side, rotate by the instance angle, translate to the instance.
        import math
        c,s=math.cos(math.radians(rot)),math.sin(math.radians(rot))
        def xy(m):
            lx,ly=float(m.group(1)),float(m.group(2))
            if back: ly=-ly
            return '(xy %s %s)'%(fmt(pos[0]+lx*c+ly*s),fmt(pos[1]-lx*s+ly*c))
        item=re.sub(r'\(xy (-?[\d.]+) (-?[\d.]+)\)',xy,item)
        if copper:   # the library lists every copper layer; the board holds only its own
            def layers(m):
                names=re.findall(r'"[^"]*"',m.group(1))
                keep=[n for n in names if not n.endswith('.Cu"') or n in copper]
                return '(layers %s)'%' '.join(keep)
            item=re.sub(r'\(layers ((?:\s*"[^"]*")+)\s*\)',layers,item,count=1)
        if back: item=swap_layers(item)
        return re.sub(r'\(uuid "[^"]+"\)',lambda m:'(uuid "%s")'%uuid.uuid4(),item)
    if back:
        item=re.sub(r'\((start|end|mid|center|xy) (-?[\d.]+) (-?[\d.]+)\)',lambda m:'(%s %s %s)'%(m.group(1),m.group(2),fmt(-float(m.group(3)))),item)
        item=swap_layers(item)
    def at(m):
        x,y,a=m.group(1),float(m.group(2)),float(m.group(3) or 0)
        if back: y=-y; a=(rot-a)%360
        else: a=(a+rot)%360   # KiCad 10 writes angles in [0, 360)
        return '(at %s %s%s)'%(x,fmt(y),'' if a==0 else ' '+fmt(a))
    if k in ('pad','fp_text'): item=re.sub(r'\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)',at,item,count=1)
    if k=='fp_text' and back and '(justify mirror)' not in item:
        item=re.sub(r'\n(\t+)\)\n(\t+)\)\s*$',lambda m:'\n'+m.group(1)+'\t(justify mirror)\n'+m.group(1)+')\n'+m.group(2)+')',item)
    return re.sub(r'\(uuid "[^"]+"\)',lambda m:'(uuid "%s")'%uuid.uuid4(),item)
def padinfo(item):
    num=re.match(r'\s*\(pad "([^"]*)"',item).group(1)
    at=re.search(r'\(at (-?[\d.]+) (-?[\d.]+)',item); sz=re.search(r'\(size (-?[\d.]+) (-?[\d.]+)',item)
    net=re.search(r'\((net (?:\d+ )?"[^"]*")\)',item)
    return num,(float(at.group(1)),float(at.group(2))),(float(sz.group(1)),float(sz.group(2))),net.group(1) if net else None
def rebody_block(block,libitems,copper=None):
    """One footprint block of a board, re-bodied from the library's items. Returns (new block, report dict or None)."""
    head,its,tail=items(block,2)
    layer=re.search(r'^\t\t\(layer "([^"]+)"\)',block,re.M).group(1); back=layer.startswith('B.')
    atm=re.search(r'^\t\t\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)',block,re.M); rot=float(atm.group(3) or 0); pos=(float(atm.group(1)),float(atm.group(2)))
    isbody=[kind(i) in BODY for i in its]
    first=isbody.index(True) if any(isbody) else len(its)
    keep_before=[i for j,i in enumerate(its) if not isbody[j] and j<first]
    # descr and tags are the library's: take them from it (after the instance's (at ...) line, where KiCad writes them)
    libmeta=[i for i in libitems if kind(i) in ('descr','tags')]
    keep_before=[i for i in keep_before if kind(i) not in ('descr','tags')]
    if libmeta:
        k=[j for j,i in enumerate(keep_before) if kind(i)=='at']
        pos_i=(k[0]+1) if k else len(keep_before)
        keep_before[pos_i:pos_i]=['\t'+i for i in libmeta]
    keep_after=[i for j,i in enumerate(its) if not isbody[j] and j>=first]
    # the library's (attr ...) is the part's (through_hole, smd, allow_soldermask_bridges, ...): the instance takes it,
    # keeping any placement-only attribute it carried (board_only, exclude_from_pos_files, exclude_from_bom, dnp)
    libattr=[i for i in libitems if kind(i)=='attr']
    if libattr:
        libwords=libattr[0].strip()[len('(attr '):-1].split()
        mine=[i for i in keep_before+keep_after if kind(i)=='attr']
        placement=[w for w in (mine[0].strip()[len('(attr '):-1].split() if mine else []) if w in ('board_only','exclude_from_pos_files','exclude_from_bom','dnp')]
        line='\t\t(attr %s)'%' '.join(libwords+[w for w in placement if w not in libwords])
        keep_before=[i for i in keep_before if kind(i)!='attr']; keep_after=[i for i in keep_after if kind(i)!='attr']
        k=[j for j,i in enumerate(keep_before) if kind(i)=='sheetfile']
        keep_before.insert((k[0]+1) if k else len(keep_before),line)
    # whether same-numbered pads are one terminal (KiCad 9+): the library's word replaces the instance's
    libjump=[i for i in libitems if kind(i)=='duplicate_pad_numbers_are_jumpers']
    if libjump:
        line='\t'+libjump[0].strip()
        had=[i for i in keep_before+keep_after if kind(i)=='duplicate_pad_numbers_are_jumpers']
        keep_before=[i for i in keep_before if kind(i)!='duplicate_pad_numbers_are_jumpers']; keep_after=[i for i in keep_after if kind(i)!='duplicate_pad_numbers_are_jumpers']
        k=[j for j,i in enumerate(keep_before) if kind(i) in ('attr','sheetfile')]
        keep_before.insert((k[-1]+1) if k else len(keep_before),'\t'+line)
    old={}
    for i in its:
        if kind(i)=='pad':
            p=padinfo(i); old.setdefault(p[0],p)
    new=[]; pads_new={}
    for li in libitems:
        if kind(li) not in BODY: continue
        ti='\n'.join('\t'+l for l in transform(li,rot,back,pos,copper).split('\n'))
        if kind(li)=='pad':
            num=padinfo(ti)[0]
            if num in old and old[num][3]:
                ti=re.sub(r'(\(layers [^)]*\)\n)',lambda m:m.group(1)+'\t\t\t(%s)\n'%old[num][3],ti,count=1)
            pads_new.setdefault(num,padinfo(ti))
        new.append(ti)
    r={'layer':layer,'rot':rot,'pads_only_on_board':sorted(set(old)-set(pads_new)),'pads_only_in_library':sorted(set(pads_new)-set(old)),'pads_moved':[]}
    for num in set(old)&set(pads_new):
        o=old[num]; q=pads_new[num]
        if any(abs(o[1][i]-q[1][i])>0.0005 for i in (0,1)) or any(abs(o[2][i]-q[2][i])>0.0005 for i in (0,1)):
            r['pads_moved'].append({'pad':num,'board':[o[1],o[2]],'library':[q[1],q[2]]})
    changed=r['pads_only_on_board'] or r['pads_only_in_library'] or r['pads_moved']
    return '\n'.join(head+keep_before+new+keep_after)+'\n'+tail, (r if changed else None)
def main():
    a=sys.argv[1:]; only=None; report=None
    if '--only' in a: i=a.index('--only'); only=set(a[i+1].split(',')); del a[i:i+2]
    if '--report' in a: i=a.index('--report'); report=a[i+1]; del a[i:i+2]
    pcb,nick,pretty=a
    lib={}; rep={}; n=[0]
    t=open(pcb).read()
    copper=set(re.findall(r'^\t\t\(\d+ ("[A-Za-z0-9]+\.Cu")',t,re.M))   # the board's own copper layers
    def sub(m):
        block=m.group(0); name=m.group(1)
        if not name.startswith(nick+':'): return block
        ref=re.search(r'\(property "Reference" "([^"]*)"',block).group(1)
        if only and ref not in only: return block
        fname=name.split(':',1)[1]
        if fname not in lib: lib[fname]=items(open(os.path.join(pretty,fname+'.kicad_mod')).read(),1)[1]
        out,r=rebody_block(block,lib[fname],copper); n[0]+=1
        if r: r['name']=fname; rep[ref]=r
        return out
    t2=re.sub(r'^\t\(footprint "([^"]+)"\n.*?^\t\)\n',sub,t,flags=re.S|re.M)
    open(pcb,'w').write(t2)
    if report: json.dump(rep,open(report,'w'),indent=1)
    print('footprints re-bodied: %d; with a pad change: %d'%(n[0],len(rep)))
    for ref,r in sorted(rep.items()): print(' ',ref,r['name'],'only on board',r['pads_only_on_board'],'only in library',r['pads_only_in_library'],'moved',[(p['pad'],p['board'],p['library']) for p in r['pads_moved']][:3])
if __name__=='__main__': main()
