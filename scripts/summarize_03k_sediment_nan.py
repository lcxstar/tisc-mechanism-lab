#!/usr/bin/env python3
"""Summarize and timestamp 03k first sediment NaN with no speculative root cause."""
import csv,json,re,sys
from pathlib import Path

EVENT=re.compile(r"TISC_SED_DIAG stage=(\S+) iter=(-?\d+) row=(-?\d+) col=(-?\d+) mass=(\S+) masstr=(\S+) out_mass=(\S+) sed_mass=(\S+) bed_mass=(\S+)")
STAGE=re.compile(r"TISC_SED_DIAG phase=(\S+) iter=(\d+) lost_sed=(\S+) total_sed=(\S+) total_bed=(\S+)")
def main(folder):
    p=Path(folder)
    raw=(p/"RUN.log").read_text(errors="replace")
    events=[{"stage":m[1],"substep":int(m[2]),"row":int(m[3]),"col":int(m[4]),
             "mass":m[5],"masstr":m[6],"total_out":m[7],"total_sed":m[8],
             "total_bed":m[9]} for m in EVENT.finditer(raw)]
    phases=[{"phase":m[1],"substep":int(m[2]),"total_out":m[3],
             "total_sed":m[4],"total_bed":m[5]} for m in STAGE.finditer(raw)]
    with (p/"03K_NONFINITE_FIRST_EVENTS.csv").open("w",newline="") as f:
        cols=["stage","substep","row","col","mass","masstr","total_out","total_sed","total_bed"]
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(events)
    with (p/"03K_SEDIMENT_SUBSTEPS.csv").open("w",newline="") as f:
        cols=["phase","substep","total_out","total_sed","total_bed"]
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(phases)
    rc=int((p/"EXIT_CODE.txt").read_text())
    anynan=re.findall(r"\boutp_seds:\s*([+-]?(?:nan|inf))\b",raw,re.I)
    report={
        "job":str(p),"exit_code":rc,"profile_trace_events":len(events),
        "profile_substep_snapshots":len(phases),"first_nonfinite_event":events[0] if events else None,
        "first_nonfinite_substep_from_internal_timing":events[0]["substep"] if events else None,
        "first_substep_with_nonfinite_cumulative_outlet":next(
            (x for x in phases if x["phase"]=="after_fluvial" and
             (re.search(r"\b(?:nan|inf)\b",x["total_out"],re.I))),None),
        "final_outp_seds_nan":bool(anynan),"first_events":events[:15],
        "tail_phases":phases[-12:],
        "tracer_bound":"first 32 nonfinite event stderr printouts to control artifact size",
        "sediment_physics_edited":False,
    }
    (p/"03K_NAN_QC.json").write_text(json.dumps(report,indent=2))
    print("03K NAN QA",json.dumps({k:v for k,v in report.items()
         if k not in ("first_events","tail_phases")},ensure_ascii=False))
    if not phases:raise SystemExit("Expected sediment substep diagnostic lines but got none")
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("summarize_03k_sediment_nan.py DIR")
    main(sys.argv[1])
