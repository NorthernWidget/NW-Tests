#!/usr/bin/env python3
"""Rewrite the sheet symbols of a root schematic from an ordered list.

    root_sheets.py <root.kicad_sch> <sheets.json> [--paper NAME]

sheets.json is a list of {"name": ..., "file": ..., "uuid": ...} in page
order; page numbers start at 2 (the root is page 1). Every existing sheet
symbol is replaced; one that keeps its uuid keeps its place in the
hierarchy, so footprint paths and net names under it do not change. The
symbols are laid out in a grid of three columns, 50.8 x 31.75 mm each,
in KiCad's own form (the one its Eagle importer and its editor write).
Run `kicad-cli sch upgrade --force` on the root afterwards, then roundtrip.sh.
"""
import json, re, sys

TEMPLATE = '''\t(sheet
\t\t(at {x} {y})
\t\t(size 50.8 31.75)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(fields_autoplaced yes)
\t\t(stroke
\t\t\t(width 0.1524)
\t\t\t(type solid)
\t\t)
\t\t(fill
\t\t\t(color 0 0 0 0)
\t\t)
\t\t(uuid "{uuid}")
\t\t(property "Sheetname" "{name}"
\t\t\t(at {x} {yn} 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left bottom)
\t\t\t)
\t\t)
\t\t(property "Sheetfile" "{file}"
\t\t\t(at {x} {yf} 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left top)
\t\t\t)
\t\t)
\t\t(instances
\t\t\t(project "{project}"
\t\t\t\t(path "/{root}"
\t\t\t\t\t(page "{page}")
\t\t\t\t)
\t\t\t)
\t\t)
\t)
'''

def fmt(v):
    s = ('%.6f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s

def main():
    a = sys.argv[1:]
    paper = None
    if '--paper' in a:
        i = a.index('--paper')
        paper = a[i + 1]
        del a[i:i + 2]
    root, plan = a
    sheets = json.load(open(plan))
    t = open(root).read()
    root_uuid = re.search(r'^\t\(uuid "([^"]*)"\)', t, re.M).group(1)
    project = re.search(r'\(project "([^"]*)"', t).group(1)
    t, n = re.subn(r'\t\(sheet\n(?:.*\n)*?\t\)\n', '', t)
    if paper:
        t = re.sub(r'\(paper "[^"]*"[^)]*\)', '(paper "%s")' % paper, t, count=1)
    out = []
    for i, s in enumerate(sheets):
        col, row = i % 3, i // 3
        x = 25.4 + 63.5 * col
        y = 25.4 + 44.45 * row
        out.append(TEMPLATE.format(x=fmt(x), y=fmt(y), yn=fmt(y - 0.7116), yf=fmt(y + 31.75 + 0.5346),
                                   uuid=s['uuid'], name=s['name'], file=s['file'], project=project, root=root_uuid, page=i + 2))
    # sheets go before sheet_instances
    m = re.search(r'\t\(sheet_instances\n', t)
    t = t[:m.start()] + ''.join(out) + t[m.start():]
    open(root, 'w').write(t)
    print('%s: %d sheet symbols replaced by %d' % (root, n, len(sheets)))

if __name__ == '__main__':
    main()
