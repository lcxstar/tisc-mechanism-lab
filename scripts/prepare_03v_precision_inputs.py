#!/usr/bin/env python3
"""Prepare exact paired original 6_tectonics inputs for convergence sweeps.

Change ONLY Nx, Ny, dt, dt_eros on an explicit experimental parameter grid.
The author .UNIT/.PRFL and all other .PRM lines retain exact author bytes.
"""
import argparse,hashlib,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AUTHOR=ROOT/"upstream/tisc/demo/6_tectonics"
FILES=("demo.PRM","demo1.UNIT","demo2.UNIT","demo.PRFL")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(args):
    if args.grid not in (81,121,201,401):raise SystemExit("Unsupported experiment grid")
    if (args.dt,args.dt_eros) not in ((.5,.05),(.5,.025),(.25,.025)):
        raise SystemExit("Only pre-registered temporal controls allowed")
    dest=Path(args.destination)
    if dest.exists():shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for variant in ("reference","optimized"):
        d=dest/variant;d.mkdir()
        for fn in FILES:shutil.copy2(AUTHOR/fn,d/fn)
    for variant in ("reference","optimized"):
        p=dest/variant/"demo.PRM"
        s=p.read_text(encoding="latin-1")
        values={"Nx":args.grid,"Ny":args.grid,"dt":args.dt,"dt_eros":args.dt_eros}
        old_values={"Nx":401,"Ny":401,"dt":0.5,"dt_eros":0.05}
        if args.grid==401 and args.dt==.5 and args.dt_eros==.05:continue
        for key,value in values.items():
            v = f"{value:g}" if isinstance(value,float) else str(value)
            if float(value)==old_values[key]:continue
            pat=rf"(?m)^({re.escape(key)}\s+)(\S+)"
            matches=list(re.finditer(pat,s))
            if len(matches)!=1:raise RuntimeError(f"Ambiguous author {key} in PRM")
            orig=matches[0].group(2)
            if float(orig)!=float(old_values[key]):raise RuntimeError(f"Unexpected upstream {key}={orig}")
            s,c=re.subn(pat,lambda m:m.group(1)+v,s,count=1)
            if c!=1:raise RuntimeError(f"Cannot substitute {key}")
        p.write_text(s,encoding="latin-1")
    inputs_ref={x:sha(dest/"reference"/x) for x in FILES}
    inputs_alt={x:sha(dest/"optimized"/x) for x in FILES}
    upstream={x:sha(AUTHOR/x) for x in FILES}
    if inputs_ref!=inputs_alt:raise RuntimeError("PAIRED INPUTS DIFFER")
    if any(inputs_ref[x]!=upstream[x] for x in FILES if x!="demo.PRM"):raise RuntimeError("Original tectonic geology files changed")
    if args.grid==401 and args.dt==.5 and args.dt_eros==.05 and inputs_ref!=upstream:raise RuntimeError("Unexpected nonbyte author original inputs")
    audit={"experiment":"03v staged numerical divergence / time-space controls",
        "author_source":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd",
        "Nx":args.grid,"Ny":args.grid,"dt_Myr":args.dt,"dt_eros_Myr":args.dt_eros,
        "horizon_Myr":args.horizon,
        "changes_from_author":{"Nx":args.grid!=401,"Ny":args.grid!=401,
            "dt":args.dt!=.5,"dt_eros":args.dt_eros!=.05},
        "author_full_inputs_byte_exact":inputs_ref==upstream,
        "other_author_geological_parameters_untouched":True,
        "isost_model_preserved":1,
        "source_sha256":upstream,"reference_sha256":inputs_ref,
        "optimized_sha256":inputs_alt,"reference_optimized_same_inputs":True,
        "PRM_full_text_author_unmodified":args.grid==401 and args.dt==.5 and args.dt_eros==.05}
    (dest/"INPUT_AUDIT.json").write_text(json.dumps(audit,indent=2))
    print("03V_INPUTS",json.dumps({k:v for k,v in audit.items() if k not in ("source_sha256","reference_sha256","optimized_sha256")}))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("destination")
    p.add_argument("--grid",type=int,required=True)
    p.add_argument("--dt",type=float,default=.5)
    p.add_argument("--dt-eros",type=float,default=.05)
    p.add_argument("--horizon",type=float,required=True)
    main(p.parse_args())
