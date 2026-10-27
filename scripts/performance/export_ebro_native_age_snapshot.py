#!/usr/bin/env python3
"""Export *calculated*, age-specific Ebro native XYW arrays as compact scientific data.

Do not generate any intermediate geologic time by spatial interpolation.
The visual atlas renderer consumes only these accepted native snapshots.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import numpy as np

def file_hash(p):
    h=hashlib.sha256()
    with p.open("rb") as stream:
        for buf in iter(lambda:stream.read(1<<20),b""):
            h.update(buf)
    return h.hexdigest()

def run(inp, out, wanted):
    src=inp/"Ebro_evol.xyw"
    log=inp/"RUN.log"
    code=int((inp/"EXIT_CODE.txt").read_text())
    txt=log.read_text(errors="replace")
    years=[float(t) for t in re.findall(r"(?m)^\s*T=\s*([-+\d.]+)\s*My",txt)]
    if code!=0 or not years or abs(years[-1]-wanted)>1e-6:
        raise RuntimeError(f"Native age/exit failed: code={code}, ages={years[-5:]}, wanted={wanted}")
    gridmeta=json.loads((inp/"INPUT_MANIFEST.json").read_text())
    nx,ny=gridmeta["grid"]
    rows=[]
    with src.open(errors="replace") as fp:
        for line in fp:
            p=line.split()
            if not p or p[0].startswith("#"):continue
            if len(p)<6:raise RuntimeError(f"Malformed .xyw row: {p}")
            rows.append([float(p[i]) for i in (0,1,2,3,5)])
    v=np.asarray(rows,dtype=np.float64)
    if v.shape!=(nx*ny,5) or not np.isfinite(v).all():
        raise RuntimeError(f"Native grid must be finite and exactly Nx*Ny: {v.shape}")
    x=np.unique(v[:,0]);y=np.unique(v[:,1])
    if x.size!=nx or y.size!=ny:raise RuntimeError("XYW coordinate dimensions differ from PRM")
    ix=np.searchsorted(x,v[:,0]);iy=np.searchsorted(y,v[:,1])
    def grid(column):
        field=np.full((ny,nx),np.nan,np.float64)
        field[iy,ix]=v[:,column]
        if not np.isfinite(field).all():raise RuntimeError("Missing raster cells")
        return field.astype(np.float32)
    z=grid(4)
    out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/"native_snapshot.npz", x_km=x.astype(np.float32),
       y_km=y.astype(np.float32),elevation_m=z,
       water_m3s=grid(2),sediment_kgs=grid(3),age_Ma=np.float32(wanted))
    (out/"TISC_NATIVE_SOURCE_XYW_SHA256.txt").write_text(file_hash(src)+"  Ebro_evol.xyw\n")
    qc={"age_Ma":wanted,"source":"danigeos/tisc pinned d18b7d270, V08 salt fix, V3 patches",
      "x_y_georeferenced":False,
      "input_original_sha256":gridmeta["author_inputs"],
      "native_xyw_sha256":file_hash(src),"native_exit_code":code,
      "actual_last_age_Ma":years[-1],"all_native_rows_present":True,
      "grid":[nx,ny],"elevation_min_m":float(np.min(z)),
      "elevation_max_m":float(np.max(z)),"elevation_p50_m":float(np.percentile(z,50)),
      "elevation_p999_m":float(np.percentile(z,99.9)),
      "nodes_above_5000m":int(np.count_nonzero(z>5000)),
      "nodes_below_minus5000m":int(np.count_nonzero(z<-5000)),
      "native_data_file":"native_snapshot.npz","original_native_field_col":6,
      "sediment_mass_budget_verified":False,
      "geologically_calibrated":False}
    (out/"NATIVE_AGE_QC.json").write_text(json.dumps(qc,indent=2))
    (out/"NATIVE_RUN_LAST_LINES.txt").write_text("\n".join(txt.splitlines()[-100:])+"\n")
    print("NATIVE_AGE_SNAPSHOT_ACCEPTED",json.dumps({k:qc[k] for k in
      ("age_Ma","grid","native_exit_code","elevation_min_m","elevation_max_m",
       "nodes_above_5000m","elevation_p999_m")}),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("input",type=Path);p.add_argument("output",type=Path)
    p.add_argument("--age",type=float,required=True)
    a=p.parse_args();run(a.input,a.output,a.age)
