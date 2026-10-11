#!/usr/bin/env python3
"""03u0 review: paired byte-exact physical fields and float32 rounding counters.

No model output comparisons from detached artifacts: the two binaries here are
built from the same pinned upstream checkout with/without ONLY 03u observer.
"""
import csv,hashlib,json,re,sys,math
from pathlib import Path
FIELDS=[".xyw",".st",".hrz",".lak",".bas",".pfl",".xyzt"]
KINDS=["sediment_topo","sediment_block","sediment_Dq","erosion_topo","erosion_block","river_inflow","lake_inflow","lake_outflow"]
PAT=re.compile(r'TISC_03U0 kind=(\w+) timeMyr=([^\s]+) calls=(\d+) round_to_zero=(\d+) finite_errors=(\d+) ideal_increment_sum=([^\s]+) dropped_abs_sum=([^\s]+) error_signed_sum=([^\s]+) error_abs_sum=([^\s]+) max_abs_error=([^\s]+) max_abs_dropped=([^\s]+) max_existing=([^\s]+) max_abs_increment=([^\s]+)')
KEYS=["kind","timeMyr","calls","round_to_zero","finite_errors","ideal_increment_sum","dropped_abs_sum","error_signed_sum","error_abs_sum","max_abs_error","max_abs_dropped","max_existing","max_abs_increment"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metrics(log):
    return [dict(zip(KEYS,[m[1],float(m[2]),int(m[3]),int(m[4]),int(m[5])]+
           [float(m[i]) for i in range(6,14)])) for m in PAT.finditer(log)]
def main(p,horizon):
    p=Path(p);ref=p/"reference";obs=p/"optimized";steps=[]
    ref_log=(ref/"RUN.log").read_text(errors="replace")
    obs_log=(obs/"RUN.log").read_text(errors="replace")
    profile=metrics(obs_log)
    for version,d in [("reference",ref),("observed",obs)]:
        exit_code=int((d/"EXIT_CODE.txt").read_text())
        times=[float(x) for x in re.findall(r"(?m)^\s*T=\s*(\d+(?:\.\d+)?)\s*My", (d/"RUN.log").read_text(errors="replace"))]
        steps.append({"variant":version,"process_exit":exit_code,"last_timeMyr":times[-1] if times else None,"time_count":len(times),"wall_seconds":float((d/"WALL_SEC.txt").read_text())})
    rows=[]
    for suffix in FIELDS:
        a=ref/("demo"+suffix);b=obs/("demo"+suffix)
        rows.append({"field":suffix,"reference_exists":a.exists(),"observed_exists":b.exists(),
                     "exact":a.exists() and b.exists() and sha(a)==sha(b),
                     "reference_sha256":sha(a) if a.exists() else None,
                     "observed_sha256":sha(b) if b.exists() else None})
    record_by_kind={}
    for kind in KINDS:
        v=[x for x in profile if x["kind"]==kind]
        record_by_kind[kind]={
            "reported_main_steps":len(v),"total_updates":sum(x["calls"] for x in v),
            "round_to_zero_updates":sum(x["round_to_zero"] for x in v),
            "round_to_zero_fraction":sum(x["round_to_zero"] for x in v)/max(1,sum(x["calls"] for x in v)),
            "total_signed_increment":sum(x["ideal_increment_sum"] for x in v),
            "sum_abs_dropped_increments":sum(x["dropped_abs_sum"] for x in v),
            "signed_rounding_error_sum":sum(x["error_signed_sum"] for x in v),
            "sum_abs_local_rounding_error":sum(x["error_abs_sum"] for x in v),
            "max_abs_local_error":max((x["max_abs_error"] for x in v),default=None),
            "max_abs_dropped_increment":max((x["max_abs_dropped"] for x in v),default=None)
        }
    audit=json.loads((p/"INPUT_AUDIT.json").read_text())
    input_match=audit["reference_optimized_same_inputs"]
    is_original=(audit["Nx"]!=401 or all(audit["reference_sha256"][name]==audit["source_sha256"][name] for name in audit["reference_sha256"]))
    good=bool(input_match and is_original and len(profile)>=len(KINDS) and all(x["exact"] for x in rows)
              and all(x["process_exit"]==0 and x["last_timeMyr"] is not None
              and abs(x["last_timeMyr"]-float(horizon))<1e-5 for x in steps)
              and all(x["finite_errors"]==0 for x in profile)
              and set(x["kind"] for x in profile)==set(KINDS))
    result={"variant":"03u-0 read-only 32/64 single-store operation diagnostic",
        "source_sha":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd",
        "Nx":audit["Nx"],"requested_horizon_Myr":float(horizon),
        "input_identical":input_match,"original_401_input_sha256_match":is_original,
        "physical_fields_all_byte_exact":all(x["exact"] for x in rows),
        "physical_fields":rows,"steps":steps,"diagnostic_main_step_records":len(profile)//len(KINDS),
        "operation_precision_metrics":record_by_kind,
        "observer_pass":good,
        "full_double_model_ran":False,
        "interpretation":"Single float32 state update vs double ideal at same stored float state, NOT full float64 forward simulation"}
    (p/"03U0_PRECISION_QC.json").write_text(json.dumps(result,indent=2))
    with (p/"03U0_PRECISION_BY_STEP.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=KEYS);w.writeheader();w.writerows(profile)
    print("03U0_QC "+json.dumps({k:v for k,v in result.items() if k not in ("physical_fields","operation_precision_metrics")}))
    print("03U0_METRICS "+json.dumps(record_by_kind))
    if not good:raise SystemExit("03u-0 FAIL: source-only observational equivalence / inputs / timeline / metrics")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("summarize_03u0_precision.py PAIR_ROOT END_MYR")
    main(sys.argv[1],sys.argv[2])
