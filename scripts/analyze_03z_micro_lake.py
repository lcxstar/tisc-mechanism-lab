#!/usr/bin/env python3
"""Compute actual evolved TISC dual-sill lake memberships, spillways and sediment."""
import csv,json,re,hashlib,sys,math
from pathlib import Path
import numpy as np
root=Path(sys.argv[1]);out=root/"03Z_RESULTS";out.mkdir(exist_ok=True)
spec=json.loads((root/"INPUT_SPEC.json").read_text());arms=spec["experiments"]
N=41
def read(p):
 d={}
 with p.open(errors="replace") as f:
  for line in f:
   if line.startswith("#") or not line.strip():continue
   a=line.split();d[(round(float(a[0]),3),round(float(a[1]),3))]=(
     np.float32(a[5]),a[4],(round(float(a[6]),3),round(float(a[7]),3)))
 assert len(d)==N*N
 return d
def lakes(p):
 ls=[];cur=None
 for s in p.read_text(errors="replace").splitlines():
  if s.startswith(">Lake "):
   cur=dict(nodes=set(),outlets=set());ls.append(cur)
  elif cur and s.strip() and not s.startswith("#"):
   a=s.split()
   if len(a)>2:
    try:key=(round(float(a[0]),3),round(float(a[1]),3))
    except ValueError:continue
    cur["nodes"].add(key)
    if a[2]=="E":cur["outlets"].add(key)
 return ls
def field(case):
 d=root/case
 if int((d/"EXIT_CODE.txt").read_text())!=0:raise RuntimeError(case+" failed TISC")
 log=(d/"RUN.log").read_text(errors="replace")
 end=[float(x) for x in re.findall(r"(?m)^\s*T=\s*(\d+(?:\.\d+)?)\s*My",log)]
 if not end or abs(end[-1]-.1)>1e-5:raise RuntimeError(case+" incomplete t=.1")
 sedmass=[abs(float(x)) for x in re.findall(
  r"TISC_03T_CORRECTED_BALANCE[^\n]*balance_pct=([^\s]+)",log)]
 if not sedmass or max(sedmass)>=.001:raise RuntimeError(case+" corrected sediment mass budget failed")
 v=read(d/"micro.xyw");l=lakes(d/"micro.lak")
 xy=np.loadtxt(d/"micro.xyzt",comments="#");hz=np.loadtxt(d/"micro.hrz",skiprows=2)
 if xy.shape!=(N*N,5) or hz.shape[0]!=N*N:raise RuntimeError("Physical field shape")
 dlist=[v[k] for k in sorted(v,key=lambda p:(-p[1],p[0]))]
 top=np.array([p[0] for p in dlist],float)
 link=np.array([p[2] for p in dlist],float)
 typ=np.array([p[1] for p in dlist])
 # 1km spacing, 41x41. Stratigraphy densities can be traced from .hrz header.
 with (d/"micro.hrz").open() as f:f.readline();hdr=f.readline()
 dens=[float(a) for a in hdr.split("Dens:")[1].split("water")[0].split()]
 h=hz[:,2:]
 if h.shape[1]!=len(dens):raise RuntimeError("Sediment horizon type mismatch")
 sm=np.diff(h,axis=1)
 sm=np.maximum(0,sm[:,np.isclose(dens[1:],2200)]).sum(axis=1)
 wx=np.ones(N);wx[0]=wx[-1]=.5
 trap=(wx[None,:]*wx[:,None]).ravel()
 vol=float((sm*trap).sum()/1000)
 main_lake=max(l,key=lambda q:len(q["nodes"])) if l else dict(nodes=set(),outlets=set())
 main_outlets=sorted(main_lake["outlets"])
 membership={pt:i for i,L in enumerate(l) for pt in L["nodes"]}
 outs=set().union(*(L["outlets"] for L in l)) if l else set()
 center=(20.,20.);west=(10.,20.);east=(30.,20.)
 sel={side:dict(z_m=float(v[pt][0]),type=v[pt][1],to=v[pt][2],
    lake_component=membership.get(pt),is_lake_outlet=pt in outs)
      for side,pt in (("centre",center),("west_sill",west),("east_sill",east))}
 return dict(topo=top,sed=sm,w=xy[:,2],ty=typ,link=link,
  lake_member_set=set(membership),lake_outlet_set=outs,
  lake_components={frozenset(L["nodes"]) for L in l},vol_km3=vol,
  net_sed_max_m=float(sm.max()),w_absmax_m=float(np.max(np.abs(xy[:,2]))),
  max_budget_pct=max(sedmass),n_lakes=len(l),n_outlet_nodes=len(outs),main_lake_nodes=len(main_lake["nodes"]),main_lake_outlets=main_outlets,sills=sel)
def diff(a,b):
 return dict(topography_RMS_m=float(np.sqrt(np.mean((b["topo"]-a["topo"])**2))),
  topography_max_abs_m=float(np.max(np.abs(b["topo"]-a["topo"]))),
  sediment_thickness_RMS_m=float(np.sqrt(np.mean((b["sed"]-a["sed"])**2))),
  sediment_thickness_max_abs_m=float(np.max(np.abs(b["sed"]-a["sed"]))),
  flexure_w_RMS_m=float(np.sqrt(np.mean((b["w"]-a["w"])**2))),
  changed_downstream_count=int(np.any(np.abs(b["link"]-a["link"])>.001,axis=1).sum()),
  changed_node_type_count=int(np.sum(b["ty"]!=a["ty"])),
  changed_lake_member_nodes=len(b["lake_member_set"]^a["lake_member_set"]),
  changed_lake_outlet_nodes=len(b["lake_outlet_set"]^a["lake_outlet_set"]),
  same_lake_component_node_sets=b["lake_components"]==a["lake_components"],
  compacted_sediment_volume_delta_km3=b["vol_km3"]-a["vol_km3"],
  compacted_sediment_volume_delta_pct=100*(b["vol_km3"]-a["vol_km3"])/a["vol_km3"] if a["vol_km3"] else None)
def writecsv(name,rows):
 with (out/name).open("w",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
data={a["name"]:field(a["name"]) for a in arms};base=data["TIE"]
rows=[]
for setting in arms:
 k=setting["name"];z=data[k];p=diff(base,z)
 rows.append(dict(case=k,sill_gap_input_m=setting["actual_east_minus_west_m"],
   west_type=z["sills"]["west_sill"]["type"],east_type=z["sills"]["east_sill"]["type"],
   west_outlet=z["sills"]["west_sill"]["is_lake_outlet"],
   east_outlet=z["sills"]["east_sill"]["is_lake_outlet"],
   native_lake_components=z["n_lakes"],outlet_nodes=z["n_outlet_nodes"],
   largest_lake_node_count=z["main_lake_nodes"],largest_lake_outlet_locations=str(z["main_lake_outlets"]),
   compacted_sediment_volume_km3=z["vol_km3"],
   maximum_sediment_thickness_m=z["net_sed_max_m"],
   maximum_w_deflection_m=z["w_absmax_m"],max_mass_error_percent=z["max_budget_pct"],**p))
writecsv("03Z_MICRO_LAKE_FULL_TISC_COMPARISON.csv",rows)
s={"experiment":"03z actual original 41x41 TISC dual-sill toy full forward runs",
   "all_completed_physics":True,"baseline_input_exact_across_arms":
    len(set(a["PRM_sha256"] for a in arms))==1,
   "n_arms":len(rows),"all_mass_event_budgets_pass":all(z["max_budget_pct"]<.001 for z in data.values()),
   "cases":rows,"sill_state":{k:z["sills"] for k,z in data.items()},
   "largest_lake_outlets":{k:z["main_lake_outlets"] for k,z in data.items()},
   "important_limits":["No claim of causal representation of first 401 3Myr lake bifurcation",
   "Small toy landscape is a physical TISC simulation with input perturbation only",
   "Final 0.1Myr snapshot can miss earlier spill timing; changed lake identities must be compared by membership sets, not numeric lake ID",
   "Sediment volume is compacted horizon proxy, not gross erosion and sediment budget"]}
(out/"03Z_MICRO_LAKE_FULL_TISC_QC.json").write_text(json.dumps(s,indent=2))
print("03Z_MICRO_FULL_TISC_QC "+json.dumps(
 {"all_completed":True,"arms":len(rows),
  "effects":[{k:r[k] for k in ("case","changed_downstream_count","changed_lake_outlet_nodes","sediment_thickness_RMS_m","compacted_sediment_volume_delta_km3")} for r in rows]}))
assert s["baseline_input_exact_across_arms"] and s["all_mass_event_budgets_pass"]
