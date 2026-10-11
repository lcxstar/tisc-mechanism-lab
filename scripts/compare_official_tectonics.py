#!/usr/bin/env python3
"""Compare official tectonic cases ONLY where grid/physical settings agree."""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT=Path("analysis/03_tectonics")
SOURCE=ROOT/"cases"
DEST=ROOT/"summary"
CASES=["original_401","baseline_81","ride0_81","slow2_81","no2_81"]

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    case_data={}
    output=[]
    for key in CASES:
        d=SOURCE/f"TISC03_CASE_{key}"
        p=d/"CASE_QC.json"
        if p.exists():
            q=json.loads(p.read_text())
            case_data[key]=d
            output.append(q)
        else:
            output.append({"case":key,"numeric_pass":False,"missing_artifact":True})
    flatkeys=["case","grid","actual_exit_code","numeric_pass","last_logged_time_Myr","n_steps",
              "final_block_count","number_of_author_unit_files","has_xyzt","has_hrz",
              "final_downward_w_max_m","final_downward_w_min_m","final_downward_w_mean_m",
              "final_center_w_m","final_topography_max_m","final_topography_min_m",
              "final_topography_mean_m"]
    with (DEST/"ALL_CASE_SUMMARY.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=flatkeys);w.writeheader()
        for q in output:w.writerow({k:q.get(k) for k in flatkeys})
    detail={"study":"TISC official 6_tectonics exact original and controlled mechanisms",
            "cases":output,"comparability_notice":"Never directly infer ride effect by comparing 401 to 81 resolution.",
            "ride_comparator":"baseline_81 versus ride0_81; only ride differs",
            "velocity_comparator":"baseline_81 versus slow2_81; only second velocity differs",
            "second_fault_exclusion":"baseline_81 versus no2_81; removal of a whole UNIT"}
    if "baseline_81" in case_data:
        b=case_data["baseline_81"]
        base=np.loadtxt(b/"CENTERLINE_DEFLECTION.csv",delimiter=",",skiprows=1)
        fig,ax=plt.subplots(figsize=(9.6,5.2),constrained_layout=True)
        for key in ("baseline_81","ride0_81","slow2_81","no2_81"):
            p=case_data.get(key)
            if not p or not (p/"CENTERLINE_DEFLECTION.csv").exists():continue
            z=np.loadtxt(p/"CENTERLINE_DEFLECTION.csv",delimiter=",",skiprows=1)
            if z.shape!=base.shape or not np.allclose(z[:,0:2],base[:,0:2]):
                detail[key+"_compare_error"]="coordinate inconsistency";continue
            ax.plot(z[:,0],z[:,2],label=key)
            delta=z[:,2]-base[:,2]
            detail[key+"_minus_baseline"]={
                "center_w_delta_m":float(delta[len(delta)//2]),
                "max_abs_along_centerline_m":float(np.max(np.abs(delta))),
                "mean_absolute_centerline_delta_m":float(np.mean(np.abs(delta)))}
        ax.set(title="Pinned official 6_tectonics | controlled 81x81 deflection comparison",
               xlabel="X (km), Y=0",ylabel="Flexural deflection w (m)")
        ax.grid(alpha=.25);ax.legend()
        fig.savefig(DEST/"FIG03_TECTONICS_VARIANT_DEFLECTION.png",dpi=180);plt.close(fig)
    detail["all_five_pass"]=all(q.get("numeric_pass",False) for q in output)
    detail["all_four_controls_pass"]=all(next((q.get("numeric_pass",False) for q in output if q.get("case")==key),False) for key in ("baseline_81","ride0_81","slow2_81","no2_81"))
    (DEST/"EXPERIMENT_03_SUMMARY.json").write_text(json.dumps(detail,indent=2,allow_nan=False))
    print(json.dumps(detail,indent=2,allow_nan=False))

if __name__=="__main__":main()
