#!/usr/bin/env python3
"""Refresh a sheet's embedded copy of library symbols after the library changed.

    refresh_symbols.py <sheet.kicad_sch> <lib.kicad_sym> <nick> NAME [NAME ...]

For each NAME, the sheet's lib_symbols entry "<nick>:NAME" is replaced by the
library's current definition (the top symbol takes the library-qualified
name; its units keep their bare names, as KiCad writes them). Placed
instances are untouched: this is right only when the pins did not change,
which swap_symbols.py's measure (symbol_map.py) establishes; for artwork
symbols with no pins it is always right. Run roundtrip.sh afterwards.
"""
import re, sys

def main():
    sheet, lib, nick = sys.argv[1:4]
    names = sys.argv[4:]
    L = open(lib).read()
    S = open(sheet).read()
    for name in names:
        m = re.search(r'^\t\(symbol "' + re.escape(name) + r'"\n.*?^\t\)\n', L, re.S | re.M)
        assert m, 'no symbol %s in %s' % (name, lib)
        copy = re.sub(r'^\t\(symbol "' + re.escape(name) + '"', '\t(symbol "%s:%s"' % (nick, name), m.group(0), count=1)
        copy = '\n'.join('\t' + l if l else l for l in copy.rstrip('\n').split('\n')) + '\n'
        pat = r'^\t\t\(symbol "' + re.escape(nick + ':' + name) + r'"\n.*?^\t\t\)\n'
        S, n = re.subn(pat, lambda _: copy, S, count=1, flags=re.S | re.M)
        assert n == 1, 'sheet has no copy of %s:%s' % (nick, name)
        print('%s: %s refreshed' % (sheet, name))
    open(sheet, 'w').write(S)

if __name__ == '__main__':
    main()
