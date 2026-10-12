#!/usr/bin/env python3
"""Inspect real 401x401 at t3Myr original lake outlets, and run ONE-CELL
float32 ULP perturbations of the STRICT downhill selection in a frozen DEM.
No physical lake-filling re-integration is claimed by this replay.
"""
from pathlib import Path
import sys,json,csv,math
import numpy as np
root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
dx=1.25; dirs=[(-1,0),(0,1),(1,0),(0,-1),(-1,1),(1,1),(1,-1),(-1,-1)]
targets=[("lake_sill",(37.5,-246.25)),("outlet",(38.75,-247.5)),
 ("flat_river",(-148.75,-246.25)),("upland_river",(-145.,-185.))]
def read(tag):
 d={}
 with (root/"experiment"/tag/"demo.xyw").open() as f:
  for line in f:
   if line.startswith("#") or not line.strip():continue
   a=line.split();p=(round(float(a[0]),3),round(float(a[1]),3))
   d[p]=(np.float32(a[5]),a[4],(round(float(a[6]),3),round(float(a[7]),3)))
 assert len(d)==401**2
 return d
def lake_nodes(tag):
 s=(root/"experiment"/tag/"demo.lak").read_text(errors="replace")
 ls=[];current=None
 for line in s.splitlines():
  if line.startswith(">Lake "):
   current={"nodes":set(),"outlets":set(),"header":line};ls.append(current)
  elif current and line.strip() and not line.startswith("#"):
   a=line.split()
   if len(a)<3:continue
   try:p=(round(float(a[0]),3),round(float(a[1]),3))
   except ValueError:continue
   current["nodes"].add(p)
   if a[2]=="E":current["outlets"].add(p)
 lookup={p:i for i,l in enumerate(ls) for p in l["nodes"]}
 outsets=set().union(*(l["outlets"] for l in ls)) if ls else set()
 return ls,lookup,outsets
def descend(d,p,override={}):
 me=override.get(p,d[p][0]);win=None;low=np.float32(0);negative=zero=0;detail=[]
 for order,(di,dj) in enumerate(dirs):
  q=(round(p[0]+dj*dx,3),round(p[1]-di*dx,3))
  if q not in d:continue
  neighbor=override.get(q,d[q][0])
  dist=np.float32(1000*dx*(math.sqrt(2) if di and dj else 1))
  slope=np.float32(np.float32(neighbor-me)/dist)
  if slope<0:negative+=1
  if slope==0:zero+=1
  if slope<0 and slope<low:low=slope;win=q
  detail.append([order,q,float(slope)])
 ranked=sorted([v for v in detail if v[2]<0],key=lambda t:(t[2],t[0]))
 gap=ranked[1][2]-ranked[0][2] if len(ranked)>1 else None
 return {"winner":win,"negative":negative,"zero":zero,"gap":gap,"choices":detail}
def writecsv(name,rows):
 with (out/name).open("w",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
runs={x:read(x) for x in ("reference","optimized")}
lakes={x:lake_nodes(x) for x in runs}
inspected=[];neighborhood=[];perturbed=[]
for label,p in targets:
 for tag,d in runs.items():
  first=descend(d,p);zi,kind,native=d[p];ls,lut,ot=lakes[tag]
  inspected.append(dict(site=label,variant=tag,x_km=p[0],y_km=p[1],
   z_native_float32_m=float(zi),node_type=kind,native_downstream=str(native),
   original_steepest_neighbor=str(first["winner"]),strict_route_matches_native=first["winner"]==native,
   lake_component=lut.get(p),is_lake_outlet=p in ot,
   exact_zero_neighbors=first["zero"],slope_runnerup_margin_m_per_m=first["gap"]))
  for iy in range(-3,4):
   for ix in range(-3,4):
    q=(round(p[0]+ix*dx,3),round(p[1]+iy*dx,3))
    if q not in d:continue
    neighborhood.append(dict(site=label,variant=tag,x=q[0],y=q[1],
      offset_x_cells=ix,offset_y_cells=iy,z_native_float32_m=float(d[q][0]),
      node_type=d[q][1],outlet=p in ot,lake_component=lut.get(q)))
  candidates=[p]+[v[1] for v in first["choices"]]
  for cell in candidates:
   for ulps in (-2,-1,0,1,2):
    updated=np.float32(d[cell][0])
    for _ in range(abs(ulps)):
     updated=np.nextafter(updated,np.float32(np.inf if ulps>0 else -np.inf))
    change={} if ulps==0 else {cell:updated}
    new=descend(d,p,change)
    perturbed.append(dict(site=label,variant=tag,switch_node=str(p),
      modified_node=str(cell),ULPs=ulps,height_change_m=float(updated-d[cell][0]),
      baseline_strict_downhill=str(first["winner"]),new_strict_downhill=str(new["winner"]),
      changed_downhill=new["winner"]!=first["winner"],
      baseline_zero_neighbor_count=first["zero"],new_zero_neighbor_count=new["zero"],
      changed_zero_neighbor_count=new["zero"]!=first["zero"],
      is_full_lake_solver=False))
writecsv("03Z_NATIVE_401_OUTLET_SITES.csv",inspected)
writecsv("03Z_NATIVE_7X7_WINDOWS.csv",neighborhood)
writecsv("03Z_ULP_PERTURBATION_STRICT_DESCENT.csv",perturbed)
summary={"native_example":"03x 38183004799 t3Myr 401x401",
 "source_predicates":"author surf_proc.c Define_Drainage_Net float32 strict derivative<0, deriv==0, deriv<maxderneg",
 "lake_count_original":len(lakes["reference"][0]),
 "lake_count_local_double":len(lakes["optimized"][0]),
 "same_lake_component_sets":{tuple(sorted(v["nodes"])) for v in lakes["reference"][0]}==
                             {tuple(sorted(v["nodes"])) for v in lakes["optimized"][0]},
 "site_count":len(targets),"cases":len(perturbed),
 "changed_strict_downhill_from_ulp":sum(v["changed_downhill"] for v in perturbed),
 "changed_zero_neighbors_from_ulp":sum(v["changed_zero_neighbor_count"] for v in perturbed),
 "found_actual_sites":inspected,
 "limitations":["Frozen state only: does not re-integrate TISC or predict lake membership after perturbation",
                "Original TISC chooses/propagates lake outlets using more than steepest local slope",
                "Near-south-boundary reservoir geometry may depend on global border classification",
                "Two local numerical precision variants are not complete float32 vs float64 full solver"]}
(out/"03Z_NATIVE_OUTLET_FROZEN_QC.json").write_text(json.dumps(summary,indent=2))
print("03Z_NATIVE_OUTLET_QC "+json.dumps({k:v for k,v in summary.items() if k!="found_actual_sites"}))
assert len(perturbed)>0
