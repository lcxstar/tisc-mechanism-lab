#!/usr/bin/env python3
"""03u1 controlled double intermediate versus accepted float32 baseline.

This study intentionally alters numerical physics; write numeric differences
for major fields, preserve model time/equation/inputs. No equivalence claim.
"""
import csv,hashlib,json,math,re,sys
from itertools import zip_longest
from pathlib import Path
FIELDS=(".xyw",".st",".hrz",".lak",".bas",".pfl",".xyzt")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compare(a,b,ext):
    data={"field":"demo"+ext,"byte_equal":sha(a)==sha(b),"different_rows":0,"numeric_different_tokens":0,"non_numeric_changed_rows":0,"max_abs_difference":0,"sum_sq_diff":0.0,"compared_numeric_tokens":0,"lines_compared":0,"unpaired_lines":0}
    xytopo={"n":0,"sum_sq":0.0,"max_abs":0.0,"mean":0.0}
    # Original output may include different numbers of stratigraphic columns.
    with a.open(errors="replace") as fa,b.open(errors="replace") as fb:
        for iline,(left,right) in enumerate(zip_longest(fa,fb),1):
            if left is None or right is None:
                data["different_rows"]+=1
                data["unpaired_lines"]+=1
                continue
            data["lines_compared"]+=1
            if left==right:continue
            if left.startswith("#") and right.startswith("#"):continue
            t1=left.split();t2=right.split()
            data["different_rows"]+=1
            if len(t1)!=len(t2):
                data["non_numeric_changed_rows"]+=1;continue
            for k,(a0,b0) in enumerate(zip(t1,t2)):
                if a0==b0:continue
                try:
                    v=float(a0);w=float(b0)
                except ValueError:
                    data["non_numeric_changed_rows"]+=1
                    continue
                if not math.isfinite(v) or not math.isfinite(w):raise RuntimeError(f"Nonfinite {ext}, line {iline}")
                delta=w-v
                data["numeric_different_tokens"]+=1
                data["compared_numeric_tokens"]+=1
                data["sum_sq_diff"]+=delta*delta
                data["max_abs_difference"]=max(data["max_abs_difference"],abs(delta))
                if ext==".xyw" and k==5:
                    xytopo["n"]+=1
                    xytopo["sum_sq"]+=delta*delta
                    xytopo["max_abs"]=max(xytopo["max_abs"],abs(delta))
                    xytopo["mean"]+=delta
    data["changed_value_RMS"]=math.sqrt(data["sum_sq_diff"]/data["compared_numeric_tokens"]) if data["compared_numeric_tokens"] else 0.0
    data.pop("sum_sq_diff")
    if ext==".xyw":
        data["changed_topography_cells"]=xytopo["n"]
        data["changed_topography_max_abs_m"]=xytopo["max_abs"]
        data["changed_topography_RMS_on_changed_cells_m"]=math.sqrt(xytopo["sum_sq"]/xytopo["n"]) if xytopo["n"] else 0
        data["changed_topography_mean_m"]=xytopo["mean"]/xytopo["n"] if xytopo["n"] else 0
    return data
def run_status(p):
    log=(p/"RUN.log").read_text(errors="replace")
    times=[float(x) for x in re.findall(r"(?m)^\s*T=\s*(\d+(?:\.\d+)?)\s*My",log)]
    balances=[float(x) for x in re.findall(r"TISC_03T_CORRECTED_BALANCE[^\n]*balance_pct=([^\s]+)",log)]
    return {"exit":int((p/"EXIT_CODE.txt").read_text()),"last_time_Myr":times[-1] if times else None,
      "records":len(balances),"max_abs_budget_pct":max((abs(x) for x in balances),default=None),
      "wall_seconds":float((p/"WALL_SEC.txt").read_text())}
def main(root,horizon):
    root=Path(root);reference=root/"reference";candidate=root/"optimized";audit=json.loads((root/"INPUT_AUDIT.json").read_text())
    inputs=audit["reference_optimized_same_inputs"]
    exact_401=audit["Nx"]!=401 or all(audit["reference_sha256"][x]==audit["source_sha256"][x] for x in audit["source_sha256"])
    status={"reference":run_status(reference),"candidate":run_status(candidate)}
    fields=[compare(reference/("demo"+x),candidate/("demo"+x),x) for x in FIELDS]
    pass_gate=bool(inputs and exact_401 and
          all(x["exit"]==0 and x["last_time_Myr"] is not None
          and abs(x["last_time_Myr"]-float(horizon))<1e-5
          and x["max_abs_budget_pct"] is not None
          and x["max_abs_budget_pct"]<.001 for x in status.values()))
    result={"experiment":"03u1 single intermediate double sediment thickness sensitivity",
            "author_source":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd",
            "grid":audit["Nx"],"horizonMyr":float(horizon),"inputs_byte_exact":inputs,
            "original_401_input_sha256_match":exact_401,"status":status,"field_differences":fields,
            "physical_arithmetic_modified":True,"full_double_state_model":False,
            "non_grid_aligned_lak_lines_are_not_numeric_spatial_differences":True,
            "completed_sanity_gate":pass_gate}
    (root/"03U1_PRECISION_QC.json").write_text(json.dumps(result,indent=2))
    with (root/"03U1_FIELD_DIFF.csv").open("w",newline="") as f:
        cols=list(fields[0].keys())
        for row in fields[1:]:
            for key in row:
                if key not in cols:cols.append(key)
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(fields)
    print("03U1_QC "+json.dumps({k:v for k,v in result.items() if k!="field_differences"}))
    print("03U1_DIFF "+json.dumps([{k:v for k,v in row.items() if k in ("field","byte_equal","different_rows","max_abs_difference","changed_topography_cells","changed_topography_max_abs_m")} for row in fields]))
    if not pass_gate:raise SystemExit("03u1 physical numeric trial failed time/input/mass/sanity check")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("summarize_03u1_physics.py PAIR_ROOT HORIZON_MYR")
    main(sys.argv[1],sys.argv[2])
