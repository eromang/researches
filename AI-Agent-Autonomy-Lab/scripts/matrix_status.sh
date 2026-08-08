#!/usr/bin/env bash
# matrix_status.sh — live F16 matrix dashboard. Watch it refresh with:
#     watch -n 20 bash scripts/matrix_status.sh
# (or just re-run it). Reads runs/ + runs/swarm_matrix.log; no side effects.
cd "$(dirname "$0")/.."
echo "════════════ F16 MATRIX — $(date +%H:%M:%S) ════════════"
now=$(grep -E '×' runs/swarm_matrix.log 2>/dev/null | tail -1 | sed 's/=== //;s/ ===//')
turn=$(grep -E 'turn [0-9]+/' runs/swarm_matrix.log 2>/dev/null | tail -1 | sed 's/=== //;s/ ===//')
grep -q ALL_SWARM_all_DONE runs/swarm_matrix.log 2>/dev/null && echo "STATUS: COMPLETE" || echo "NOW: ${now:-starting…}   |   ${turn}"
echo
python3 - <<'PY'
import os, re, glob, sys
sys.path.insert(0, "scripts")
from score_swarm import score_chain
R="runs"
plan=[("S0",5,1),("S0b",3,1),("A",3,5),("B1",5,2),("B2",3,3),("C",5,5) if False else ("C",3,5)]
tot_done=tot_all=0
for cond,nchains,nlinks in plan:
    total=nchains*nlinks
    done=len(glob.glob(f"{R}/*-f16-{cond}-c*-s*"))
    tot_done+=done; tot_all+=total
    keys=sorted({re.search(rf"(f16-{cond}-c\d+)-s\d+$",d).group(1)
                 for d in os.listdir(R) if re.search(rf"f16-{cond}-c\d+-s\d+$",d)})
    bar_n=int(20*done/total) if total else 0
    bar="█"*bar_n+"·"*(20-bar_n)
    upass=0; turns=[]
    for k in keys:
        r=score_chain(k)
        if r.get("error"): continue
        if r["union_pass"]: upass+=1
        turns+=[t for _,t in r["exploiter_turns"]]
    extra=f"union {upass}/{len(keys)}" if keys else ""
    if turns: extra+=f"  expl_turns~{sorted(turns)}"
    print(f"  {cond:<4} [{bar}] {done:>2}/{total:<3} runs · {len(keys)}/{nchains} chains   {extra}")
print(f"\n  TOTAL {tot_done}/{tot_all} agent-runs")
PY
