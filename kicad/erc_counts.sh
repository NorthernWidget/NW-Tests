#!/bin/sh
# erc_counts.sh <root.kicad_sch> <out.json>
# Fresh ERC with every severity, then the two endpoint counts and the total.
# The JSON files every violation under the first sheet and gives a dangling
# wire's connected end, so attribute and diagnose with sch_walk.py, not from it.
set -e
kicad-cli sch erc --format json --severity-all -o "$2" "$1" >/dev/null 2>&1 || true
python3 - "$2" <<'PY'
import json,sys,collections
e=json.load(open(sys.argv[1])); c=collections.Counter()
for sh in e['sheets']:
    for v in sh['violations']: c[v['type']]+=1
print('unconnected_wire_endpoint',c['unconnected_wire_endpoint'],' endpoint_off_grid',c['endpoint_off_grid'],' total',sum(c.values()))
PY
