#!/usr/bin/env python3
"""Audit and plot native Ebro model output with correct TISC .xyw columns.

Coordinates are AUTHOR LOCAL MODEL X/Y, not EPSG longitude/latitude.
Column 3=water [m3/s], 4=sediment [kg/s], 5=type, 6=terrain [m].
"""
import argparse
import json
import math
import re
from pathlib import Path
import numpy as np

def data(path,nx,ny):
    x=[]; y=[]; h=[]; w=[]; sediment=[]; typ=[]
    with path.open(errors="replace") as f:
        for line in f:
            ln=line.strip()
            if not ln or ln.startswith("#"):
                continue
            p=ln.split()
            if len(p)<7:
                raise RuntimeError(f"Unexpected native .xyw record: {p[:8]}")
            xi,yi,qi,si,hi=map(float,(p[0],p[1],p[2],p[3],p[5]))
            x.append(xi);y.append(yi);w.append(qi);sediment.append(si);h.append(hi)
            typ.append(p[4])
    N=nx*ny
    if len(h)!=N: raise RuntimeError(f"native .xyw grid incomplete: {len(h)} vs {N}")
    arr=np.array([x,y,h,w,sediment],dtype=float)
    if not np.isfinite(arr).all(): raise RuntimeError("Nonfinite terrain/water/sediment outputs")
    ux=np.unique(np.asarray(x)); uy=np.unique(np.asarray(y))
    if len(ux)!=nx or len(uy)!=ny:
        raise RuntimeError(f"Unexpected x/y grid dimensions {len(ux)} x {len(uy)} expected {nx} x {ny}")
    # Reorder by coordinates rather than assuming writer's traversal.
    xi=np.searchsorted(ux,x); yi=np.searchsorted(uy,y)
    grid=np.full((ny,nx),np.nan)
    grid[yi,xi]=h
    if not np.isfinite(grid).all(): raise RuntimeError("Grid map has holes")
    return ux,uy,grid,arr,typ

def main(root):
    manifest=json.loads((root/"INPUT_MANIFEST.json").read_text())
    nx,ny=manifest["grid"]
    log=(root/"RUN.log").read_text(errors="replace")
    code=int((root/"EXIT_CODE.txt").read_text())
    ages=[float(a) for a in re.findall(r"(?m)^\s*T=\s*([-+]?[0-9.]+)\s*My",log)]
    status={"case":manifest["case"],"exit_code":code,"ages_printed_Ma":ages,
            "age_min_Ma":min(ages) if ages else None,
            "age_max_Ma":max(ages) if ages else None,
            "source":"original Ebro input geometry with V08 salt-fix and V3 performance patches",
            "is_true_geological_reconstruction":False,
            "author_original_inputs_preserved_except":["Nx","Ny","dt","dt_eros"],
            "tectonic_units_hash_preserved":True}
    if code!=0 or not ages:
        status["native_success"]=False
        (root/"NATIVE_QC.json").write_text(json.dumps(status,indent=2))
        print("EBRO_NATIVE_FAIL",json.dumps(status)); raise SystemExit(1)
    file=root/"Ebro_evol.xyw"
    if not file.is_file() or file.stat().st_size==0:
        status["native_success"]=False
        (root/"NATIVE_QC.json").write_text(json.dumps(status,indent=2))
        raise RuntimeError("Missing native xyw")
    x,y,h,values,typ=data(file,nx,ny)
    status.update({"native_success":True,"n_xyw_rows":nx*ny,
                   "terrain_min_m":float(np.min(h)),
                   "terrain_max_m":float(np.max(h)),
                   "terrain_mean_m":float(np.mean(h)),
                   "terrain_integral_m3":float(np.mean(h)*(manifest["domain_m"][1]-manifest["domain_m"][0])*(manifest["domain_m"][3]-manifest["domain_m"][2])),
                   "max_discharge_m3s":float(values[3].max()),
                   "max_sediment_flux_kgs":float(values[4].max()),
                   "river_types":{k:typ.count(k) for k in sorted(set(typ))},
                   "xyw_terrain_is_column_6":True,
                   "mass_conservation_validated":False})
    (root/"NATIVE_QC.json").write_text(json.dumps(status,indent=2))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    X,Y=np.meshgrid(x,y)
    fig,ax=plt.subplots(figsize=(10,7))
    vmin=min(-500,float(h.min()));vmax=max(2500,float(h.max()))
    im=ax.pcolormesh(X,Y,h,cmap="terrain",shading="auto",vmin=vmin,vmax=vmax,rasterized=True)
    cb=fig.colorbar(im,ax=ax,shrink=.84)
    cb.set_label("Simulated surface elevation (m)")
    ax.set_xlabel("TISC local x (native model km)")
    ax.set_ylabel("TISC local y (native model km)")
    ax.set_aspect("equal",adjustable="box")
    ax.set_title(f"Ebro Basin model: {manifest['case']} {nx}×{ny} | last age {ages[-1]:g} Ma")
    fig.text(.5,.015,"Actual native TISC output | not georeferenced; not independent geological validation",
             ha="center",fontsize=9)
    fig.tight_layout(rect=[0,.045,1,1])
    fig.savefig(root/"EBRO_NATIVE_TOPOGRAPHY.png",dpi=150)
    fig.savefig(root/"EBRO_NATIVE_TOPOGRAPHY.pdf")
    plt.close(fig)
    print("EBRO_NATIVE_ACCEPTED",json.dumps({k:status[k] for k in
        ("case","exit_code","age_max_Ma","n_xyw_rows","terrain_min_m","terrain_max_m",
         "terrain_mean_m","max_discharge_m3s")}),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("run_dir",type=Path)
    main(p.parse_args().run_dir)
