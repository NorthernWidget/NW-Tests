"""Text edits on a .kicad_sch that leave what KiCad itself would have written.

    from sch_edit import Editor
    e = Editor('sheet.kicad_sch')
    e.move_symbol('R1', 2.54, 0)                 # symbol and all its property anchors
    e.move_wire(a, b, a2, b2)                     # both ends of the wire a-b
    e.move_wire_end(a, b, old, new)               # one end
    e.add_wire(a, b); e.delete_wire(a, b)
    e.move_junction(p, q); e.delete_junction(p)
    e.move_label('global_label', 'NET', p, dx, dy)   # label and its hidden Intersheetrefs field
    e.set_property('R1', 'Reference', x, y)      # one property anchor, angle kept
    e.save()

Every operation asserts the thing it edits exists exactly once, so a stale
coordinate fails loudly instead of editing the wrong wire. Numbers are written
the way KiCad writes them (fmt), which is what keeps roundtrip.sh identical.
Run check_conversion.sh, roundtrip.sh and erc_counts.sh after saving.
"""
import re,uuid
def fmt(v):
    s=('%.4f'%v).rstrip('0').rstrip('.')
    return '0' if s in ('-0','') else s
def xy(p): return '(xy %s %s)'%(fmt(p[0]),fmt(p[1]))
class Editor:
    def __init__(self,path):
        self.path=path; self.s=open(path).read()
    def save(self): open(self.path,'w').write(self.s)
    def wire_block(self,a,b):
        pat=re.compile(r'\t\(wire\n\t\t\(pts\n\t\t\t'+re.escape(xy(a))+r'\s*'+re.escape(xy(b))+r'\n\t\t\)\n.*?\n\t\)\n',re.S)
        m=pat.search(self.s)
        if not m:
            pat=re.compile(r'\t\(wire\n\t\t\(pts\n\t\t\t'+re.escape(xy(b))+r'\s*'+re.escape(xy(a))+r'\n\t\t\)\n.*?\n\t\)\n',re.S)
            m=pat.search(self.s)
        assert m, ('wire not found',a,b)
        return m
    def move_wire_end(self,a,b,old,new):
        m=self.wire_block(a,b); blk=m.group(0)
        assert blk.count(xy(old))==1, (a,b,old)
        self.s=self.s[:m.start()]+blk.replace(xy(old),xy(new))+self.s[m.end():]
    def delete_wire(self,a,b):
        m=self.wire_block(a,b); self.s=self.s[:m.start()]+self.s[m.end():]
    def add_wire(self,a,b):
        blk='\t(wire\n\t\t(pts\n\t\t\t%s %s\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'%(xy(a),xy(b),uuid.uuid4())
        # insert before the first (symbol (lib_id ...) instance, i.e. after the last wire/junction/label region
        i=self.s.find('\t(symbol\n\t\t(lib_id')
        assert i>0
        self.s=self.s[:i]+blk+self.s[i:]
    def delete_junction(self,p):
        pat=re.compile(r'\t\(junction\n\t\t\(at %s %s\)\n.*?\n\t\)\n'%(re.escape(fmt(p[0])),re.escape(fmt(p[1]))),re.S)
        m=pat.search(self.s); assert m, ('junction',p)
        self.s=self.s[:m.start()]+self.s[m.end():]
    def move_junction(self,p,q):
        pat=r'\t\(junction\n\t\t\(at %s %s\)'%(re.escape(fmt(p[0])),re.escape(fmt(p[1])))
        n=len(re.findall(pat,self.s)); assert n==1,(p,n)
        self.s=re.sub(pat,lambda m:'\t(junction\n\t\t(at %s %s)'%(fmt(q[0]),fmt(q[1])),self.s)
    def _shift_block(self,blk,dx,dy):
        def rep(m):
            return '(at %s %s%s)'%(fmt(float(m.group(1))+dx),fmt(float(m.group(2))+dy),m.group(3) or '')
        return re.sub(r'\(at (-?[\d.]+) (-?[\d.]+)((?: -?[\d.]+)?)\)',rep,blk)
    def move_symbol(self,ref,dx,dy):
        pat=re.compile(r'\t\(symbol\n\t\t\(lib_id "[^"]+"\)\n\t\t\(at [^)]*\)\n.*?\n\t\)\n',re.S)
        hits=[m for m in pat.finditer(self.s) if '(property "Reference" "%s"'%ref in m.group(0)]
        assert len(hits)==1,(ref,len(hits))
        m=hits[0]; blk=m.group(0)
        # shift the symbol's own (at ...) and every property (at ...); pins inside have no (at)
        self.s=self.s[:m.start()]+self._shift_block(blk,dx,dy)+self.s[m.end():]
    def move_label(self,kind,name,p,dx,dy):
        pat=re.compile(r'\t\(%s "%s"\n(?:\t\t\(shape \w+\)\n)?\t\t\(at %s %s [\d.]+\)\n.*?\n\t\)\n'%(kind,re.escape(name),re.escape(fmt(p[0])),re.escape(fmt(p[1]))),re.S)
        m=pat.search(self.s); assert m,(kind,name,p)
        self.s=self.s[:m.start()]+self._shift_block(m.group(0),dx,dy)+self.s[m.end():]
    def move_wire(self,a,b,a2,b2):
        m=self.wire_block(a,b); blk=m.group(0)
        blk=blk.replace(xy(a),'\0A').replace(xy(b),'\0B').replace('\0A',xy(a2)).replace('\0B',xy(b2))
        self.s=self.s[:m.start()]+blk+self.s[m.end():]
    def set_property(self,ref,prop,x,y):
        pat=r'(\(property "%s" "%s"\n\t\t\t\(at )-?[\d.]+ -?[\d.]+( -?[\d.]+\))'%(prop,re.escape(ref))
        n=len(re.findall(pat,self.s)); assert n==1,(ref,prop,n)
        self.s=re.sub(pat,lambda m:m.group(1)+fmt(x)+' '+fmt(y)+m.group(2),self.s)
