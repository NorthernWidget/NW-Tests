#!/usr/bin/env python3
"""One version per library, everywhere it is written.

For every maintained library beside this repository, read the version from
library.properties and compare it with every other place the library states
it: a version constant in its source (Margay's LibVersion, written to every
status file), CITATION.cff, .zenodo.json, and the latest release tag.

  FAIL  two in-repo sources disagree, or library.properties is behind the
        latest tag (a released version number was reused or rolled back)
  ok    every in-repo source agrees; the tag column says whether that
        version is released (= tag), unreleased (> tag), or untagged

Exit 1 on any FAIL. NW_WORKSPACE names the directory holding the checkouts
(default: the parent of this repository). Andy, 2026-09-23: the library
version in the status file must be the library's version, and the check
belongs here, beside the style and compile checks.
"""
import json, os, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("NW_WORKSPACE", HERE.parent))

# The maintained libraries, by workspace directory name (stale copies beside
# them are not scanned).
LIBRARIES = ["NW_Core", "NW_Logger", "Apis_Library", "Walrus_Library", "Haar_Library", "Libelle_Library", "Liasis_Library",
             "T9602_Library", "MaxBotix_Library", "NW_BME280", "Tally_Library",
             "Margay_Library", "Okapi_Library", "DS3231_Logger", "MCP3421", "MCP23018"]

SEMVER = r"(\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?)"
SOURCE_CONSTANT = re.compile(r'(?:LibVersion|LIB_VERSION|[A-Z_]*_VERSION(?:_STR)?)\s*=\s*"' + SEMVER + '"')
SOURCE_DEFINE = re.compile(r'#define\s+[A-Z_]*VERSION[A-Z_]*\s+"' + SEMVER + '"')

def key(v):
    """Sort key for a semantic version; a prerelease sorts before its release."""
    core, _, pre = v.partition("-")
    return tuple(int(x) for x in core.split(".")) + ((0,) if pre else (1,))

def read(path, pattern):
    if not path.exists(): return None
    m = re.search(pattern, path.read_text(errors="replace"), re.M)
    return m.group(1) if m else None

def sources(lib):
    """Every place the library states its version: {label: version or None}."""
    found = {"library.properties": read(lib / "library.properties", r"^version=" + SEMVER)}
    for f in sorted((lib / "src").rglob("*")) if (lib / "src").is_dir() else []:
        if f.suffix not in (".h", ".cpp", ".c", ".hpp"): continue
        text = f.read_text(errors="replace")
        for m in list(SOURCE_CONSTANT.finditer(text)) + list(SOURCE_DEFINE.finditer(text)):
            found[f"src/{f.name}"] = m.group(1)
    found["CITATION.cff"] = read(lib / "CITATION.cff", r"^version:\s*['\"]?" + SEMVER)
    zen = lib / ".zenodo.json"
    if zen.exists():
        try: found[".zenodo.json"] = json.loads(zen.read_text()).get("version")
        except json.JSONDecodeError: found[".zenodo.json"] = "unparseable"
    return found

def latest_tag(lib):
    p = subprocess.run(["git", "-C", str(lib), "tag", "--list", "v*", "--sort=-v:refname"], capture_output=True, text=True)
    tags = [t.strip() for t in p.stdout.splitlines() if t.strip()]
    return tags[0][1:] if tags else None

def check(name):
    lib = ROOT / name
    if not (lib / "library.properties").exists():
        return name, "skip", "no library.properties", {}
    found = sources(lib)
    stated = {k: v for k, v in found.items() if v is not None}
    versions = set(stated.values())
    props = found["library.properties"]
    tag = latest_tag(lib)
    problems = []
    if len(versions) > 1:
        problems.append("disagree: " + ", ".join(f"{k}={v}" for k, v in stated.items()))
    if props and tag and key(props) < key(tag):
        problems.append(f"library.properties {props} is behind the latest tag v{tag}")
    if problems:
        return name, "FAIL", "; ".join(problems), stated
    if tag is None: rel = "untagged"
    elif key(props) == key(tag): rel = f"released (v{tag})"
    else: rel = f"unreleased ({props} > v{tag})"
    return name, "ok", f"{props} in {len(stated)} place{'s' if len(stated) != 1 else ''}; {rel}", stated

def main():
    only = sys.argv[1:] or LIBRARIES
    failed = []
    for name in only:
        n, state, why, _ = check(name)
        print(f"{n:18s} {state:5s} {why}", flush=True)
        if state == "FAIL": failed.append(n)
    print(f"\n{len(only) - len(failed)} of {len(only)} libraries consistent" + (f"; FAILED: {', '.join(failed)}" if failed else ""))
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
