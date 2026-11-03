#!/usr/bin/env python3
"""Lift a region of one KiCad sheet into another sheet, as text.

    sheet_lift.py <src.kicad_sch> <dst.kicad_sch> --rect X0 X1 Y0 Y1 [--rect ...]
                  --translate DX DY [--new --uuid UUID [--paper NAME] [--date D] [--rev R]]
                  [--dry-run]

Every item whose anchor lies inside one of the rectangles (a symbol by its
own (at ...), a wire or polyline by every point, a label, junction,
no-connect or text by its (at ...)) moves to the destination sheet,
translated by (DX, DY) mm; give whole grid ticks (multiples of 1.27). A
wire with one end inside and one outside stops the run: cut nothing. The
lib_symbols entries the moved symbols need are copied into the destination
and those the source no longer uses are dropped from it. With --new the
destination is created with the given uuid (use the uuid the root's sheet
symbol will carry), paper and title block. Run `kicad-cli sch upgrade
--force` on both files afterwards to let KiCad order the items, then
roundtrip.sh.
"""
import re, sys

HEAD_KINDS = ('version', 'generator', 'generator_version', 'uuid', 'paper', 'title_block', 'lib_symbols')
STAY = ('sheet_instances', 'symbol_instances', 'embedded_fonts')

def fmt(v):
    s = ('%.6f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s

def split_items(t):
    """Top-level items of a .kicad_sch: list of (kind, text) in file order, plus the closing text."""
    assert t.startswith('(kicad_sch\n')
    body = t[len('(kicad_sch\n'):]
    items = []
    i = 0
    n = len(body)
    while i < n:
        if body.startswith('\t(', i):
            depth = 0
            j = i
            in_str = False
            while True:
                c = body[j]
                if c == '"' and body[j - 1] != '\\':
                    in_str = not in_str
                elif not in_str:
                    if c == '(':
                        depth += 1
                    elif c == ')':
                        depth -= 1
                        if depth == 0:
                            break
                j += 1
            assert body[j + 1] == '\n'
            item = body[i:j + 2]
            kind = re.match(r'\t\((\S+)', item).group(1)
            items.append([kind, item])
            i = j + 2
        elif body.startswith(')', i):
            return items, body[i:]
        else:
            raise SystemExit('unexpected text at %d: %r' % (i, body[i:i + 40]))
    raise SystemExit('no closing paren')

def anchor_points(kind, item):
    if kind in ('wire', 'polyline', 'bus'):
        return [(float(a), float(b)) for a, b in re.findall(r'\(xy (-?[\d.]+) (-?[\d.]+)\)', item)]
    m = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)', item)
    return [(float(m.group(1)), float(m.group(2)))] if m else []

def inside(p, rects):
    return any(x0 <= p[0] < x1 and y0 <= p[1] < y1 for x0, x1, y0, y1 in rects)

def translate(item, dx, dy):
    return re.sub(r'\((at|xy|start|end|center|mid) (-?[\d.]+) (-?[\d.]+)',
                  lambda m: '(%s %s %s' % (m.group(1), fmt(float(m.group(2)) + dx), fmt(float(m.group(3)) + dy)), item)

def lib_entries(lib_block):
    """The (symbol "lib:name" ...) entries of a lib_symbols block, as {name: text}."""
    out = {}
    for m in re.finditer(r'\t\t\(symbol "([^"]*)"\n(?:.*\n)*?\t\t\)\n', lib_block):
        out[m.group(1)] = m.group(0)
    return out

def build_lib_block(entries):
    if not entries:
        return '\t(lib_symbols)\n'
    return '\t(lib_symbols\n' + ''.join(entries[k] for k in sorted(entries)) + '\t)\n'

def used_lib_ids(items):
    ids = set()
    for kind, item in items:
        if kind == 'symbol':
            ids.add(re.search(r'\(lib_id "([^"]*)"\)', item).group(1))
    return ids

def main():
    a = sys.argv[1:]
    rects = []
    while '--rect' in a:
        i = a.index('--rect')
        rects.append(tuple(float(v) for v in a[i + 1:i + 5]))
        del a[i:i + 5]
    i = a.index('--translate')
    dx, dy = float(a[i + 1]), float(a[i + 2])
    del a[i:i + 3]
    new = '--new' in a
    if new:
        a.remove('--new')
    opts = {}
    for k in ('--uuid', '--paper', '--date', '--rev'):
        if k in a:
            i = a.index(k)
            opts[k] = a[i + 1]
            del a[i:i + 2]
    dry = '--dry-run' in a
    if dry:
        a.remove('--dry-run')
    src, dst = a
    t = open(src).read()
    items, closing = split_items(t)
    head = [it for it in items if it[0] in HEAD_KINDS]
    lib = [it for it in head if it[0] == 'lib_symbols'][0][1]
    moving, staying = [], []
    for kind, item in items:
        if kind in HEAD_KINDS or kind in STAY:
            continue
        pts = anchor_points(kind, item)
        if not pts:
            staying.append([kind, item])
            continue
        flags = [inside(p, rects) for p in pts]
        if all(flags):
            moving.append([kind, item])
        elif any(flags):
            raise SystemExit('%s straddles the region: %s' % (kind, item[:120]))
        else:
            staying.append([kind, item])
    refs = sorted(re.search(r'\(property "Reference" "([^"]*)"', it[1]).group(1) for it in moving if it[0] == 'symbol')
    counts = {}
    for kind, _ in moving:
        counts[kind] = counts.get(kind, 0) + 1
    print('%s -> %s: moving %s; symbols %s' % (src, dst, counts, ' '.join(refs)))
    if dry:
        return
    moved = [[k, translate(it, dx, dy)] for k, it in moving]
    src_entries = lib_entries(lib)
    need = used_lib_ids(moved)
    keep = used_lib_ids(staying)
    # source: head with pruned lib_symbols, staying items, closing
    new_lib = build_lib_block({k: v for k, v in src_entries.items() if k in keep})
    src_out = '(kicad_sch\n' + ''.join(it[1] if it[0] != 'lib_symbols' else new_lib for it in head) + ''.join(it[1] for it in staying) + closing
    open(src, 'w').write(src_out)
    # destination
    if new:
        dhead = ['\t(version 20260306)\n', '\t(generator "eeschema")\n', '\t(generator_version "10.0")\n',
                 '\t(uuid "%s")\n' % opts['--uuid'], '\t(paper "%s")\n' % opts.get('--paper', 'USLetter')]
        tb = ''.join('\t\t(%s "%s")\n' % (k, opts['--' + k]) for k in ('date', 'rev') if '--' + k in opts)
        if tb:
            dhead.append('\t(title_block\n' + tb + '\t)\n')
        dlib = {k: src_entries[k] for k in need}
        dst_out = '(kicad_sch\n' + ''.join(dhead) + build_lib_block(dlib) + ''.join(it[1] for it in moved) + ')\n'
    else:
        d = open(dst).read()
        ditems, dclosing = split_items(d)
        dhead = [it for it in ditems if it[0] in HEAD_KINDS]
        dlib_block = [it for it in dhead if it[0] == 'lib_symbols'][0][1]
        dlib = lib_entries(dlib_block)
        for k in need:
            if k not in dlib:
                dlib[k] = src_entries[k]
        rest = [it for it in ditems if it[0] not in HEAD_KINDS]
        dst_out = '(kicad_sch\n' + ''.join(it[1] if it[0] != 'lib_symbols' else build_lib_block(dlib) for it in dhead) + ''.join(it[1] for it in rest) + ''.join(it[1] for it in moved) + dclosing
    open(dst, 'w').write(dst_out)
    print('  lib_symbols: destination holds %d, source keeps %d of %d' % (len(dlib), len(keep & set(src_entries)), len(src_entries)))

if __name__ == '__main__':
    main()
