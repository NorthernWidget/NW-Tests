"""Set fields of placed symbols, by reference, as the GUI's symbol properties dialog would.

usage: set_fields.py <kicad dir> REF[,REF...] FIELD=VALUE [FIELD=VALUE ...] [--dry-run]

Every listed reference must be one placed symbol in the directory's sheets,
or the run stops before anything is written. An existing field keeps its
position and form and takes the new value; a missing field is added in the
importer's form (eagle_fields.field: hidden, at the symbol's anchor). Value
is the mandatory field and must exist. Afterwards carry the change to the
board with link_paths.py --values --fields, then the usual checks.
"""
import sys, os, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eagle_fields import field, quote

def main():
    a = sys.argv[1:]; dry = '--dry-run' in a
    if dry: a.remove('--dry-run')
    kdir, refs = a[0], a[1].split(',')
    sets = [kv.split('=', 1) for kv in a[2:]]
    found = {r: 0 for r in refs}; out = {}; log = []
    for f in sorted(glob.glob(os.path.join(kdir, '*.kicad_sch'))):
        t = open(f).read()
        def sub(m):
            b = m.group(0)
            ref = re.search(r'^\t\t\(property "Reference" "([^"]*)"', b, re.M).group(1)
            if ref not in found: return b
            found[ref] += 1
            x, y = re.search(r'^\t\t\(at (\S+) (\S+)', b, re.M).groups()
            for name, v in sets:
                pat = r'^(\t\t\(property "%s" ")((?:[^"\\]|\\.)*)(")' % re.escape(name)
                have = re.search(pat, b, re.M)
                if have:
                    log.append((ref, name, have.group(2), v))
                    b = b[:have.start()] + have.group(1) + quote(v) + have.group(3) + b[have.end():]
                else:
                    if name == 'Value': sys.exit('%s has no Value field' % ref)
                    props = list(re.finditer(r'^\t\t\(property "([^"]+)".*?^\t\t\)\n', b, re.S | re.M))
                    later = [p for p in props if p.group(1) not in ('Reference', 'Value', 'Footprint', 'Datasheet', 'Description') and p.group(1) > name]
                    pos = later[0].start() if later else props[-1].end()
                    b = b[:pos] + field(name, v, x, y) + b[pos:]
                    log.append((ref, name, None, v))
            return b
        t2 = re.sub(r'^\t\(symbol\n.*?^\t\)\n', sub, t, flags=re.S | re.M)
        if t2 != t: out[f] = t2
    bad = {r: n for r, n in found.items() if n != 1}
    if bad: sys.exit('each reference must be placed exactly once: %s; nothing written' % bad)
    for ref, name, old, new in log: print('%s %s: %r -> %r' % (ref, name, old, new))
    if not dry:
        for f, t2 in out.items(): open(f, 'w').write(t2)

if __name__ == '__main__': main()
