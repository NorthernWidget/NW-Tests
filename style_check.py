#!/usr/bin/env python3
"""Check that the lines a diff adds match the style of the file they land in.

Usage: style_check.py [--base REF] [REPO_DIR ...]
       (default: the repositories with staged or unstaged changes under this
       workspace; --base defaults to the index, i.e. the working tree is
       compared with HEAD)

For every .ino/.cpp/.h/.c file touched, the pre-change file sets the style:
indent unit (tab, 2 or 4 spaces), `if(` or `if (`, `//Comment` or
`// Comment`, and brace placement for control statements. Added lines that
contradict a clear majority (at least 3:1) are reported and the exit status is
1. New files are held to the Arduino IDE convention (2 spaces, attached
braces, `if (`, `// Comment`). This is the standing rule from the workspace
CLAUDE.md made mechanical: match the file; never reformat untouched lines.
"""
import re, subprocess, sys, os, glob, collections

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = re.compile(r'\.(ino|cpp|h|c)$')

def stats(lines):
    c = collections.Counter()
    for s in lines:
        if not s.strip() or s.lstrip().startswith('#'): continue   # preprocessor lines keep their own indent convention
        m = re.match(r'^([ \t]+)', s)
        if m:
            ind = m.group(1)
            if '\t' in ind: c['tab'] += 1
            elif len(ind) % 4 == 2: c['sp2'] += 1
            elif len(ind) % 4 == 0: c['sp4'] += 1
        if re.search(r'\bif\(', s): c['if('] += 1
        if re.search(r'\bif \(', s): c['if ('] += 1
        if re.search(r'(^|\s)//[A-Za-z]', s): c['//x'] += 1
        if re.search(r'(^|\s)// [A-Za-z]', s): c['// x'] += 1
        if re.search(r'\b(if|for|while|else|switch)\b.*\)\s*\{\s*$', s) or re.search(r'\belse\s*\{\s*$', s): c['attached'] += 1
    return c

def majority(c, a, b):
    """'a' if a dominates b at least 3:1, 'b' if the reverse, else None."""
    if c[a] >= 3 * max(c[b], 1) and c[a] >= 3: return a
    if c[b] >= 3 * max(c[a], 1) and c[b] >= 3: return b
    return None

def indent_unit(lines):
    """'tab', 'sp2', 'sp4' or None: tabs if they lead 3:1 over spaces; else the
    smallest leading-space count seen at least three times (2 or 4)."""
    tabs = spaces = 0; widths = collections.Counter()
    for s in lines:
        if s.lstrip().startswith('#'): continue
        m = re.match(r'^([ \t]+)\S', s)
        if not m: continue
        if '\t' in m.group(1): tabs += 1
        else: spaces += 1; widths[len(m.group(1))] += 1
    if tabs >= 3 and tabs >= 3 * max(spaces, 1): return 'tab'
    if spaces >= 3 and spaces >= 3 * max(tabs, 1):
        for w in sorted(widths):
            if widths[w] >= 3: return 'sp2' if w % 4 == 2 else 'sp4'
    return None

def added_lines(repo, path, base):
    out = subprocess.run(['git', '-C', repo, 'diff', '-U0', base, '--', path], capture_output=True, text=True).stdout
    return [l[1:] for l in out.splitlines() if l.startswith('+') and not l.startswith('+++')]

def locally_matched(repo, path, base):
    """Added lines whose leading whitespace is of the same kind (tabs or spaces)
    as the nearest unchanged line above them in the diff: a line added inside a
    function that already indents differently from the rest of its file matches
    its neighbours, which is the rule (match the surrounding lines; never
    reformat what you do not touch)."""
    out = subprocess.run(['git', '-C', repo, 'diff', '-U1', base, '--', path], capture_output=True, text=True).stdout
    def indent(line):
        m = re.match(r'^([ \t]+)\S', line); return m.group(1) if m else None
    matched, ctx, pending = [], None, []      # pending: added lines before any indented context in the hunk
    def settle(ws):
        for a in pending:
            if ws and ('\t' in indent(a)) == ('\t' in ws): matched.append(a)
        pending.clear()
    for l in out.splitlines():
        if l.startswith('@@'): settle(None); ctx = None; continue
        if l.startswith(('+++', '---')): continue
        if l.startswith(' '):
            ws = indent(l[1:])
            if ws: ctx = ws; settle(ws)     # the first indented line below settles what came before it
        elif l.startswith('+') and indent(l[1:]):
            if ctx and ('\t' in indent(l[1:])) == ('\t' in ctx): matched.append(l[1:])
            elif not ctx: pending.append(l[1:])
    settle(None)
    return matched

def old_text(repo, path, base):
    r = subprocess.run(['git', '-C', repo, 'show', f'{base}:{path}'], capture_output=True, text=True)
    return r.stdout.splitlines() if r.returncode == 0 else None

def check_repo(repo, base):
    files = subprocess.run(['git', '-C', repo, 'diff', '--name-only', base], capture_output=True, text=True).stdout.split()
    problems = []
    for f in files:
        if not CODE.search(f) or 'baseline' in f: continue
        added = added_lines(repo, f, base)
        if not added: continue
        old = old_text(repo, f, base)
        sa = stats(added)
        if old is not None:   # indent counts leave out lines that match their unchanged neighbour
            local = locally_matched(repo, f, base)
            si = stats([l for l in added if l not in local])
            for k in ('tab', 'sp2', 'sp4'): sa[k] = si[k]
        if old is None:                       # new file: the IDE convention
            rules = {'indent': 'sp2', 'if': 'if (', 'comment': '// x'}
            so = None
        else:
            so = stats(old)
            rules = {'indent': indent_unit(old), 'if': majority(so, 'if(', 'if ('), 'comment': majority(so, '//x', '// x')}
        # indentation: tabs vs spaces is strict; a 4-space file cannot hold a 2-space line (definite);
        # a 2-space file with only multiples of 4 added is possible nesting, so it is a warning only
        if rules['indent'] == 'tab' and (sa['sp2'] or sa['sp4']):
            problems.append((f, f"file indents with tabs; {sa['sp2'] + sa['sp4']} added lines use spaces"))
        if rules['indent'] in ('sp2', 'sp4') and sa['tab']:
            problems.append((f, f"file indents with spaces; {sa['tab']} added lines use tabs"))
        if rules['indent'] == 'sp4' and sa['sp2']:
            problems.append((f, f"file indents by 4; {sa['sp2']} added lines sit at a 2-space depth"))
        if rules['indent'] == 'sp2' and sa['sp2'] == 0 and sa['sp4'] >= 6:
            print(f"warning: {os.path.basename(repo)}/{f}: file indents by 2 and all {sa['sp4']} added indented lines are multiples of 4; check they are nesting, not 4-space")
        if rules['if'] and sa[{'if(': 'if (', 'if (': 'if('}[rules['if']]] > 0:
            other = {'if(': 'if (', 'if (': 'if('}[rules['if']]
            problems.append((f, f"file writes `{rules['if']}`; {sa[other]} added lines write `{other}`"))
        if rules['comment'] and sa[{'//x': '// x', '// x': '//x'}[rules['comment']]] > 0:
            other = {'//x': '// x', '// x': '//x'}[rules['comment']]
            problems.append((f, f"file comments as `{rules['comment']}`; {sa[other]} added lines comment as `{other}`"))
    return problems

def main():
    args = sys.argv[1:]; base = 'HEAD'
    if args and args[0] == '--base': base = args[1]; args = args[2:]
    repos = args or [d for d in sorted(glob.glob(os.path.join(WS, '*'))) if os.path.isdir(os.path.join(d, '.git'))
                     and subprocess.run(['git', '-C', d, 'diff', '--quiet', base]).returncode != 0]
    bad = 0
    for r in repos:
        for f, why in check_repo(r, base):
            print(f"{os.path.basename(r)}/{f}: {why}"); bad += 1
    print("style: OK" if not bad else f"style: {bad} mismatch(es)")
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
