#!/usr/bin/env python3
"""03i QC: organize per-substep discharge bottlenecks, preserving 124 timeouts."""
import csv
import json
import re
import sys
from pathlib import Path

LINE=re.compile(r"(?m)^TISC_DISCHARGE event=(\S+) stage=(\S+) substep=(\d+) nodes=(\d+) grid=(\d+) (.+)$")
FLOATS=("elapsed_s","precheck_s","lake_input_s","outlet_rain_s","outlet_evap_s",
        "permeability_s","attempt_delete_s","salt_deposit_s","lake_volume_s","checks_s")
COUNTS=("lake_input_calls","lake_input_nodes","lake_input_outlets","attempt_calls",
        "lake_nodes","outlet_nodes","max_lake_size","nlakes")
SUBSTAGES=("precheck_s","outlet_rain_s","outlet_evap_s","permeability_s",
           "salt_deposit_s","lake_volume_s","checks_s")

def parse(log):
    snapshots=[]
    for m in LINE.finditer(log):
        p=dict(x.split("=",1) for x in m.group(6).split() if "=" in x)
        if any(k not in p for k in FLOATS+COUNTS):
            raise ValueError("Incomplete TISC_DISCHARGE diagnostic line")
        o={"event":m.group(1),"stage":m.group(2),
           "substep":int(m.group(3)),"nodes":int(m.group(4)),
           "grid":int(m.group(5))}
        o.update({k:float(p[k]) for k in FLOATS})
        o.update({k:int(p[k]) for k in COUNTS})
        snapshots.append(o)
    return snapshots

def main(folder):
    root=Path(folder)
    log=(root/"RUN.log").read_text(errors="replace")
    snapshots=parse(log)
    if not snapshots:
        raise SystemExit("03i FAIL: discharge tracing absent; check compilation and stage reached")
    fields=list(snapshots[0])
    with (root/"03I_DISCHARGE_PROGRESS.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(snapshots)
    intervals=[]
    for a,b in zip(snapshots,snapshots[1:]):
        if b["substep"] != a["substep"] or b["nodes"]<a["nodes"]:continue
        if b["stage"] not in ("node_scan","salt_deposition","lake_volume","checks_and_total"):continue
        row={"substep":b["substep"],"event":b["event"],"stage":b["stage"],
             "start_nodes":a["nodes"],"end_nodes":b["nodes"],
             "delta_elapsed_s":round(b["elapsed_s"]-a["elapsed_s"],6)}
        for k in FLOATS[1:]+COUNTS:
            if k=="nlakes" or k=="max_lake_size":continue
            row["delta_"+k]=round(b[k]-a[k],6)
        intervals.append(row)
    with (root/"03I_DISCHARGE_INTERVALS.csv").open("w",newline="") as f:
        columns=list(intervals[0]) if intervals else ["substep","event","stage","start_nodes","end_nodes","delta_elapsed_s"]
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(intervals)
    rc=int((root/"EXIT_CODE.txt").read_text().strip())
    audit=json.loads((root/"INPUT_AUDIT.json").read_text())
    last=snapshots[-1]
    subtotal=sum(last[k] for k in SUBSTAGES)
    contributions={k:{"seconds":round(last[k],6),
                       "percent_of_elapsed":round(100*last[k]/last["elapsed_s"],3)
                       if last["elapsed_s"]>0 else 0}
                   for k in SUBSTAGES}
    ordered=sorted(contributions, key=lambda k:contributions[k]["seconds"],reverse=True)
    report={
      "experiment":"03i Calculate_Discharge nested instrumentation",
      "physical_source":"author demo/6_tectonics at d18b7d270f4d671b80223e10dede329ad35cafdd",
      "optimized_c_source":"03g validated merge-only membership patch plus diagnostic-only 03d/03e/03i timers",
      "case":root.name,
      "input_grid":audit["grid"],
      "401_source_inputs_byte_identical_to_author":
        audit["source_hashes"]==audit["run_hashes"] if audit["grid"]==401 else None,
      "actual_runtime_flags":"-tf0.5 -qisost_model=0 -qplotting_mode=0",
      "process_exit_code":rc,
      "timed_out":rc==124,
      "surface_substeps_started":max(x["substep"] for x in snapshots),
      "surface_substeps_finished":len([x for x in snapshots if x["event"]=="END" and x["stage"]=="checks_and_total"]),
      "snapshots":len(snapshots),"last_event":last,
      "last_recorded_stage_components":contributions,
      "component_sum_excluding_nested_helper":round(subtotal,6),
      "dominant_measured_component":ordered[0] if ordered else None,
      "last_stage_open_on_timeout":last["stage"] if rc==124 else None,
      "nested_overlap_notice":"lake_input_s and attempt_delete_s are subsets of precheck_s/outlet_evap_s and must not be added to stage totals",
      "instrumentation_scope":"Aggregate timing and function counts only; no physics changes or solver acceleration in 03i",
      "scientific_validity_limit":"No 401 full 0–15 Myr reproduction; existing sediment NaN bug must be evaluated separately"
    }
    (root/"03I_DISCHARGE_QC.json").write_text(json.dumps(report,indent=2))
    print("03i QC SUMMARY",json.dumps({k:v for k,v in report.items()
         if k not in ("last_event","last_recorded_stage_components")}))
    print("03i LAST",json.dumps(last))
    print("03i SUBSTAGE RANK",json.dumps(contributions))
    return report

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("summarize_tisc_discharge.py CASE_DIRECTORY")
    main(sys.argv[1])
