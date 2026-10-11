#!/usr/bin/env python3
"""Reproduce TISC's official direct flexure benchmark and isolate effects of Te."""
from __future__ import annotations
import csv, json, math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT=Path("results/02_Te_sensitivity")
TES=(5,20,40)
GRIDS=(51,101)
REFERENCE={11:675.1,51:711.0}

def load_grid(path,n):
    rows=[]
    for line in path.read_text(errors="replace").splitlines():
        parts=line.split()
        if len(parts)!=4: continue
        try: vals=[float(p) for p in parts]
        except ValueError: continue
        if all(math.isfinite(v) for v in vals): rows.append(vals)
    arr=np.asarray(rows,dtype=float)
    if arr.shape!=(n*n,4): raise ValueError(f"{path.name}: got {arr.shape}, expected {n*n}x4")
    xs,ys=np.unique(arr[:,0]),np.unique(arr[:,1])
    if len(xs)!=n or len(ys)!=n or not np.allclose([xs[0],xs[-1],ys[0],ys[-1]],[-250,250,-250,250],atol=.01):
        raise ValueError(f"{path.name}: wrong grid")
    img=arr.reshape(n,n,4)
    if not np.allclose(img[:,:,0],xs[None,:]) or not np.allclose(img[:,:,1],ys[::-1,None]):
        raise ValueError(f"{path.name}: wrong x/y ordering")
    return img

def center(img):
    n=len(img)
    if n%2!=1 or not np.allclose(img[n//2,n//2,:2],[0,0]): raise ValueError("No central x=y=0 node")
    return float(img[n//2,n//2,2])

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    reference=[]
    for n,w_ref in REFERENCE.items():
        img=load_grid(OUT/f"AUTHOR_DEFAULT_N{n:03d}.log",n)
        val=center(img)
        reference.append({"N":n,"author_center_m":w_ref,"measured_center_m":val,"error_m":val-w_ref,"pass":abs(val-w_ref)<1.0})
    cases={(t,n):load_grid(OUT/f"TE_{t:03d}km_N{n:03d}.log",n) for n in GRIDS for t in TES}
    same_load={}
    for n in GRIDS:
        p=cases[(5,n)][:,:,3]
        same_load[str(n)]=all(np.array_equal(p,cases[(t,n)][:,:,3]) for t in TES[1:])
        if not np.isclose(p.max(),2e7): raise ValueError(f"Unexpected pressure for N={n}: {p.max()}")

    data=[]
    for n in GRIDS:
        for t in TES:
            img=cases[(t,n)]
            w=img[:,:,2];step=500/(n-1)
            data.append({"Te_km":t,"N":n,"center_w_m":center(img),
              "max_w_m":float(w.max()),"min_w_m":float(w.min()),"mean_w_m":float(w.mean()),
              "integrated_w_m_km2":float(w.sum()*step*step),
              "middle_profile_width_above_half_max_km":float(np.count_nonzero(img[n//2,:,2]>=w.max()/2)*step)})
    with (OUT/"TE_SWEEP_NUMERICS.csv").open("w",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=list(data[0]))
        wr.writeheader();wr.writerows(data)
    with (OUT/"TE_SWEEP_PROFILE_X_51.csv").open("w",newline="") as f:
        wr=csv.writer(f);wr.writerow(["x_km","w_te5_m","w_te20_m","w_te40_m","load_Pa"])
        for j in range(51):
            wr.writerow([cases[(5,51)][25,j,0],
              *[cases[(t,51)][25,j,2] for t in TES],cases[(5,51)][25,j,3]])

    fig,axs=plt.subplots(1,2,figsize=(13.6,5.3),constrained_layout=True)
    for ax,n in zip(axs,GRIDS):
        for t in TES:
            img=cases[(t,n)]
            ax.plot(img[n//2,:,0],img[n//2,:,2],label=f"Te={t} km | center={center(img):.1f} m")
        ax.axhline(0,color="grey",lw=.7)
        ax.set(title=f"Identical original load, {n}x{n} nodes",xlabel="X at Y=0 (km)",ylabel="Downward deflection (m)")
        ax.grid(alpha=.25);ax.legend(fontsize=9)
    fig.suptitle("Official TISC elastic plate: single changed input = Te")
    fig.savefig(OUT/"FIG01_Te_profiles.png",dpi=175)
    fig.savefig(OUT/"FIG01_Te_profiles.svg")
    plt.close(fig)

    fig,axs=plt.subplots(1,3,figsize=(15.5,5),constrained_layout=True)
    lim=max(float(np.max(np.abs(cases[(t,51)][:,:,2]))) for t in TES)
    for ax,t in zip(axs,TES):
        im=ax.imshow(cases[(t,51)][:,:,2],origin="upper",extent=(-250,250,-250,250),
          vmin=-lim,vmax=lim,cmap="RdBu_r")
        ax.set(title=f"Te={t} km",xlabel="X (km)",ylabel="Y (km)")
    fig.colorbar(im,ax=list(axs),shrink=.75,label="w (m); positive = downward")
    fig.suptitle("Same model geometry and pressure field; N=51")
    fig.savefig(OUT/"FIG02_Te_maps.png",dpi=175)
    plt.close(fig)

    center51=[next(d["center_w_m"] for d in data if d["Te_km"]==t and d["N"]==51) for t in TES]
    report={"experiment":"02_TE_ONLY_SWEEP",
      "pinned_source":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd",
      "unchanged":["original demo pressure field","spatial domain","grid per comparison","TISC physics and solver","boundary settings"],
      "changed_only":"effective elastic thickness Te via -T in metres",
      "published_reference":reference,"same_pressure_at_each_N":same_load,
      "cases":data,"expect_center_w_decreases_as_Te_increases":center51[0]>center51[1]>center51[2],
      "numerical_pass":bool(all(r["pass"] for r in reference) and all(same_load.values())
        and len(data)==6 and len(set(center51))==3),
      "limits":"Static flexure; no thrust displacement, mountain building, erosion or sedimentation"}
    (OUT/"TE_SWEEP_QC.json").write_text(json.dumps(report,indent=2,allow_nan=False))
    print(json.dumps(report,indent=2,allow_nan=False))
    if not report["numerical_pass"]:raise SystemExit("FAILED reference or one-factor checks")
if __name__=="__main__":main()
