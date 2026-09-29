#!/usr/bin/env python3
"""The standard names, and the generated header that must match them.

Two checks, both cheap, both of which have been shown to bite:

  1. NW-Device-Specification/check_standard_names.py: the vocabulary itself -
     the CSDMS grammar, registry claims, units, statuses, row shape, and every
     name a row's `aggregations` column implies.
  2. generate_names.py --check: NW_Core/src/NW_StandardNames.h against the CSV
     that produced it. Hand-editing the header, or changing a name and not
     regenerating, is caught here rather than discovered in a data file.

A name typed in two places is a name that will differ in two places, and the
copy in the firmware is the one nobody notices is wrong. This check is what
makes that sentence true rather than hopeful.

  python3 names_check.py

Exit 1 on any failure. NW_WORKSPACE names the directory holding the checkouts
(default: the parent of this repository).
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("NW_WORKSPACE", HERE.parent))
SPEC = ROOT / "NW-Device-Specification"
HEADER = ROOT / "NW_Core" / "src" / "NW_StandardNames.h"


def run(label, args, cwd):
    r = subprocess.run([sys.executable] + args, cwd=cwd, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    print(f"{label:<22} {'ok  ' if r.returncode == 0 else 'FAIL'} {out.splitlines()[-1] if out else ''}")
    if r.returncode != 0 and out:
        print("\n".join("    " + l for l in out.splitlines()))
    return r.returncode


def main():
    if not SPEC.is_dir():
        print(f"{SPEC} not found; set NW_WORKSPACE", file=sys.stderr)
        return 1
    bad = run("standard-names.csv", ["check_standard_names.py"], SPEC)
    bad += run("NW_StandardNames.h", ["generate_names.py", "--check", str(HEADER)], SPEC)
    print("\nnames: " + ("OK" if bad == 0 else f"{bad} check(s) failed"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
