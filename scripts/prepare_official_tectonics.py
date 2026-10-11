#!/usr/bin/env python3
"""Prepare unmodified 6_tectonics example plus strictly labelled mechanism variants.

The ORIGINAL_401 case copies author's inputs byte-for-byte. All other cases
use the same author's inputs, with explicitly audited small modifications.
Never import custom Junggar patches or loads into this laboratory.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re,shutil
from pathlib import Path

CASES={
 "original_401":{"grid":401,"change":"NONE — author's unchanged inputs"},
 "baseline_81":{"grid":81,"change":"grid Nx=Ny=81 only"},
 "ride0_81":{"grid":81,"change":"grid=81; second UNIT ride=0 instead of 1"},
 "slow2_81":{"grid":81,"change":"grid=81; second UNIT vel_x=5 instead of 10 km/Myr"},
 "no2_81":{"grid":81,"change":"grid=81; remove second UNIT entirely"}
}
REPO=Path(__file__).resolve().parents[1]
INPUT_NAMES=("demo.PRM","demo1.UNIT","demo2.UNIT","demo.PRFL")
UPSTREAM="d18b7d270f4d671b80223e10dede329ad35cafdd"

def replace_param(text,key,original,new):
    match=rf"(?m)^({re.escape(key)}\s+){re.escape(str(original))}(?=\s|$)"
    result,n=re.subn(match,lambda m:m.group(1)+str(new),text)
    if n!=1: raise ValueError(f"parameter {key} expected exactly once; got {n}")
    return result

def prepare(case):
    src=REPO/"upstream"/"tisc"/"demo"/"6_tectonics"
    folder=REPO/"work_03"/case
    if folder.exists():shutil.rmtree(folder)
    folder.mkdir(parents=True)
    for file in INPUT_NAMES:
        shutil.copy2(src/file,folder/file)

    changes={}
    if case!="original_401":
        f=folder/"demo.PRM"
        before=f.read_text(encoding="latin-1")
        after=replace_param(replace_param(before,"Nx",401,81),"Ny",401,81)
        f.write_text(after,encoding="latin-1")
        changes["demo.PRM"]="grid only: 401x401 -> 81x81"
        if case=="ride0_81":
            f=folder/"demo2.UNIT"
            f.write_text(replace_param(f.read_text(encoding="latin-1"),"ride",1,0),encoding="latin-1")
            changes["demo2.UNIT"]="ride 1 -> ride 0"
        elif case=="slow2_81":
            f=folder/"demo2.UNIT"
            f.write_text(replace_param(f.read_text(encoding="latin-1"),"vel_x",10,5),encoding="latin-1")
            changes["demo2.UNIT"]="second fault vel_x 10 -> 5 km/Myr"
        elif case=="no2_81":
            (folder/"demo2.UNIT").unlink()
            changes["demo2.UNIT"]="removed at 6 Myr; diagnostic exclusion (NOT single parameter)"
    audit={"case":case,"grid":CASES[case]["grid"],"nominal_time_Myr":[0,15],
      "official_path":"tisc/demo/6_tectonics","official_commit":UPSTREAM,
      "declared_change":CASES[case]["change"],"modified_files":changes,
      "original_source_hashes":{n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in INPUT_NAMES},
      "runtime_input_hashes":{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
          for p in folder.glob("demo*") if p.is_file()},
      "no_custom_physics_patch":True}
    # Hard source integrity gate for literal author case
    if case=="original_401":
        assert all((folder/n).read_bytes()==(src/n).read_bytes() for n in INPUT_NAMES)
    # Check PRM/UNIT content differences for controlled cases with exact known edits.
    if case=="baseline_81":
        assert (folder/"demo1.UNIT").read_bytes()==(src/"demo1.UNIT").read_bytes()
        assert (folder/"demo2.UNIT").read_bytes()==(src/"demo2.UNIT").read_bytes()
    for p in folder.iterdir():
        if p.name.endswith(".UNIT") and not p.read_text(encoding="latin-1").strip():raise ValueError("empty UNIT")
    (folder/"INPUT_AUDIT.json").write_text(json.dumps(audit,indent=2,ensure_ascii=False))
    with (folder/"INPUT_SHA256.txt").open("w") as f:
        for p in sorted(folder.glob("demo*")):
            if p.is_file(): f.write(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n")
    print(json.dumps(audit,indent=2))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("case",choices=CASES)
    a=ap.parse_args()
    prepare(a.case)
