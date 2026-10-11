#!/usr/bin/env python3
"""Audit literal original TISC 401x401 full run, timeout evidence and mass budget."""
import json, math, re, sys
from pathlib import Path

folder=Path(sys.argv[1])
log=(folder/"RUN.log").read_text(errors="replace") if (folder/"RUN.log").is_file() else ""
rc=int((folder/"EXIT_CODE.txt").read_text().strip()) if (folder/"EXIT_CODE.txt").exists() else None
times=[float(s) for s in re.findall(r"(?m)^\s*T=\s*([-+]?\d+(?:\.\d+)?)\s*My",log)]
mass=re.findall(r"(?m)outp_seds\s*:\s*([-+]?nan|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)",log,re.I)
finite_mass=(len(mass)>0 and all(math.isfinite(float(v)) for v in mass))
original=folder/"INPUT_AUDIT.json"
audit=json.loads(original.read_text()) if original.exists() else {}
orig_equal=(audit.get("case")=="original_401" and len(audit.get("modified_files",{}))==0 and
    audit.get("original_source_hashes")=={k:v for k,v in audit.get("runtime_input_hashes",{}).items()
                              if k in audit.get("original_source_hashes",{})})
report={
    "experiment":"literal author 401x401 6_tectonics",
    "upstream_commit":"d18b7d270f4d671b80223e10dede329ad35cafdd",
    "literal_input_file_sha256_identical":bool(orig_equal),
    "process_exit_code":rc,
    "exit_is_timeout":rc==124,
    "logged_step_count":len(times),
    "last_logged_time_Myr":times[-1] if times else None,
    "model_final_time_Myr":15.0,
    "has_Time_end_marker":"Time end:" in log,
    "has_xyzt":(folder/"demo.xyzt").exists(),
    "has_hrz":(folder/"demo.hrz").exists(),
    "has_restart_all":(folder/"demo.all").exists(),
    "total_logged_sediment_flux_values":len(mass),
    "all_logged_sediment_flux_finite":finite_mass,
    "nonfinite_logged_sediment_flux_values":sum(not math.isfinite(float(v)) for v in mass),
}
report["full_0_15_Myr_completed"]=bool(orig_equal and rc==0 and times and abs(times[-1]-15.0)<0.11
    and report["has_Time_end_marker"] and report["has_xyzt"] and report["has_hrz"])
report["scientific_sediment_balance_valid"]=bool(report["full_0_15_Myr_completed"] and finite_mass)
report["important_caveat"]="All fluxes finite does not independently prove conservation; a separate mass-balance residual is still required."
(folder/"ORIGINAL_401_QC.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
