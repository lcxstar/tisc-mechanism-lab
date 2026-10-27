#!/usr/bin/env python3
"""Prepare author-provided Ebro model at native and node-coincident 2x refinement.

Author's model domain and all geological boundary/input files are preserved.
Only numeric Nx, Ny, dt and dt_eros lines in copied PRM are modified.
"""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "upstream" / "tisc" / "demo" / "8_Ebro_evol"
DEST = ROOT / "ebro_v1"
VALID_SUFFIXES = {".PRM", ".ZINI", ".EET", ".RAIN", ".WINI", ".UNIT",
                  ".REC", ".SLV", ".NDEF", ".INS", ".INT", ".PRFL",
                  ".RIV", ".CMP", ".VISC", ".TSBC", ".LOAD"}
PARAMS = {"original": (208, 110, "0.5", "0.05"),
          "time_only": (208, 110, "0.25", "0.025"),
          "space_only": (415, 219, "0.5", "0.05"),
          "refined": (415, 219, "0.25", "0.025")}
PRESERVE_DOMAIN = {"xmin": "-48160", "xmax": "660573", "ymin": "0",
                   "ymax": "500000", "Timeini": "-60", "Timefinal": "-0"}
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def replace_one(s, key, new):
    pattern = rf"(?m)^(\s*{re.escape(key)}\s+)([^\s#]+)"
    out, n = re.subn(pattern, lambda m: m.group(1) + str(new), s)
    if n != 1:
        raise ValueError(f"Expected exactly one {key} in Ebro_evol.PRM; got {n}")
    return out
def get_param(s, key):
    hits = re.findall(rf"(?m)^\s*{re.escape(key)}\s+([^\s#]+)", s)
    if len(hits) != 1:
        raise ValueError(f"Unexpected count of {key}: {hits}")
    return hits[0]
def run(case):
    if not SOURCE.is_dir():
        raise RuntimeError(f"Official author source directory is absent: {SOURCE}")
    if (DEST / case).exists():
        shutil.rmtree(DEST / case)
    target = DEST / case
    target.mkdir(parents=True)
    files = sorted(p for p in SOURCE.glob("Ebro_evol*")
                   if p.is_file() and (p.suffix in VALID_SUFFIXES
                                      or re.fullmatch(r"\.INT\d+", p.suffix)))
    if len(files) < 7 or not any(p.name=="Ebro_evol1.UNIT" for p in files):
        raise RuntimeError("Incomplete author Ebro input deck: expected PRM and UNIT files")
    for f in files:
        shutil.copy2(f, target / f.name)
    prm = target / "Ebro_evol.PRM"
    native = (SOURCE / "Ebro_evol.PRM").read_text(encoding="utf-8")
    for key, val in PRESERVE_DOMAIN.items():
        if get_param(native, key) != val:
            raise RuntimeError(f"Upstream author {key} changed unexpectedly")
    nx, ny, dt, dt_eros = PARAMS[case]
    customized = native
    for k, v in [("Nx", nx), ("Ny", ny), ("dt", dt), ("dt_eros", dt_eros)]:
        customized = replace_one(customized, k, v)
    prm.write_text(customized, encoding="utf-8")
    for k, v in PRESERVE_DOMAIN.items():
        assert get_param(customized, k) == v, (k, v)
    for p in files:
        if p.suffix != ".PRM" and digest(p) != digest(target/p.name):
            raise RuntimeError(f"Modified geology input {p.name}")
    for n in range(1, 6):
        if not (target/f"Ebro_evol{n}.UNIT").is_file():
            raise RuntimeError(f"Missing expected moving-tectonics Ebro_evol{n}.UNIT")
    xmin,xmax,ymin,ymax = -48160.,660573.,0.,500000.
    audit = {"case":case,"source":"TISC official demo/8_Ebro_evol",
             "repository_revision":"d18b7d270f4d671b80223e10dede329ad35cafdd",
             "grid":[nx,ny],"nodes":nx*ny,
             "domain_m":[xmin,xmax,ymin,ymax],
             "spacing_m":[(xmax-xmin)/(nx-1),(ymax-ymin)/(ny-1)],
             "dt_Myr":float(dt),"dt_eros_Myr":float(dt_eros),
             "author_inputs":{p.name:digest(p) for p in files},
             "copied_inputs":{p.name:digest(target/p.name) for p in files},
             "only_allowed_PRM_changes":["Nx","Ny","dt","dt_eros"],
             "model_age_range_Ma":[-60,0],
             "all_nonPRM_author_input_hashes_exact":True,
             "scientific_model_claim":"experimental numerical refinement, not geological validation"}
    (target/"INPUT_MANIFEST.json").write_text(json.dumps(audit,indent=2))
    print("EBRO_INPUT_PREPARED", json.dumps({k:audit[k] for k in
          ("case","grid","nodes","spacing_m","dt_Myr","dt_eros_Myr")}),flush=True)
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("case",choices=PARAMS)
    run(a.parse_args().case)
