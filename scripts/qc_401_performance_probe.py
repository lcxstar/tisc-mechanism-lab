#!/usr/bin/env python3
"""Record honest 401 performance diagnosis, including timeouts and partial output."""
import json,re,sys
from pathlib import Path
import numpy as np

p=Path(sys.argv[1]);raw=(p/"RUN.log").read_text(errors="replace") if (p/"RUN.log").exists() else ""
audit=json.loads((p/"INPUT_AUDIT.json").read_text())
rc=int((p/"EXIT_CODE.txt").read_text()) if (p/"EXIT_CODE.txt").exists() else -999
times=[float(z) for z in re.findall(r"(?m)^\s*T=\s*([-+\d.eE]+)\s*My",raw)]
duration=(p/"RUNTIME_SEC.txt").read_text().strip() if (p/"RUNTIME_SEC.txt").exists() else None
if duration:
    matches=re.findall(r"(?m)^\s*([0-9]+(?:\.[0-9]+)?)\s*$", duration)
    duration=float(matches[-1]) if matches else None
result={"case":audit["case"],"original_input_hashes_match":audit["grid"]==401 and
    audit["source_hashes"]==audit["run_hashes"],
    "overrides":audit["run_override_flags"],"physical_model_full_original":False,
    "exit_code":rc,"timeout":rc==124,"numeric_pass":False,
    "last_logged_time_Myr":times[-1] if times else None,
    "time_log_entries":len(times),"wall_seconds":float(duration) if duration else None,
    "has_time_end":"Time end:" in raw,
    "has_hrz":(p/"demo.hrz").exists(),"has_xyzt":(p/"demo.xyzt").exists(),
    "sediment_flux_nonfinite_logged":bool(re.search(r"(?i)outp_seds\s*:\s*[-+]?nan",raw)),
    "scientific_mass_budget_pass":None,  # No mass-balance closure has been independently audited}
xy=p/"demo.xyzt"
if xy.exists():
    try:
        a=np.loadtxt(xy)
        result["output_rows"]=int(a.shape[0])
        result["output_columns"]=int(a.shape[1])
        result["finite_output"]=bool(np.isfinite(a).all())
        if a.ndim==2 and a.shape[1]==5 and np.isfinite(a).all():
            result["output_current_max_w_m"]=float(a[:,2].max())
            result["output_current_min_w_m"]=float(a[:,2].min())
    except Exception as e:result["xyzt_error"]=str(e)
if rc==0:
    expected_end=15.0 if audit["grid"]==121 else .5
    result["numeric_pass"]=bool(result["has_time_end"] and result["has_hrz"] and
      result["has_xyzt"] and result.get("finite_output",False) and
      times and abs(times[-1]-expected_end)<.11)
(p/"PERFORMANCE_QC.json").write_text(json.dumps(result,indent=2,allow_nan=False))
print(json.dumps(result,indent=2,allow_nan=False))
