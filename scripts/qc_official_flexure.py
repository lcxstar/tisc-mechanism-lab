#!/usr/bin/env python3
"""Numerically validate the author's -Q flexure reference; visualize full flex project.

Original upstream benchmark is in tisc/demo/README. These checks distinguish
reference reproduction from generic program-exit success. Standard-library
and NumPy/Matplotlib only, no modifications to upstream code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

def candidate_rows(path: Path):
    """TISC -Q prints gridded x, y, displacement in plain text, possibly
    surrounded by runtime diagnostic messages. Keep ONLY numeric triples."""
    triples=[]
    for line in path.read_text(errors="replace").splitlines():
        toks=line.strip().split()
        if len(toks) != 3:
            continue
        try:
            xyz=tuple(float(q) for q in toks)
        except ValueError:
            continue
        if all(math.isfinite(x) for x in xyz):
            triples.append(xyz)
    return triples

def reference_check(log: Path, size: int, target: float):
    rows=candidate_rows(log)
    centers=[v for x,y,v in rows if abs(x)<1e-4 and abs(y)<1e-4]
    value=centers[-1] if centers else None
    return {
        "grid": f"{size}x{size}",
        "expected_center_deflection_abs_m":target,
        "observed_center_deflection_abs_m":None if value is None else abs(value),
        "number_of_numeric_rows":len(rows),
        "center_rows":len(centers),
        "reference_tolerance_m":10.0,
        "pass":bool(value is not None and abs(abs(value)-target)<=10.0),
        "log":str(log),
    }

def project_check(case: Path):
    xy=case/"flex.xyzt"
    result={"has_xyzt":xy.exists(),"has_hrz":(case/"flex.hrz").exists(),
            "source_folder":str(case),"numerical_pass":False}
    if not xy.exists():
        return result
    try:
        data=np.loadtxt(xy,comments="#")
        if data.ndim != 2 or data.shape[0]!=141*141 or data.shape[1]<4 or not np.isfinite(data).all():
            result["parse_error"]=f"Unexpected flex.xyzt shape: {data.shape}"
            return result
        result.update({
            "n_grid_nodes":len(data),
            "xyzt_columns":int(data.shape[1]),
            "center_first_record_w_m":float(data[np.argmin(data[:,0]**2+data[:,1]**2),2]),
            "center_last_record_w_m":float(data[np.argmin(data[:,0]**2+data[:,1]**2),-2]),
            "numerical_pass":True,
        })
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        center_y=data[np.argmin(abs(data[:,1])),1]
        transect=data[np.isclose(data[:,1],center_y)]
        transect=transect[np.argsort(transect[:,0])]
        fig,ax=plt.subplots(figsize=(9,4.5),constrained_layout=True)
        ax.plot(transect[:,0],transect[:,2],label="First output: deflection")
        ax.plot(transect[:,0],transect[:,-2],label="Last output: deflection")
        ax.set(xlabel="Official model x (km)",ylabel="Deflection w (m)",title="Official flex project — Y centerline")
        ax.grid(alpha=.25);ax.legend()
        fig.savefig(case/"OFFICIAL_FLEXURE_TRANSECT.png",dpi=160);plt.close(fig)
    except Exception as exc:
        result["parse_error"]=f"{type(exc).__name__}: {exc}"
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path("results"))
    args=ap.parse_args()
    root=args.root
    a=reference_check(root/"Q_mode_N11.log",11,675.1)
    b=reference_check(root/"Q_mode_N51.log",51,711.0)
    project=project_check(root/"full_official_flex")
    report={
      "project":"TISC Mechanism Lab",
      "upstream":"danigeos/tisc",
      "pinned_commit":"d18b7d270f4d671b80223e10dede329ad35cafdd",
      "physical_code_patches":0,
      "reference_checks":[a,b],
      "full_official_flex":project,
      "overall_pass":bool(a["pass"] and b["pass"] and project["numerical_pass"]),
      "limitations":"This checks author numerical references and file outputs, not geological applicability.",
    }
    (root/"OFFICIAL_FLEXURE_QC.json").write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps(report,indent=2,ensure_ascii=False))
    if not report["overall_pass"]:
        raise SystemExit("FAIL: One or more official reference or project-output gates did not pass")
if __name__=="__main__":
    main()
