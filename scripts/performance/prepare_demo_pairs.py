#!/usr/bin/env python3
"""Prepare paired, byte-identical inputs for official TISC benchmark cases.

The two executables differ ONLY by the documented 03g source patch.
All cases are author's demo/6_tectonics. For smaller grids only Nx/Ny
changes; no Junggar inputs or diagnostic alteration of physics constants.
"""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"upstream"/"tisc"/"demo"/"6_tectonics"
FILES=("demo.PRM","demo1.UNIT","demo2.UNIT","demo.PRFL")
CASES={"N81":81,"N121":121,"N401":401}
MODES={
 "first_step":"-tf0.5 -qisost_model=0 -qplotting_mode=0",
 "full_coupled":"-qplotting_mode=0",
}
def prepare(case,mode):
    n=CASES[case]
    folder=ROOT/"validation_03g"/case/mode
    if folder.exists(): shutil.rmtree(folder)
    folder.mkdir(parents=True)
    reference=folder/"reference"
    optimized=folder/"optimized"
    reference.mkdir()
    optimized.mkdir()
    for run in (reference,optimized):
        for f in FILES: shutil.copy2(SRC/f,run/f)
        if n != 401:
            prm=run/"demo.PRM"
            txt=prm.read_text(encoding="latin-1")
            for key in ("Nx","Ny"):
                txt,c=re.subn(rf"(?m)^({key}\s+)401(?=\s|$)",
                              lambda x:x.group(1)+str(n),txt)
                if c!=1: raise ValueError(f"Missing exact {key}=401")
            prm.write_text(txt,encoding="latin-1")
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    expected={f:digest(SRC/f) for f in FILES}
    left={f:digest(reference/f) for f in FILES}
    right={f:digest(optimized/f) for f in FILES}
    if left != right: raise RuntimeError("DIFFERENT REFERENCE / OPTIMIZED INPUTS")
    if n==401 and left != expected:
        raise RuntimeError("401-grid original source inputs not SHA-exact")
    for f in FILES:
        if f!="demo.PRM" and left[f]!=expected[f]:
            raise RuntimeError("Geological/tectonic input changed unexpectedly")
    audit={
      "case":case,"mode":mode,"Nx":n,"Ny":n,
      "author_upstream_commit":"d18b7d270f4d671b80223e10dede329ad35cafdd",
      "prm_grid_only_changed_from_author":n!=401,
      "te_and_physical_properties_unchanged":True,
      "tectonic_UNITS_byte_exact":True,
      "run_flags":MODES[mode],
      "source_sha256":expected,"reference_sha256":left,
      "optimized_sha256":right,
      "reference_optimized_same_inputs":True,
      "literal_full_401_author_reproduction":False,
    }
    (folder/"INPUT_AUDIT.json").write_text(json.dumps(audit,indent=2))
    print(json.dumps(audit,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("case",choices=CASES)
    p.add_argument("mode",choices=MODES)
    args=p.parse_args()
    prepare(args.case,args.mode)
