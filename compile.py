#!/usr/bin/env python3
"""Compile every sketch under sketches/ for the NorthernWidget ATmega1284P board
(Margay and Okapi both use it), against the libraries checked out beside this
repository, with the user sketchbook pointed at an empty directory so stale
copies cannot mask a break. Writes results.md and results.json; exits 1 if any
sketch fails.

  NW_WORKSPACE  directory holding the library checkouts (default: parent of this repo)
  ARDUINO_CLI   arduino-cli binary (default: on PATH, else the Arduino IDE 2 bundled one)
  EXTRA_LIBS    colon-separated extra library directories (default: ~/Arduino/libraries/Adafruit_*)
  FQBN          board (default NorthernWidget:avr:NW1284p)

Usage: ./compile.py [--only NAME ...]
"""
import glob, json, os, re, shutil, subprocess, sys, tempfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("NW_WORKSPACE", HERE.parent))
CLI = os.environ.get("ARDUINO_CLI") or shutil.which("arduino-cli") or \
      "/usr/local/bin/arduino-ide_2.3.3_Linux_64bit/resources/app/lib/backend/resources/arduino-cli"
FQBN = os.environ.get("FQBN", "NorthernWidget:avr:NW1284p")

# Every library a sketch here may pull in, by workspace directory name.
LIBRARIES = ["NW_Core", "Apis_Library", "Walrus_Library", "Haar_Library", "Libelle_Library", "Liasis_Library",
             "T9602_Library", "MaxBotix_Library", "NW_BME280", "Tally_Library",
             "Margay_Library", "Okapi_Library", "DS3231_Logger", "MCP3421", "SdFat", "MCP23018", "MCP4725", "TCA9534"]
extra = os.environ.get("EXTRA_LIBS")
EXTRA = extra.split(":") if extra else sorted(glob.glob(os.path.expanduser("~/Arduino/libraries/Adafruit_*")))

def compile_one(sketch: Path, empty_sketchbook: str):
    args = [CLI, "compile", "--fqbn", FQBN]
    for lib in LIBRARIES:
        d = ROOT / lib
        if d.is_dir(): args += ["--library", str(d)]
    for d in EXTRA:
        if Path(d).is_dir(): args += ["--library", d]
    args.append(str(sketch))
    env = dict(os.environ, ARDUINO_DIRECTORIES_USER=empty_sketchbook)
    p = subprocess.run(args, capture_output=True, text=True, env=env)
    out = p.stdout + p.stderr
    flash = re.search(r"Sketch uses (\d+) bytes", out)
    ram = re.search(r"Global variables use (\d+) bytes", out)
    err = next((l.strip() for l in out.splitlines() if "error:" in l or "fatal error" in l), "")
    if not err and p.returncode != 0:   # e.g. a link failure: take the linker's line
        err = next((l.strip() for l in out.splitlines() if "multiple definition" in l or "undefined reference" in l), "compile failed")
    err = err.replace(str(ROOT) + "/", "")
    return dict(ok=(p.returncode == 0), flash=int(flash.group(1)) if flash else None,
                ram=int(ram.group(1)) if ram else None, error=err[:160])

def main():
    only = sys.argv[2:] if len(sys.argv) > 2 and sys.argv[1] == "--only" else []
    sketches = sorted(p for p in (HERE / "sketches").iterdir() if p.is_dir())
    if only: sketches = [s for s in sketches if s.name in only or s.name.split("_")[0] in only]
    results = {}
    with tempfile.TemporaryDirectory() as empty:
        for s in sketches:
            r = compile_one(s, empty)
            results[s.name] = r
            print(f"{s.name:20s} {'OK  ' if r['ok'] else 'FAIL'} {r['flash'] or '':>6} {r['ram'] or '':>5}  {r['error']}", flush=True)
    # results.md: one row per sensor, one column pair per logger
    sensors = sorted({n.rsplit("_", 1)[0] for n in results})
    loggers = sorted({n.rsplit("_", 1)[1] for n in results})
    lines = [f"# Compile results — {date.today().isoformat()}", "",
             f"Board `{FQBN}`; libraries from `{ROOT}`; sketchbook empty. Cells: flash B / RAM B, or the first error.", "",
             "| Sensor | " + " | ".join(loggers) + " |", "|---|" + "---|" * len(loggers)]
    for sn in sensors:
        cells = []
        for lg in loggers:
            r = results.get(f"{sn}_{lg}")
            cells.append("—" if r is None else (f"✅ {r['flash']} / {r['ram']}" if r["ok"] else f"❌ {r['error'] or 'compile failed'}"))
        lines.append(f"| {sn} | " + " | ".join(cells) + " |")
    (HERE / "results.md").write_text("\n".join(lines) + "\n")
    (HERE / "results.json").write_text(json.dumps(dict(date=date.today().isoformat(), fqbn=FQBN, results=results), indent=1) + "\n")
    # Libraries with uncommitted changes: the runner compiles working trees, so say so.
    dirty = [lib for lib in LIBRARIES if (ROOT / lib).is_dir() and
             subprocess.run(["git", "-C", str(ROOT / lib), "status", "--porcelain", "--untracked-files=no"],
                            capture_output=True, text=True).stdout.strip()]
    if dirty:
        lines += ["", "Working trees with uncommitted changes (compiled as they are): " + ", ".join(dirty)]
        (HERE / "results.md").write_text("\n".join(lines) + "\n")
        print("\nworking trees with uncommitted changes:", ", ".join(dirty))
    failed = [n for n, r in results.items() if not r["ok"]]
    print(f"\n{len(results) - len(failed)} of {len(results)} sketches compile" + (f"; FAILED: {', '.join(failed)}" if failed else ""))
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
