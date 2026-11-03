#!/usr/bin/env python3
"""Page settings of a KiCad schematic sheet, edited as text.

    sheet_page.py <sheet.kicad_sch> [--paper NAME] [--date D] [--rev R]
                  [--title T] [--company C] [--delete-lib-id NICK:NAME]

--paper writes (paper "NAME") in place of whatever the sheet has (a User
size from the Eagle import, usually). --date/--rev/--title/--company write
the sheet's (title_block ...) after (paper ...), in KiCad's own order
(title, date, rev, company), keeping fields already there that are not
given. --delete-lib-id removes every placed instance of that symbol and
its lib_symbols entry, which is how the Eagle frame symbols leave a sheet
once the project has a drawing sheet. Run roundtrip.sh afterwards.
"""
import argparse, re, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sheet')
    ap.add_argument('--paper')
    for k in ('title', 'date', 'rev', 'company'):
        ap.add_argument('--' + k)
    ap.add_argument('--delete-lib-id', action='append', default=[])
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
    open(a.sheet, 'w').write(t)

if __name__ == '__main__':
    main()
