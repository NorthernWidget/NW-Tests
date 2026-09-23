#!/usr/bin/env python3
"""Run every library's desktop harness (extras/test/run.sh) found in the
workspace and report; exit 1 if any fails. The harnesses compile the library's
source with the host compiler against stub Arduino/Wire headers and diff the
output against a recorded baseline, so they need no board and no arduino-cli.

  NW_WORKSPACE  directory holding the library checkouts (default: parent of this repo)
"""
import os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("NW_WORKSPACE", HERE.parent))

def main():
    runs = sorted(p for p in ROOT.glob("*/extras/test/run.sh"))
    results = {}
    for run in runs:
        lib = run.parents[2].name
        env = dict(os.environ, NW_CORE=str(ROOT / "NW_Core"))
        p = subprocess.run(["sh", str(run)], capture_output=True, text=True, env=env)
        ok = p.returncode == 0
        last = (p.stdout.strip().splitlines() or [""])[-1]
        err = next((l for l in (p.stderr + p.stdout).splitlines() if "error" in l.lower() or l.startswith(("+", "-"))), "")
        results[lib] = ok
        print(f"{lib:20s} {'OK  ' if ok else 'FAIL'}  {last if ok else err[:120]}", flush=True)
    failed = [l for l, ok in results.items() if not ok]
    print(f"\n{len(results) - len(failed)} of {len(results)} harnesses pass" + (f"; FAILED: {', '.join(failed)}" if failed else ""))
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
