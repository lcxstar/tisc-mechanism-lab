#!/usr/bin/env python3
"""Prepare high-resolution performance isolation without altering upstream physics code.

401 original input files are copied byte-for-byte. Testing flexure vs surface
overrides is labelled explicitly and is NOT an official 0–15 Myr reproduction.
"""
from pathlib import Path
import argparse, hashlib, json, re, shutil

CASES={
 "N121_FULL":{"grid":121,"overrides":"-qplotting_mode=0","purpose":"full physical model, 0–15 Myr, medium resolution"},
 "N401_ISO_OFF":{"grid":401,"overrides":"-tf0.5 -qisost_model=0 -qplotting_mode=0","purpose":"isolate 401 runtime without flexural solver, 0–0.5 Myr only"},
 "N401_SURFACE_OFF":{"grid":401,"overrides":"-tf0.5 -qhydro_model=0 -qerosed_model=0 -qplotting_mode=0","purpose":"isolate 401 runtime without surface processes, 0–0.5 Myr only"},
 "N401_BOTH_OFF":{"grid":401,"overrides":"-tf0.5 -qisost_model=0 -qhydro_model=0 -qerosed_model=0 -qplotting_mode=0","purpose":"input and time-loop sanity, neither flexure nor surface, 0–0.5 Myr only"}
}
ROOT=Path(__file__).resolve().parents[1]
SOURCES=("demo.PRM","demo1.UNIT","demo2.UNIT","demo.PRFL")
def main(name):
    spec=CASES[name];n=spec["grid"]
    src=ROOT/"upstream"/"tisc"/"demo"/"6_tectonics"
    out=ROOT/"diagnostic_03b"/name
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    for f in SOURCES: shutil.copy2(src/f,out/f)
    if n!=401:
        f=out/"demo.PRM"
        s=f.read_text(encoding="latin-1")
        for key in ("Nx","Ny"):
            s,c=re.subn(r"(?m)^("+key+r"\s+)401(?=\s|$)",lambda m:m.group(1)+str(n),s)
            if c!=1: raise RuntimeError(f"Unexpected {key} count {c}")
        f.write_text(s,encoding="latin-1")
    audit={"case":name,"grid":n,"cell_size_km":500/(n-1),"run_override_flags":spec["overrides"],
           "purpose":spec["purpose"],"is_exact_author_full_history":False,
           "same_software_as_exp03":True,"official_commit":"d18b7d270f4d671b80223e10dede329ad35cafdd",
           "source_hashes":{f:hashlib.sha256((src/f).read_bytes()).hexdigest() for f in SOURCES},
           "run_hashes":{f:hashlib.sha256((out/f).read_bytes()).hexdigest() for f in SOURCES}}
    if n==401 and any(audit["source_hashes"][f]!=audit["run_hashes"][f] for f in SOURCES):
        raise AssertionError("401 inputs not byte-identical with author.")
    if n==121 and any((out/f).read_bytes()!=(src/f).read_bytes() for f in SOURCES if f!="demo.PRM"):
        raise AssertionError("Fault geometry altered.")
    (out/"INPUT_AUDIT.json").write_text(json.dumps(audit,indent=2))
    print(json.dumps(audit,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("case",choices=list(CASES))
    main(p.parse_args().case)
