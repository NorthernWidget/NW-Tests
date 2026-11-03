#!/usr/bin/env python3
"""Page settings of a KiCad schematic sheet, edited as text.

    sheet_page.py <sheet.kicad_sch> [--paper NAME] [--date D] [--rev R]
                  [--title T] [--company C] [--delete-lib-id NICK:NAME]
                  [--translate DX DY]

--paper writes (paper "NAME") in place of whatever the sheet has (a User
size from the Eagle import, usually). --date/--rev/--title/--company write
the sheet's (title_block ...) after (paper ...), in KiCad's own order
(title, date, rev, company), keeping fields already there that are not
given. --delete-lib-id removes every placed instance of that symbol and
its lib_symbols entry, which is how the Eagle frame symbols leave a sheet
once the project has a drawing sheet. --translate moves everything on the
sheet by (DX, DY) mm: every absolute coordinate outside lib_symbols
(symbols and their fields, wires, junctions, labels, texts, graphics).
Give whole grid ticks (multiples of 1.27) or every endpoint goes off
grid. Run roundtrip.sh afterwards.
"""
import argparse, re, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sheet')
    ap.add_argument('--paper')
    for k in ('title', 'date', 'rev', 'company'):
        ap.add_argument('--' + k)
    ap.add_argument('--delete-lib-id', action='append', default=[])
    ap.add_argument('--translate', nargs=2, type=float, metavar=('DX', 'DY'))
    a = ap.parse_args()
    t = open(a.sheet).read()
    if a.paper:
        t, n = re.subn(r'\(paper "[^"]*"[^)]*\)', '(paper "%s")' % a.paper, t, count=1)
        assert n == 1, 'no (paper ...) found'
    fields = {k: getattr(a, k) for k in ('title', 'date', 'rev', 'company') if getattr(a, k) is not None}
    if fields:
        m = re.search(r'\t\(title_block\n((?:\t\t.*\n)*?)\t\)\n', t)
        have = {}
        if m:
            for k, v in re.findall(r'\t\t\((title|date|rev|company) "([^"]*)"\)\n', m.group(1)):
                have[k] = v
            t = t[:m.start()] + t[m.end():]
        have.update(fields)
        block = '\t(title_block\n' + ''.join('\t\t(%s "%s")\n' % (k, have[k]) for k in ('title', 'date', 'rev', 'company') if have.get(k)) + '\t)\n'
        m = re.search(r'\t\(paper "[^"]*"[^)]*\)\n', t)
        assert m, 'no (paper ...) found'
        t = t[:m.end()] + block + t[m.end():]
    for lib_id in a.delete_lib_id:
        pat = r'\t\(symbol\n\t\t\(lib_id "%s"\)\n(?:.*\n)*?\t\)\n' % re.escape(lib_id)
        t, n = re.subn(pat, '', t)
        name = lib_id.split(':', 1)[1]
        pat = r'\t\t\(symbol "%s"\n(?:.*\n)*?\t\t\)\n' % re.escape(lib_id)
        t, k = re.subn(pat, '', t)
        print('%s: %d instances of %s removed, %d lib_symbols entry' % (a.sheet, n, lib_id, k))
    if a.translate:
        dx, dy = a.translate
        i = t.find('(lib_symbols')
        depth = 0
        j = i
        while True:
            if t[j] == '(':
                depth += 1
            elif t[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        head, lib, tail = t[:i], t[i:j + 1], t[j + 1:]
        def fmt(v):
            s = ('%.6f' % v).rstrip('0').rstrip('.')
            return '0' if s in ('-0', '') else s
        def shift(m):
            return '(%s %s %s' % (m.group(1), fmt(float(m.group(2)) + dx), fmt(float(m.group(3)) + dy))
        pat = r'\((at|xy|start|end|center|mid) (-?[\d.]+) (-?[\d.]+)'
        head, n1 = re.subn(pat, shift, head)
        tail, n2 = re.subn(pat, shift, tail)
        print('%s: %d coordinates moved by (%s, %s)' % (a.sheet, n1 + n2, fmt(dx), fmt(dy)))
        t = head + lib + tail
    open(a.sheet, 'w').write(t)

if __name__ == '__main__':
    main()
