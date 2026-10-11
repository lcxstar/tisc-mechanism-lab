#!/usr/bin/env python3
"""03x read-only from archived, paired official TISC benchmark results.
Requires qc/{81,121,201,401,t2p5,t3}/experiment/{reference,optimized}/demo.{xyw,hrz}.
No numerical-physics changes. Basal .hrz elevation != isolated flexure w.
"""
import csv,json,hashlib
from pathlib import Path
import numpy as np
from scipy.interpolate import RegularGridInterpolator
BASE=Path("qc")
OUT=Path("results_03x")
def run(n, variant="reference"):
    root=BASE/str(n)/"experiment"/variant
    with (root/"demo.hrz").open() as f:
        f.readline(); hdr=f.readline()
        dens=[float(v) for v in hdr.split("Dens:")[1].split("water")[0].split()]
        raw=np.loadtxt(f)
    N=int(np.sqrt(len(raw)))
    assert N*N==len(raw) and raw.shape[1]==len(dens)+2
    h=raw[:,2:]
    sediment=np.diff(h,axis=1)[:,np.isclose(dens[1:],2200)]
    thickness=np.maximum(0,sediment).sum(axis=1)
    xy=raw[:,:2]
    xx=np.unique(xy[:,0]); yy=np.unique(xy[:,1])
    assert len(xx)==N and len(yy)==N
    assert np.allclose(xy[:,1].reshape(N,N)[:,0],yy[::-1])
    xyz=[]
    with (root/"demo.xyw").open() as f:
        for line in f:
            if not line.startswith("#") and line.strip():xyz.append(line.split())
    assert len(xyz)==len(xy)
    assert np.allclose([[float(a[0]),float(a[1])] for a in xyz],xy,atol=0.002)
    def grid(t): return np.asarray(t).reshape(N,N)[::-1,:].copy()
    return dict(n=N,x=xx,y=yy,topo=grid([float(a[5]) for a in xyz]),
                sed=grid(thickness),basal=grid(h[:,0]),
                types=grid([a[4] for a in xyz]),
                downstream=np.stack([grid([float(a[k]) for a in xyz]) for k in (6,7)],axis=2))
def volume(d):return float(np.trapezoid(np.trapezoid(d["sed"],d["x"],axis=1),d["y"],axis=0)/1000.)
def metrics(data,truth):
    n=data["n"]; xy=np.array([(y,x) for y in data["y"] for x in data["x"]])
    row=dict(n=n,dx_km=float(np.diff(data["x"]).mean()),volume_compacted_km3=volume(data),
             volume_percent_different_from_401=float(100*(volume(data)/volume(truth)-1)),
             mean_sed_m=float(data["sed"].mean()),max_sed_m=float(data["sed"].max()))
    for key in ["topo","sed","basal"]:
        z=RegularGridInterpolator((truth["y"],truth["x"]),truth[key])(xy).reshape(n,n)
        delta=data[key]-z
        row[key+"_RMS_vs401_m"]=float(np.sqrt(np.mean(delta*delta)))
        row[key+"_max_abs_vs401_m"]=float(np.max(np.abs(delta)))
    return row
def changed_links(a,b):
    assert a["n"]==b["n"]
    c=np.any(np.abs(a["downstream"]-b["downstream"])>.001,axis=2)
    t=a["types"]!=b["types"]
    where=np.argwhere(c|t); results=[]
    for i,j in where:
        # Scanning 8 neighbours in exported elevations; ONLY 0.1m-quantized gradients.
        grads=[]
        for z in [a["topo"],b["topo"]]:
            g=[]
            for di in [-1,0,1]:
                for dj in [-1,0,1]:
                    if not (di or dj):continue
                    ii=i+di; jj=j+dj
                    if 0<=ii<a["n"] and 0<=jj<a["n"]:
                        g.append(float((z[i,j]-z[ii,jj])/(np.hypot(di,dj)*(a["x"][1]-a["x"][0]))))
            g.sort(reverse=True); grads.append(g)
        results.append(dict(x_km=float(a["x"][j]),y_km=float(a["y"][i]),
            topo32_m=float(a["topo"][i,j]),topo64_m=float(b["topo"][i,j]),
            changed_link=bool(c[i,j]),changed_type=bool(t[i,j]),
            type32=str(a["types"][i,j]),type64=str(b["types"][i,j]),
            x_to32_km=float(a["downstream"][i,j,0]),y_to32_km=float(a["downstream"][i,j,1]),
            x_to64_km=float(b["downstream"][i,j,0]),y_to64_km=float(b["downstream"][i,j,1]),
            best_descent_printed32_m_per_km=grads[0][0],
            top_two_slope_margin_printed32_m_per_km=grads[0][0]-grads[0][1],
            boundary_1cell=bool(i<2 or j<2 or i>=a["n"]-2 or j>=a["n"]-2)))
    return results
def writecsv(path,rows):
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    grids={n:run(n) for n in (81,121,201,401)}
    out=[metrics(grids[n],grids[401]) for n in sorted(grids)]
    writecsv(OUT/"03X_SAME_SCHEME_GRID_COMPARISON.csv",out)
    c3=changed_links(run("t3"),run("t3","optimized"))
    c25=changed_links(run("t2p5"),run("t2p5","optimized"))
    if c3:writecsv(OUT/"03X_FIRST_OUTLET_AND_RIVER_ROUTE_CHANGES.csv",c3)
    payload=dict(source="03v paired scientific artifacts from pinned original TISC 6_tectonics",
      same_scheme=True,dt_Myr=.5,dt_eros_Myr=.05,time_Myr=15,
      grid=out,t3=dict(changed_nodes=len(c3),changed_edges=sum(d["changed_link"] for d in c3),
          changed_types=sum(d["changed_type"] for d in c3),
          same_printed_topo=sum(d["topo32_m"]==d["topo64_m"] for d in c3),
          top2_printed_slope_equal=sum(d["top_two_slope_margin_printed32_m_per_km"]==0 for d in c3)),
      t2p5=dict(changed_nodes=len(c25)),
      caveats=["401 grid is a comparison, not an exact solution",
        "Sediment is compaction-adjusted, classified by .hrz block density 2200kg/m3",
        "Basal horizon is an elevation, not isolated flexural displacement w",
        "0.1m printed height is insufficient to prove exact tie or no native float discrepancy",
        "First altered route is not necessarily the first causal perturbation."])
    (OUT/"03X_QC_AND_INTERPRETATION.json").write_text(json.dumps(payload,indent=2))
    print("03X_QC "+json.dumps(payload))
    assert len(c25)==0 and len(c3)>0 and np.isfinite([v["volume_compacted_km3"] for v in out]).all()
if __name__=="__main__":main()
