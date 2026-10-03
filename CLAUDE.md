# NW-Tests

The core Northern Widget test repository: it compiles every library against Margay and Okapi, runs each library's host harness, checks version consistency, and checks code style. It is what CI runs, and what a commit elsewhere in the workspace is gated on.

## Standards

Follow the NW standards in the root `CLAUDE.md` one level above `github/`. This repository is Python and shell; the Arduino library checklist does not apply to it, but it enforces that checklist on everything else.

## Running it

```sh
python3 compile.py            # every sketch; expect 16 of 18 (MaxBotix is the known failure)
python3 harness.py            # every library's host harness; expect 8 of 8
python3 version_check.py      # library.properties vs source vs CITATION.cff vs tag
python3 style_check.py <repo> # gate every commit touching .ino/.cpp/.h on this
```

`compile.py` reads sibling checkouts from `NW_WORKSPACE`, defaulting to the parent directory, and builds with an **empty** sketchbook so that stale copies in `~/Arduino/libraries` cannot satisfy an include.

## Working rules

- The expected counts above are the acceptance criterion. A number that moves is either a regression or a fact to record here, never something to shrug at.
- `make_sketches.py` generates the sketches from a table; edit the table, not the generated sketches. A hand-edit of a generated sketch survives until the next run and then vanishes, which is how `setADCColumns(true)` nearly left the Walrus sketch on 2026-10-01: configuration a sketch must make after `begin()` goes in `AFTER_BEGIN`, keyed by library.
- **Both ways of reaching a sensor are tested, and against each other.** A sketch either programs its sensors with `Logger.watch()` or lets `Logger.discover()` take them from the bus, and the suite carries one of each (Andy, 2026-10-03). The acceptance test is that on the same bus the two write the same table, **byte for byte**. That needs one constraint, and it belongs on the test rather than the library: a test sketch watches its sensors in **address** order, which is the order discovery finds them in, so a plain `diff` is the comparison and there is nothing to normalise. A user stays free to watch in any order, since column order is unimportant. This catches a `discover()` that walks the bus backwards, which a sorted set comparison would normalise away, and it only bites with two or more devices, because one cannot be out of order. Edit a test sketch out of address order and the comparison fails loudly rather than passing quietly. NW-Sim holds the cases: `walrus_margay` programmed, `margay_scan` reporting, and a discovered case diffed against the programmed one. A new sensor library joins both paths, not one.
- A new library joins by being added to the lists here and to the CI clone list, in the same commit that makes it exist.
- `style_check.py` is the authority on house style: added lines match the file's own indent unit, `if(` or `if (` as the file does, `//Comment` or `// Comment` as the file does, and new files take the Arduino IDE form.

## Hard rule

**Never** create a git tag, GitHub release, or push to a shared remote unless explicitly asked in the current message. If in doubt, ask.
