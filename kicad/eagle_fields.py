"""Write each Eagle part's BOM attributes into its KiCad symbol as fields.

usage: eagle_fields.py <eagle.sch> <kicad dir> --fields DIGIKEY,DISP,MF,MPN [--rename MFP=MPN] [--dry-run]

An Eagle part's attributes are its device's technology attributes (the
technology the part names) overlaid by the part's own, as Eagle's bom.ulp
resolves them (Project-Margay Production/tools/eagle_bom.py, which reproduces
Eagle's export byte for byte). The KiCad importer carried only some of them.
For every placed symbol in every .kicad_sch of the directory, matched by
reference, each listed field with a non-empty Eagle value is added as the
importer wrote such fields: hidden, at the symbol's anchor, angle 0, justify
left bottom, in alphabetical order among the listed fields already there.
A field already present with the same value is left alone; one with another
value stops the run before anything is written. --rename OLD=NEW reads an
Eagle attribute under a misspelled name (D8's MFP on Okapi) as NEW, and stops
if a part carries both. Run check_conversion.sh, roundtrip.sh and ERC after.
"""
import sys, os, re, glob, xml.etree.ElementTree as ET

def eagle_attrs(sch):
    root = ET.parse(sch).getroot()
    libs = {}
    for lib in root.iter('library'):
        libs[(lib.get('name'), lib.get('urn') or '')] = lib
    def find_lib(name, urn):
        for (n, u), l in libs.items():
            if n == name and (u == (urn or '') or not urn): return l
    out = {}
    for p in root.iter('part'):
        lib = find_lib(p.get('library'), p.get('library_urn'))
        ds = next(d for d in lib.iter('deviceset') if d.get('name') == p.get('deviceset'))
        dev = next(d for d in ds.iter('device') if d.get('name') == p.get('device'))
        if dev.get('package') is None: continue          # supply symbols, frames
        tech = p.get('technology') or ''
        attrs = {}
        for t in dev.iter('technology'):
            if t.get('name') == tech:
                attrs.update({a.get('name'): a.get('value') or '' for a in t.findall('attribute')})
        attrs.update({a.get('name'): a.get('value') or '' for a in p.findall('attribute')})
        out[p.get('name')] = attrs
    return out

def quote(s): return s.replace('\\', '\\\\').replace('"', '\\"')

def field(name, value, x, y):
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n'
            '\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n'
            '\t\t\t\t)\n\t\t\t\t(justify left bottom)\n\t\t\t)\n\t\t)\n') % (name, quote(value), x, y)

def main():
    a = sys.argv[1:]
    dry = '--dry-run' in a
    if dry: a.remove('--dry-run')
    rename = {}
    while '--rename' in a:
        i = a.index('--rename'); old, new = a[i+1].split('='); rename[old] = new; del a[i:i+2]
    i = a.index('--fields'); fields = sorted(a[i+1].split(',')); del a[i:i+2]
    sch, kdir = a
    eag = eagle_attrs(sch)
    for ref, at in eag.items():
        for old, new in rename.items():
            if at.get(old):
                if at.get(new): sys.exit('%s carries both %s and %s' % (ref, old, new))
                at[new] = at.pop(old); print('renamed %s %s -> %s: %s' % (ref, old, new, at[new]))
    plan = {}; conflicts = []; added = {f: 0 for f in fields}; seen = set()
    for f in sorted(glob.glob(os.path.join(kdir, '*.kicad_sch'))):
        t = open(f).read()
        def sub(m):
            b = m.group(0)
            ref = re.search(r'^\t\t\(property "Reference" "([^"]*)"', b, re.M).group(1)
            if ref.startswith('#') or ref not in eag: return b
            seen.add(ref)
            x, y = re.search(r'^\t\t\(at (\S+) (\S+)', b, re.M).groups()
            for name in fields:
                v = eag[ref].get(name, '')
                if not v: continue
                have = re.search(r'^\t\t\(property "%s" "((?:[^"\\]|\\.)*)"' % name, b, re.M)
                if have:
                    if have.group(1) != quote(v): conflicts.append((ref, name, have.group(1), v))
                    continue
                # before the first listed field already present that sorts after this one, else after the last property
                props = list(re.finditer(r'^\t\t\(property "([^"]+)".*?^\t\t\)\n', b, re.S | re.M))
                later = [p for p in props if p.group(1) in fields and p.group(1) > name]
                pos = later[0].start() if later else props[-1].end()
                b = b[:pos] + field(name, v, x, y) + b[pos:]
                added[name] += 1
            return b
        t2 = re.sub(r'^\t\(symbol\n.*?^\t\)\n', sub, t, flags=re.S | re.M)
        if t2 != t: plan[f] = t2
    if conflicts:
        for c in conflicts: print('conflict', *c)
        sys.exit('stopped: %d fields differ from Eagle; nothing written' % len(conflicts))
    print('fields added:', added, ' sheets changed:', len(plan))
    missing = sorted(set(eag) - seen)
    if missing: print('Eagle parts with no KiCad symbol:', missing)
    if not dry:
        for f, t2 in plan.items(): open(f, 'w').write(t2)

if __name__ == '__main__': main()
