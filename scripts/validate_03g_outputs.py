#!/usr/bin/env python3
"""Strict 03g equivalence audit: compare baseline vs merge-optimized TISC.

No baseline modification except compile-only U+00A0 space normalization.
Compare all author physical output files byte-for-byte (including binary ALL)
and summarize finite drainage elevation, water and sediment fields.
This is a gate for *numerical equivalence*, not a declaration that upstream
sediment conservation is physically correct.
"""
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

COMPARE_EXT={".all",".xyw",".hrz",".st",".pfl",".lak",".bas",".xyzt"}
MANDATORY={".all",".xyw",".hrz",".st"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_exit(p):return int((p/"EXIT_CODE.txt").read_text().strip())
def times(path):
    text=(path/"RUN.log").read_text(errors="replace")
    xs=[float(v) for v in re.findall(r"(?m)^\s*T=\s*(\d+(?:\.\d+)?)\s*My",text)]
    return xs
def summarize_xyw(path,n):
    p=path/"demo.xyw"
    if not p.exists():return {"present":False}
    total_rows=0
    max_topo=-math.inf; min_topo=math.inf
    sum_topo=sum_q=sum_sed=0.0
    n_nonfinite=0
    river_types={}
    with p.open(errors="replace") as f:
        for line in f:
            if not line.strip() or line.startswith("#"):continue
            tok=line.split()
            if len(tok)<7: raise ValueError(f"Bad xyw row: {tok[:10]}")
            try:
                q=float(tok[2]);sed=float(tok[3]);topo=float(tok[6])
            except ValueError as ex:
                raise ValueError(f"Malformed numerical output row: {tok[:8]}") from ex
            if not all(math.isfinite(v) for v in (q,sed,topo)):
                n_nonfinite+=1
            else:
                sum_q+=q;sum_sed+=sed;sum_topo+=topo
                min_topo=min(min_topo,topo);max_topo=max(max_topo,topo)
            river_types[tok[4]]=river_types.get(tok[4],0)+1
            total_rows+=1
    return {"present":True,"rows":total_rows,"expected_rows":n*n,
      "nonfinite_q_sed_topo":n_nonfinite,"min_topo_m":min_topo,
      "max_topo_m":max_topo,"mean_topo_m":sum_topo/total_rows if total_rows else None,
      "total_local_q_m3_s":sum_q,"total_local_sed_kg_s":sum_sed,
      "drainage_types":river_types}

def main(directory):
    root=Path(directory)
    audit=json.loads((root/"INPUT_AUDIT.json").read_text())
    n=audit["Nx"]
    ref=root/"reference";fast=root/"optimized"
    all_names={p.name for d in (ref,fast) for p in d.iterdir()
               if p.name.startswith("demo.") and p.suffix in COMPARE_EXT}
    rows=[]
    for name in sorted(all_names):
        x=ref/name;y=fast/name
        row={"filename":name,"ext":x.suffix,"reference_exists":x.exists(),
             "optimized_exists":y.exists(),
             "reference_bytes":x.stat().st_size if x.exists() else None,
             "optimized_bytes":y.stat().st_size if y.exists() else None,
             "reference_sha256":sha(x) if x.exists() else "",
             "optimized_sha256":sha(y) if y.exists() else "",
             "byte_exact_match":bool(x.exists() and y.exists() and sha(x)==sha(y))}
        rows.append(row)
    cols=["filename","ext","reference_exists","optimized_exists",
          "reference_bytes","optimized_bytes","reference_sha256",
          "optimized_sha256","byte_exact_match"]
    with (root/"FILE_COMPARISON.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=cols)
        writer.writeheader();writer.writerows(rows)
    missing=[suffix for suffix in MANDATORY if not any(
        x["ext"]==suffix and x["byte_exact_match"] for x in rows)]
    mismatches=[r["filename"] for r in rows if not r["byte_exact_match"]]
    times_ref=times(ref);times_fast=times(fast)
    xref=summarize_xyw(ref,n);xfast=summarize_xyw(fast,n)
    score={
      "experiment":"03g reference vs optimized TISC",
      "grid":n,"case":audit["case"],"mode":audit["mode"],
      "flags":audit["run_flags"],
      "original_physical_inputs_identical":audit["reference_optimized_same_inputs"],
      "author_source_commit":audit["author_upstream_commit"],
      "reference_exit":read_exit(ref),"optimized_exit":read_exit(fast),
      "reference_times":times_ref,"optimized_times":times_fast,
      "required_outputs_missing_or_mismatched":missing,
      "all_changed_output_names":mismatches,
      "n_matched_output_files":sum(r["byte_exact_match"] for r in rows),
      "n_compared_output_files":len(rows),
      "reference_xyw":xref,"optimized_xyw":xfast,
      "reference_seconds":float((ref/"WALL_SEC.txt").read_text().strip()),
      "optimized_seconds":float((fast/"WALL_SEC.txt").read_text().strip()),
      "scientific_sediment_mass_conservation_validated":False,
    }
    if score["optimized_seconds"]>0:
        score["speedup_factor"]=round(score["reference_seconds"]/score["optimized_seconds"],3)
    data_finite=(xref.get("present") and xfast.get("present")
        and xref.get("rows")==n*n and xfast.get("rows")==n*n
        and xref.get("nonfinite_q_sed_topo")==0
        and xfast.get("nonfinite_q_sed_topo")==0)
    expected_end=0.5 if audit["mode"]=="first_step" else 15.0
    same_time=(len(times_ref)>=2 and times_ref==times_fast
               and abs(times_ref[-1]-expected_end)<1e-5)
    score["numerical_equivalence_pass"]=bool(
        score["reference_exit"]==0 and score["optimized_exit"]==0
        and audit["reference_optimized_same_inputs"]
        and not missing and not mismatches and data_finite and same_time)
    score["nonfinite_sediment_export_in_reference"]=bool(
        re.search(r"\boutp_seds:\s*[+-]?nan\b",
           (ref/"RUN.log").read_text(errors="replace"),re.I))
    score["nonfinite_sediment_export_in_optimized"]=bool(
        re.search(r"\boutp_seds:\s*[+-]?nan\b",
           (fast/"RUN.log").read_text(errors="replace"),re.I))
    (root/"VALIDATION_QC.json").write_text(json.dumps(score,indent=2,allow_nan=False))
    print("03g VALIDATION",json.dumps({
        k:v for k,v in score.items() if k not in
            ("reference_xyw","optimized_xyw","reference_times","optimized_times")},
        ensure_ascii=False))
    if not score["numerical_equivalence_pass"]:
        raise SystemExit("03g FAIL: numerical equivalence has not been proven")

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("validate_03g_outputs.py PAIR_ROOT")
    main(sys.argv[1])
