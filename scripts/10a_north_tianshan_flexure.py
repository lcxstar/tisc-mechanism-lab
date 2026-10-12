#!/usr/bin/env python3
"""V10a: first-order Northern Tian Shan -> southern Junggar STATIC flexural response.

Run original author's pinned TISC -Q direct flexure. No tectonic forward modelling,
real-data georeferencing, erosional/transport or subsidence calibration is implied.
Pressure polygon uses the author's mode_interp=4 grammar.

CLI:
  python scripts/10a_north_tianshan_flexure.py prepare --root WORK
  python scripts/10a_north_tianshan_flexure.py analyze --root WORK
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
from collections import defaultdict

PIN="d18b7d270f4d671b80223e10dede329ad35cafdd"
RHO=2850.0
G=9.81
BASE_LOAD_H_M=1000.0
XMIN=-250000
XMAX=250000
YMIN=-250000
YMAX=350000
RECT_X=(-150000,150000)
RECT_Y=(-130000,-50000)  # mountain load south of the y=0 conceptual mountain front
CASES=[
  ("base_T25_shift0",25,0,1,101,121),
  ("T15_shift0",15,0,1,101,121),
  ("T40_shift0",40,0,1,101,121),
  ("T25_shift20km",25,20,1,101,121),
  ("T25_shift40km",25,40,1,101,121),
  ("T25_loadhalf",25,0,0.5,101,121),
  ("T25_load1p5",25,0,1.5,101,121),
  ("T25_noload",25,0,0,101,121),
  ("base_T25_coarse10km",25,0,1,51,61),
]
def sha(path):
  return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def prepare(root):
  root.mkdir(parents=True,exist_ok=True)
  spec=[]
  for name,te,shift,ratio,nx,ny in CASES:
    folder=root/name
    folder.mkdir(exist_ok=True)
    y0,y1=(v+shift*1000 for v in RECT_Y)
    pressure=RHO*G*BASE_LOAD_H_M*ratio
    polygon=f"{pressure:.6f}\n{RECT_X[0]} {y0}\n{RECT_X[0]} {y1}\n{RECT_X[1]} {y1}\n{RECT_X[1]} {y0}\n"
    (folder/"load.xyp").write_text(polygon)
    cmd=f'tisc -Qload.xyp -N{nx}/{ny} -D{XMIN}/{XMAX}/{YMIN}/{YMAX} -qmode_interp=4 -T{te*1000} -V1'
    (folder/"COMMAND.txt").write_text(cmd+"\n")
    spec.append(dict(case=name,Te_km=te,north_shift_km=shift,load_multiplier=ratio,
      nx=nx,ny=ny,model_y_front_km=0,load_y_min_km=y0/1000,
      load_y_max_km=y1/1000,load_pressure_Pa=pressure,
      is_physical_geolocation=False,load_sha256=sha(folder/"load.xyp"),command=cmd))
  (root/"PLAN.json").write_text(json.dumps(dict(upstream_commit=PIN,model_type="static_elastic_flexure_only",
    geomorphology=False,tectonic_timing=False,real_geographic_coordinates=False,
    south_is_negative_y=True,north_is_positive_y=True,Te_is_sensitivity_parameter_not_measured=True,
    load_density_kg_m3=RHO,load_thickness_m=BASE_LOAD_H_M,base_rectangle_m=dict(x=RECT_X,y=RECT_Y),
    geological_constraint_note="northward migration is a hypothesis; source forebulge rate does not directly fix load movement",
    cases=spec),indent=2))
  with (root/"RUN_MATRIX.tsv").open("w") as fp:
    wr=csv.writer(fp,delimiter="\t")
    wr.writerow(["case","command"])
    for z in spec:wr.writerow([z["case"],z["command"]])
  print("Prepared",len(spec),"static sensitivity cases")

def read_rows(path):
  arr=[]
  with gzip.open(path,"rt",errors="replace") if path.suffix==".gz" else path.open(errors="replace") as f:
    for line in f:
      t=line.split()
      if len(t)!=4:continue
      try:
        v=tuple(float(x) for x in t)
      except ValueError:
        continue
      if all(math.isfinite(z) for z in v):arr.append(v)
  return arr
def to_grid(rows,nx,ny):
  assert len(rows)==nx*ny,(len(rows),nx,ny)
  # Native -Q output: x[km] y[km] w[m] pressure[Pa].
  # Numerical x and y are printed to 0.1 km in original C code.
  coords={(round(x,3),round(y,3)):(w,p) for x,y,w,p in rows}
  assert len(coords)==len(rows),"duplicate coordinates"
  return coords
def approx(v1,v2,abs_tol=0.5,rel_tol=0.05):
  return abs(v1-v2)<=max(abs_tol,rel_tol*max(abs(v1),abs(v2)))
def analyze(root):
  spec=json.loads((root/"PLAN.json").read_text())
  cases={}
  summaries=[]
  transects=[]
  for z in spec["cases"]:
    d=root/z["case"]
    exitval=int((d/"EXIT_CODE.txt").read_text()) if (d/"EXIT_CODE.txt").exists() else None
    f=d/"RUN.log.gz"
    rows=read_rows(f) if f.exists() else []
    if len(rows)==z["nx"]*z["ny"] and exitval==0:
      grid=to_grid(rows,z["nx"],z["ny"])
      cases[z["case"]]=grid
      ny=[(y,w,p) for (x,y),(w,p) in grid.items() if abs(x)<0.001]
      ny.sort()
      basin=[w for y,w,p in ny if 0<=y<=150]
      load=[p for xyp,(w,p) in grid.items()]
      pos=[(y,w) for y,w,p in ny if 0<=y<=150]
      entry=dict(**{k:v for k,v in z.items() if k!="command"},
        exit_code=exitval,grid_nodes=len(rows),numeric_complete=True,
        centerline_y0_down_m=next((w for y,w,p in ny if abs(y)<.001),None),
        basin_y0_to150_max_down_m=max(basin) if basin else None,
        basin_y0_to150_min_down_m=min(basin) if basin else None,
        basin_y0_to150_max_down_location_km=max(pos,key=lambda r:r[1])[0] if pos else None,
        grid_min_down_m=min(w for w,p in grid.values()),
        grid_max_down_m=max(w for w,p in grid.values()),
        grid_max_pressure_Pa=max(load),
        applied_load_area_cells=sum(p>1e5 for p in load),
        model_load_integral_N=sum(load)*(XMAX-XMIN)/(z["nx"]-1)*(YMAX-YMIN)/(z["ny"]-1))
      for y,w,p in ny:
        transects.append(dict(case=z["case"],x_km=0,y_km=y,
          downward_flexure_m=w,pressure_Pa=p))
    else:
      entry=dict(case=z["case"],exit_code=exitval,grid_nodes=len(rows),
        numeric_complete=False,expected_nodes=z["nx"]*z["ny"])
    summaries.append(entry)
  all_ok=len(cases)==len(spec["cases"])
  b=cases.get("base_T25_shift0",{})
  ref={}
  for n,expected in [(11,675.1),(51,711.0)]:
    key=f"Q_ORIGINAL_N{n}.log.gz"
    f=root/key
    z=read_rows(f) if f.exists() else []
    center=[w for x,y,w,p in z if abs(x)<.001 and abs(y)<.001]
    ref[str(n)]={"expected_m":expected,"observed_m":abs(center[-1]) if center else None,
      "accepted":bool(center and abs(abs(center[-1])-expected)<.21),
      "expected_nodes":n*n,"actual_nodes":len(z)}
  no=cases.get("T25_noload",{})
  h=cases.get("T25_loadhalf",{})
  up=cases.get("T25_load1p5",{})
  shift=cases.get("T25_shift40km",{})
  coarse=cases.get("base_T25_coarse10km",{})
  ys=[y for x,y in b if x==0 and y>=0 and y<=150]
  max_basin=max((b[(0,y)][0] for y in ys),default=0)
  linear_half=max((abs(h[k][0]-0.5*v[0]) for k,v in b.items()),default=math.inf) if len(b)==len(h) else math.inf
  linear_more=max((abs(up[k][0]-1.5*v[0]) for k,v in b.items()),default=math.inf) if len(b)==len(up) else math.inf
  zero_resp=max((abs(w) for w,p in no.values()),default=math.inf)
  coarse_common=[(y,coarse[(0,y)][0],b[(0,y)][0]) for x,y in coarse
    if x==0 and (0,y) in b and -150<=y<=150]
  coarse_rms=(math.sqrt(sum((a-c)**2 for y,a,c in coarse_common)/len(coarse_common))
    if coarse_common else None)
  # Scientific validation deliberately separate from successful C execution.
  checks={
    "all_cases_numerically_complete":all_ok,
    "author_N11_reference":ref["11"]["accepted"],
    "author_N51_reference":ref["51"]["accepted"],
    "zero_load_zero_deflection_under_0p2m":zero_resp<0.2,
    "mountain_pressure_and_northern_basin_response":bool(b and max_basin>0.5 and max(p for w,p in b.values())>1e7),
    "linear_load_response_0p5_under_1m_residual":linear_half<=1.0,
    "linear_load_response_1p5_under_1m_residual":linear_more<=1.0,
    "shifted_load_changes_basin_response":bool(shift and len(shift)==len(b) and
       max(abs(b[k][0]-shift[k][0]) for k in b)>1.0),
    "coarse_refined_rms_recorded":coarse_rms is not None
  }
  out=dict(model="north_tianshan_south_junggar_static_first_order",
    upstream_source=PIN,geographic_location=False,
    numerical_execution_pass=all_ok,
    reference_reproduced=ref,science_checks=checks,
    first_order_mechanism_pass=all(checks.values()),
    diagnostics=dict(max_basin_down_m=max_basin,max_zero_deflection_m=zero_resp,
      max_residual_pressure_half_m=linear_half,max_residual_pressure_onehalf_m=linear_more,
      coarse5vs10km_center_transect_RMS_m=coarse_rms,
      caution="no true sediment transport, no underthrusting, no geological time and no real coordinate alignment"),
    cases=summaries)
  (root/"V10A_NUMERIC_QC.json").write_text(json.dumps(out,indent=2,allow_nan=False))
  with (root/"V10A_CASE_METRICS.csv").open("w",newline="") as f:
    keys=sorted(set().union(*(v.keys() for v in summaries)))
    writer=csv.DictWriter(f,fieldnames=keys)
    writer.writeheader();writer.writerows(summaries)
  with (root/"V10A_CENTERLINE_TRANSECTS.csv").open("w",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=["case","x_km","y_km","downward_flexure_m","pressure_Pa"])
    writer.writeheader();writer.writerows(transects)
  try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figs=[
      ("Effective elastic thickness (static load 1 km)",
       ["T15_shift0","base_T25_shift0","T40_shift0"]),
      ("Northward-shifted load footprint (Te 25 km)",
       ["base_T25_shift0","T25_shift20km","T25_shift40km"]),
      ("Load amplitude (Te 25 km)",
       ["T25_loadhalf","base_T25_shift0","T25_load1p5"]),
    ]
    fig,axes=plt.subplots(3,1,figsize=(9,10),sharex=True,constrained_layout=True)
    for ax,(title,names) in zip(axes,figs):
      for name in names:
        if name not in cases:continue
        xy=sorted((y,w) for (x,y),(w,p) in cases[name].items() if x==0)
        ax.plot([y for y,w in xy],[w for y,w in xy],label=name)
      ax.axvline(0,color="gray",linestyle="--",linewidth=.8)
      ax.set_title(title);ax.set_ylabel("Downward flexure, w (m)")
      ax.grid(alpha=.2);ax.legend(fontsize=8)
    axes[-1].set_xlabel("Local N-S coordinate y (km): north positive; y=0 mountain front")
    fig.suptitle("Northern Tian Shan / Southern Junggar — schematic static flexure")
    fig.savefig(root/"V10A_NORTH_SOUTH_TRANSECTS.pdf");plt.close(fig)
    if b:
      import numpy as np
      xcoords=sorted(set(x for x,y in b))
      ycoords=sorted(set(y for x,y in b))
      z=np.array([[b[(x,y)][0] for x in xcoords]for y in ycoords])
      fig,ax=plt.subplots(figsize=(8,5.6),constrained_layout=True)
      im=ax.imshow(z,origin="lower",extent=[min(xcoords),max(xcoords),min(ycoords),max(ycoords)],aspect="auto")
      ax.axhline(0,color="white",linestyle="--",linewidth=1)
      ax.set(xlabel="Schematic E-W coordinate (km)",ylabel="Schematic N-S coordinate (km)",
             title="Static Te=25km, 1km south-side mountain load: downward flexure")
      fig.colorbar(im,ax=ax,label="Downward flexure (m)")
      fig.savefig(root/"V10A_FLEXURE_MAP.pdf");plt.close(fig)
  except Exception as e:
    out["plot_generation_error"]=str(e)
    (root/"V10A_NUMERIC_QC.json").write_text(json.dumps(out,indent=2))
  status="PASS" if out["first_order_mechanism_pass"] else "NOT YET ACCEPTED"
  md=f"""# North Tian Shan → South Junggar static flexural mechanism gate — {status}

**Scope:** idealised pinned-author TISC -Q, NOT Junggar late-Cenozoic forward reconstruction.
**Provenance:** source {PIN}, only two NBSP compile whitespace normalisations.

The x/y axes are **model-local km**, with the north direction +y and nominal
mountain front y=0 km. Input parameters are **test hypotheses**, not measured
topography, true thrust kinematics, basin age or lithospheric strength.

## Numerical and mechanism gates
"""
  for name,val in checks.items():
    md+=f"- {'PASS' if val else 'FAIL'} {name}\n"
  md+=f"""
## Key numbers (not field-calibrated)
- Foreland maximum downward flexure in 0–150 km strip: **{max_basin:.1f} m**.
- Static half-pressure residual against linear half response: **{linear_half:.2f} m**.
- Static 1.5-pressure residual: **{linear_more:.2f} m**.
- Coarse-vs-refined center transect RMS: **{coarse_rms if coarse_rms is not None else 'not available'} m**.
- Grounded geological direction is from published N Tian Shan / southern Junggar structure only.
  The reported ~3.1 mm/yr 22–16 Ma forebulge migration is **not** assumed equal to load movement.
- No erosion, sediment, lakes, time integration, tectonic slip or thermal coupling is simulated.

## Preserved outputs
- V10A_CASE_METRICS.csv, V10A_CENTERLINE_TRANSECTS.csv
- V10A_NUMERIC_QC.json
- V10A_NORTH_SOUTH_TRANSECTS.pdf and V10A_FLEXURE_MAP.pdf when plotting succeeds
- per-case .xyp, exact CLI and gzip-compressed native -Q output.
"""
  (root/"V10A_ACCEPTANCE.md").write_text(md)
  print(json.dumps({"status":status,"checks":checks,"max_basin_m":max_basin,
    "grid_rms_m":coarse_rms},indent=2))
  if not out["first_order_mechanism_pass"]:raise SystemExit("V10A physics/benchmark gate NOT ACCEPTED: inspect saved QC")

if __name__=="__main__":
  p=argparse.ArgumentParser()
  p.add_argument("mode",choices=["prepare","analyze"])
  p.add_argument("--root",type=Path,default=Path("results/10_north_tianshan_pilot"))
  a=p.parse_args()
  (prepare if a.mode=="prepare" else analyze)(a.root)
