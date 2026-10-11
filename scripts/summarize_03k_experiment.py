#!/usr/bin/env python3
"""QC for controlled physics correction (NOT literal original-source reproduction)."""
import json,re,sys
from pathlib import Path
def main(path,expected_time,require_zero_nan=True):
    p=Path(path)
    raw=(p/"RUN.log").read_text(errors="replace")
    rc=int((p/"EXIT_CODE.txt").read_text())
    times=[float(x) for x in re.findall(r"T=\s*(\d+(?:\.\d+)?)\s*My",raw)]
    outputs=re.findall(r"outp_seds:\s*([^\s]+)",raw)
    guard=[int(x) for x in re.findall(r"TISC_03K_GUARD negative_incision_slopes=(\d+)",raw)]
    nan_out=[x for x in outputs if re.search(r"nan|inf",x,re.I)]
    lines=[l for l in raw.splitlines() if "eros_nosd:" in l and "sedim_inc:" in l]
    params=[]
    for l in lines:
        m=re.search(r"eros_nosd:\s*(\S+).*?sedim_inc:\s*(\S+).*?outp_seds:\s*(\S+)",l)
        if not m:continue
        try:
            eros,sedim,out=(float(m[i]) for i in (1,2,3))
            ref=max(abs(eros),abs(sedim),abs(out),1)
            params.append({"eros_N":eros,"sedim_N":sedim,"out_N":out,
                        "normalized_mass_residual":(eros-sedim-out)/ref})
        except ValueError:pass
    report={
       "experiment":"03k controlled physics correction, not byte-identical author source",
       "observed_process_exit":rc,"expected_horizon_Myr":float(expected_time),
       "last_logged_time_Myr":times[-1] if times else None,
       "completed_horizon":bool(rc==0 and times and abs(times[-1]-float(expected_time))<1e-5),
       "final_sediment_output_nonfinite":bool(nan_out),
       "sediment_output_nonfinite_count":len(nan_out),
       "negative_incision_slope_fallback_total":sum(guard),
       "total_fluid_substeps_with_slope_guard_metrics":len(guard),
       "num_sediment_mass_balance_records":len(params),
       "max_abs_normalized_mass_residual":max((abs(x["normalized_mass_residual"]) for x in params),default=None),
       "first_three_mass_balance_lines":params[:3],
       "last_three_mass_balance_lines":params[-3:],
       "mass_conservation_proven":False,
       "numerical_equivalence_to_unmodified_author":False,
       "fixed_physics_claim_scope":"negative slope clamped to zero in fractional incision only",
    }
    (p/"03K_EXPERIMENTAL_FIX_QC.json").write_text(json.dumps(report,indent=2))
    print("03K FIX QC",json.dumps(report))
    if not report["completed_horizon"]:raise SystemExit("Failed to finish requested trial")
    if require_zero_nan and report["final_sediment_output_nonfinite"]:
        raise SystemExit("Sediment outp_seds still has NaN or Inf")
    if not guard:raise SystemExit("No proof physical guard ran")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("summarize_03k_experiment.py DIR EXPECTED_TIME_MYR")
    main(sys.argv[1],sys.argv[2])
