#!/usr/bin/env python3
"""Report genuine 401 coupled-demo progress, never call timeout success a simulation pass."""
import json,re,hashlib,sys
from pathlib import Path

SOURCE=("demo.PRM","demo1.UNIT","demo2.UNIT","demo.PRFL")
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main(root,horizon):
    d=Path(root)
    raw=(d/"RUN.log").read_text(errors="replace")
    code=int((d/"EXIT_CODE.txt").read_text().strip())
    author=Path("upstream/tisc/demo/6_tectonics")
    sha_file={}
    for fn in SOURCE:
        source=author/fn; actual=d/fn
        sha_file[fn]={"author":h(source),"model":h(actual),"same":h(source)==h(actual)}
    full_exact=all(v["same"] for v in sha_file.values())
    ts=[float(x) for x in re.findall(r"T=\s*(\d+(?:\.\d+)?)\s*My",raw)]
    nanrows=[x[:300] for x in raw.splitlines() if re.search(r"\b(?:nan|inf)\b",x,re.I)]
    nonfin_sed=[x[:300] for x in nanrows if "outp_seds" in x]
    time_seqs=ts[-40:]
    file_sizes={p.name:p.stat().st_size for p in d.glob("demo.*") if p.is_file()}
    wall_path=d/"WALL_SEC.txt"
    wall=float(wall_path.read_text()) if wall_path.exists() else None
    actual_flags=(d/"ACTUAL_COMMAND.txt").read_text().strip()
    report={
      "run_type":"official tectonics input with original flexure and optimized hydro C",
      "upstream_sha":"d18b7d270f4d671b80223e10dede329ad35cafdd",
      "model_input_sha256":sha_file,
      "original_401_input_byte_exact":full_exact,
      "model_grid":"401x401",
      "author_flexure_isost_model":"1, unchanged from demo.PRM",
      "runtime_flags":actual_flags,
      "requested_time_final_Myr":float(horizon),
      "exit_code":code,"timeout":code==124,
      "wall_seconds":wall,
      "last_logged_model_time_Myr":ts[-1] if ts else None,
      "n_timestamps":len(ts),
      "recent_model_timestamps_Myr":time_seqs,
      "completed_requested_horizon":bool(
          code==0 and ts and abs(ts[-1]-float(horizon))<1e-5 and full_exact),
      "sediment_export_nonfinite_count":len(nonfin_sed),
      "sediment_export_nonfinite_examples":nonfin_sed[:8],
      "any_nonfinite_text_lines":len(nanrows),
      "other_nonfinite_examples":nanrows[:10],
      "observed_output_files_bytes":file_sizes,
      "original_author_unmodified_binary":False,
      "complete_15_Myr_claim_allowed":bool(code==0 and ts and abs(ts[-1]-15)<1e-5 and full_exact and float(horizon)==15),
      "scientific_mass_conservation_proven":False,
    }
    (d/"03K_COUPLED_RUN_QC.json").write_text(json.dumps(report,indent=2))
    print("03K COUPLED QC",json.dumps({k:v for k,v in report.items()
      if k not in ("model_input_sha256","recent_model_timestamps_Myr","observed_output_files_bytes","other_nonfinite_examples","sediment_export_nonfinite_examples")}))
    if not full_exact:
        raise SystemExit("Original 401 input differs from pinned author; invalid trial")
    return report
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("summarize_03k_coupled_run.py RUN_DIR EXPECTED_HORIZON_MYR")
    main(Path(sys.argv[1]),sys.argv[2])
