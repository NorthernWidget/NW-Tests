# NW-Tests

The core Northern Widget test repository: it compiles every library against Margay and Okapi, runs each library's host harness, checks version consistency, and checks code style. It is what CI runs, and what a commit elsewhere in the workspace is gated on.

## Standards

Follow the NW standards in the root `CLAUDE.md` one level above `github/`. This repository is Python and shell; the Arduino library checklist does not apply to it, but it enforces that checklist on everything else.

## Running it

```sh
python3 compile.py            # every sketch; expect 16 of 18 (MaxBotix is the known failure)
python3 harness.py            # every library's host harness; expect 7 of 7
python3 version_check.py      # library.properties vs source vs CITATION.cff vs tag
python3 style_check.py <repo> # gate every commit touching .ino/.cpp/.h on this
```

`compile.py` reads sibling checkouts from `NW_WORKSPACE`, defaulting to the parent directory, and builds with an **empty** sketchbook so that stale copies in `~/Arduino/libraries` cannot satisfy an include.

## Working rules

- The expected counts above are the acceptance criterion. A number that moves is either a regression or a fact to record here, never something to shrug at.
- `make_sketches.py` generates the sketches from a table; edit the table, not the generated sketches.
- A new library joins by being added to the lists here and to the CI clone list, in the same commit that makes it exist.
- `style_check.py` is the authority on house style: added lines match the file's own indent unit, `if(` or `if (` as the file does, `//Comment` or `// Comment` as the file does, and new files take the Arduino IDE form.

## Hard rule

**Never** create a git tag, GitHub release, or push to a shared remote unless explicitly asked in the current message. If in doubt, ask.
