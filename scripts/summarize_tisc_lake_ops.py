#!/usr/bin/env python3
"""Parse 03f cumulative lake-operation time & call counts.

A timed-out run can still return complete sampled evidence.  Raw per-call
time totals overlap: merge_total_s INCLUDES time inside Add_Node_To_Lake().
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

def main(folder):
    p=Path(folder)
    raw=(p/"RUN.log").read_text(errors="replace")
    snapshots=[]
    for match in LINE.finditer(raw):
        parts=dict(item.split("=",1) for item in match.group(1).split()
                   if "=" in item)
        if any(key not in parts for key in REQUIRED):
            raise ValueError(f"Malformed lake snapshot: {match.group(0)}")
        s={k:int(parts[k]) if k in INTEGERS else float(parts[k])
           for k in REQUIRED}
        snapshots.append(s)
    if not snapshots:
        raise RuntimeError("Missing TISC_LAKE_STATS snapshots; cannot attribute cost")
    for prev,cur in zip(snapshots,snapshots[1:]):
        if cur["nodes"] <= prev["nodes"]:
            raise RuntimeError("Nonmonotonic node counter, unexpected repeated scan")
        for k in ("add_calls","new_calls","merge_calls","merged_node_copies"):
            if cur[k] < prev[k]:
                raise RuntimeError(f"Counter {k} unexpectedly decreases")
    with (p/"LAKE_OPERATION_PROGRESS.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=REQUIRED)
        w.writeheader()
        w.writerows(snapshots)
    delta=[]
    for prev,cur in zip(snapshots,snapshots[1:]):
        dt={"node_start":prev["nodes"],"node_end":cur["nodes"],
            "nodes_in_interval":cur["nodes"]-prev["nodes"]}
        for k in ("add_calls","new_calls","merge_calls",
                  "merged_node_copies","add_total_s","add_search_s",
                  "add_realloc_s","new_total_s","merge_total_s"):
            dt[f"delta_{k}"]=round(cur[k]-prev[k],6)
        delta.append(dt)
    with (p/"LAKE_OPERATION_INTERVALS.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(delta[0]) if delta else
                         ["node_start","node_end","nodes_in_interval"])
        w.writeheader()
        w.writerows(delta)
    rcfile=p/"EXIT_CODE.txt"
    rc=int(rcfile.read_text().strip()) if rcfile.exists() else None
    profile=p/"STAGE_PROFILE_QC.json"
    q=json.loads(profile.read_text()) if profile.exists() else {}
    aud=json.loads((p/"INPUT_AUDIT.json").read_text())
    report={"experiment":"03f lake operations",
      "case":p.name,
      "upstream_commit":aud.get("official_commit"),
      "input_grid":aud.get("grid"),
      "source_profiled":True,
      "inputs_match_source_byte_for_byte":aud.get("source_hashes")==aud.get("run_hashes"),
      "runtime_overrides":aud.get("run_override_flags"),
      "exit_code":rc,
      "timeout":rc==124,
      "snapshots":len(snapshots),
      "sampled_nodes_last":snapshots[-1]["nodes"],
      "total_grid_nodes":aud.get("grid",0)**2,
      "last_snapshot":snapshots[-1],
      "model_last_time_Myr":q.get("last_model_time_Myr"),
      "active_stage_at_interrupt":q.get("active_stage_at_interrupt"),
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
