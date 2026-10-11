#!/usr/bin/env python3
"""Summarize 03f lake-operation timing in multiple TISC hydrology substeps.

Each 0.5-Myr step contains ~10 short surface-process substeps. Node counter
restarts at every Define_Drainage_Net() call. Function-call time counters,
in contrast, are cumulative throughout the full TISC process.
"""
import csv
import json
import re
import sys
from pathlib import Path

LINE = re.compile(r"(?m)^TISC_LAKE_STATS (.+)$")
REQUIRED=("nodes","add_calls","add_duplicates","add_total_s",
 "add_search_s","add_realloc_s","new_calls","new_total_s",
 "merge_calls","merge_total_s","merged_node_copies",
 "max_lake_nodes","nlakes")
INTEGERS={"nodes","add_calls","add_duplicates","new_calls",
          "merge_calls","merged_node_copies","max_lake_nodes","nlakes"}
CUMULATIVE=("add_calls","add_duplicates","new_calls","merge_calls",
 "merged_node_copies","add_total_s","add_search_s","add_realloc_s",
 "new_total_s","merge_total_s")

def main(folder):
    p=Path(folder)
    raw=(p/"RUN.log").read_text(errors="replace")
    snapshots=[]
    scan_number=0
    last_node=-1
    for match in LINE.finditer(raw):
        parts=dict(item.split("=",1) for item in match.group(1).split()
                   if "=" in item)
        if any(key not in parts for key in REQUIRED):
            raise ValueError(f"Malformed lake snapshot: {match.group(0)}")
        sample={k:int(parts[k]) if k in INTEGERS else float(parts[k])
                for k in REQUIRED}
        if sample["nodes"]<=last_node:
            scan_number+=1
        sample["scan_index"]=scan_number
        snapshots.append(sample)
        last_node=sample["nodes"]
    if not snapshots: raise RuntimeError("No lake stats found; inspect RUN.log")
    for prev,cur in zip(snapshots,snapshots[1:]):
        for key in CUMULATIVE:
            # Counters are cumulative across substeps, so must not decrease.
            if cur[key]+1e-4 < prev[key]:
                raise RuntimeError(f"Cumulative {key} decreased unexpectedly")
        if cur["scan_index"]==prev["scan_index"] and cur["nodes"]<=prev["nodes"]:
            raise RuntimeError("Nonmonotonic node count within a single scan")
    fields=("scan_index",)+REQUIRED
    with (p/"LAKE_OPERATION_PROGRESS.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        w.writerows(snapshots)

    intervals=[]
    for prev,cur in zip(snapshots,snapshots[1:]):
        if prev["scan_index"] != cur["scan_index"]: continue
        row={"scan_index":cur["scan_index"],"node_start":prev["nodes"],
             "node_end":cur["nodes"],"nodes_in_interval":cur["nodes"]-prev["nodes"]}
        for key in CUMULATIVE:
            row["delta_"+key]=round(cur[key]-prev[key],6)
        intervals.append(row)
    fields2=["scan_index","node_start","node_end","nodes_in_interval"]+[
        "delta_"+key for key in CUMULATIVE]
    with (p/"LAKE_OPERATION_INTERVALS.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields2)
        w.writeheader()
        w.writerows(intervals)

    rcfile=p/"EXIT_CODE.txt"
    rc=int(rcfile.read_text().strip()) if rcfile.exists() else None
    profile=p/"STAGE_PROFILE_QC.json"
    q=json.loads(profile.read_text()) if profile.exists() else {}
    aud=json.loads((p/"INPUT_AUDIT.json").read_text())
    n=int(aud.get("grid",0))**2
    complete_scans=sum(x["nodes"]==n for x in snapshots)
    report={"experiment":"03f lake operations",
      "case":p.name,
      "upstream_commit":aud.get("official_commit"),
      "input_grid":aud.get("grid"),
      "source_profiled":True,
      "inputs_match_source_byte_for_byte":aud.get("source_hashes")==aud.get("run_hashes"),
      "runtime_overrides":"-tf0.5 -qisost_model=0 -qplotting_mode=0",
      "exit_code":rc,"timeout":rc==124,
      "snapshots":len(snapshots),"surface_scan_count_started":scan_number+1,
      "surface_scan_count_finished":complete_scans,
      "sampled_nodes_last":snapshots[-1]["nodes"],
      "total_grid_nodes":n,
      "last_snapshot":snapshots[-1],
      "model_last_time_Myr":q.get("last_model_time_Myr"),
      "active_stage_at_interrupt":q.get("active_stage_at_interrupt") if rc==124 else None,
      "limitations":"Inclusive merge time overlaps nested add-node time; "
        "instrumentation changes runtime; incomplete final interval on timeout "
        "is not included in summary; no scientific mass conservation proven."
    }
    (p/"LAKE_OPERATION_QC.json").write_text(json.dumps(report,indent=2))
    print("03f SUMMARY",json.dumps(report,ensure_ascii=False))
    print("03f LAST_SNAPSHOTS",json.dumps(snapshots[-4:]))
    return report

if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("summarize_tisc_lake_ops.py DIRECTORY")
    main(sys.argv[1])
