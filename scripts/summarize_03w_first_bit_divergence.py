#!/usr/bin/env python3
"""Identify the earliest native float-state bit divergence on the same CPU/toolchain."""
import json,re,sys,csv
from pathlib import Path
RE=re.compile(r"TISC_03W_SHADOW elapsedMyr=([^\s]+) mainMyr=([^\s]+) substep=(\d+) nblocks=(\d+) topo_crc=([0-9a-f]+) block_crc=([0-9a-f]+) flex_crc=([0-9a-f]+) hydro_crc=([0-9a-f]+)")
FIELDS=["elapsedMyr","mainMyr","substep","nblocks","topo_crc","block_crc","flex_crc","hydro_crc"]
def rows(p):
    log=p.read_text(errors="replace")
    return [dict(zip(FIELDS,[float(m[1]),float(m[2]),int(m[3]),int(m[4]),*m.groups()[4:]])) for m in RE.finditer(log)]
def main(root,horizon):
    d=Path(root)
    a=rows(d/"reference/RUN.log")
    b=rows(d/"optimized/RUN.log")
    if not a or not b or len(a)!=len(b):raise SystemExit(f"03w missing/unequal substep hash records {len(a)}/{len(b)}")
    for i,(x,y) in enumerate(zip(a,b)):
        if (x["elapsedMyr"],x["mainMyr"],x["substep"],x["nblocks"]) != (y["elapsedMyr"],y["mainMyr"],y["substep"],y["nblocks"]):
            raise SystemExit(f"03w substep timing mismatch at {i}")
    names=("topo_crc","block_crc","flex_crc","hydro_crc")
    firsts={}
    for name in names:
        diff=next((i for i,(x,y) in enumerate(zip(a,b)) if x[name]!=y[name]),None)
        firsts[name]=None if diff is None else {"at_elapsed_Myr":a[diff]["elapsedMyr"],
            "main_step_start_Myr":a[diff]["mainMyr"],"hydro_substep_index":a[diff]["substep"],
            "zero_based_record":diff,
            "baseline_hash":a[diff][name],"candidate_hash":b[diff][name]}
    first_any=next((i for i,(x,y) in enumerate(zip(a,b)) if any(x[name]!=y[name] for name in names)),None)
    report={"experiment":"03w first bitwise 32/64 local-precision induced divergence",
        "horizon_requested_Myr":float(horizon),"n_substeps_compared":len(a),
        "first_any_differing_substep":None if first_any is None else a[first_any],
        "first_by_stored_state":firsts,
        "latest_substep":a[-1],
        "science_note":"Equivalent original input and 03w instrumentation on both source variants. Local state FNV hashes, not direct author ground truth. Printed 0.1m first differences typically later.",
        "complete":abs(a[-1]["elapsedMyr"]-float(horizon))<1e-5}
    (d/"03W_FIRST_BIT_DIFFERENCE.json").write_text(json.dumps(report,indent=2))
    with (d/"03W_CHECKPOINT_HASHES.csv").open("w",newline="") as f:
        col=["variant"]+FIELDS
        w=csv.DictWriter(f,fieldnames=col);w.writeheader()
        for t,rr in (("baseline",a),("local_double",b)):
            for p in rr:w.writerow(dict(variant=t,**p))
    print("03W_QC "+json.dumps({k:v for k,v in report.items() if k!="science_note"}))
    if not report["complete"]:raise SystemExit("03w ended before requested simulated time")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("summarize_03w_first_bit_divergence.py PAIRED_ROOT HORIZON_MYR")
    main(sys.argv[1],sys.argv[2])
