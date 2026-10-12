#!/usr/bin/env python3
"""Generate 41x41 two-saddle closed-basin toy DEM for ACTUAL pinned TISC solver.

Eight input cases; same PRM and one-cell ZINI differences only.  No tectonic
UNIT, no application of 03y global epsilon; no change in physical solver rules.
TISC uses mode_interp 6, row0 = maximum Y and x fastest.
"""
import csv,hashlib,json,math,re,sys
from pathlib import Path
import numpy as np
if len(sys.argv)!=3:raise SystemExit("build_03z_micro_lake.py SOURCE_AUTHOR_PRM OUT_DIR")
author=Path(sys.argv[1]);root=Path(sys.argv[2]);root.mkdir(parents=True,exist_ok=True)
base=author.read_text(encoding="latin1")
N=41;NX=NY=N;delta=1000.
x=np.arange(N,dtype=float);y=np.arange(N-1,-1,-1,dtype=float)
xx,yy=np.meshgrid(x,y)
radius=np.hypot(xx-20,yy-20)
# This is a pre-registered physically synthetic DEM, not a palaeogeographic model.
ring=18*np.exp(-.5*((radius-10)/2.)**2)
exterior=-.6*np.maximum(0,radius-10)
surface=100+ring+exterior
for sx in (10,30):
 surface-=9*np.exp(-.5*((xx-sx)**2+(yy-20)**2)/(.55**2))
surface=surface.astype(np.float32)
west=(20,10);east=(20,30)
original_right=float(surface[east]);original_left=float(surface[west])
assert original_right==original_left,(original_right,original_left)
arms={"TIE":("none",0),"E_DOWN_ULP1":("east",-1),"W_DOWN_ULP1":("west",-1),
      "E_UP_ULP1":("east",1),"W_UP_ULP1":("west",1),
      "E_DOWN_MM1":("east",-0.001),"W_DOWN_MM1":("west",-0.001),
      "E_DOWN_CM1":("east",-0.01),"W_DOWN_CM1":("west",-0.01)}
def substitute(s,k,v):
 pat=rf"(?m)^({re.escape(k)}[ \t]+)(\S+)"
 matches=list(re.finditer(pat,s))
 if len(matches)!=1:raise RuntimeError(f"Expected single PRM {k}, got {len(matches)}")
 return re.sub(pat,lambda m:m.group(1)+str(v),s,count=1)
settings={"xmin":0,"xmax":40000,"ymin":0,"ymax":40000,
 "Nx":N,"Ny":N,"zini":0,"random_topo":0,"Timeini":0,"Timefinal":0.1,
 "dt":0.05,"dt_eros":0.005,"dt_record":0.05,"verbose_level":1,
 "mode_interp":6,"plotting_mode":0,
 # do not silently presume '0000' is a closed hydrologic boundary
 "eros_bound_cond":"1111"}
prm=base
for k,v in settings.items():prm=substitute(prm,k,v)
rows=[]
for name,(which,gap) in arms.items():
 a=surface.copy()
 q=None
 if which!="none":
  q=west if which=="west" else east
  if isinstance(gap,int):
   val=a[q]
   for _ in range(abs(gap)):
    val=np.nextafter(val,np.float32(np.inf if gap>0 else -np.inf))
   a[q]=val
  else:a[q]=np.float32(a[q]+gap)
 case=root/name;case.mkdir(exist_ok=True)
 (case/"micro.PRM").write_text(prm,encoding="latin1")
 (case/"micro.ZINI").write_text(
  "# Experimental two-rim-saddle 41x41 basin, no faults, row0 north, x-fast\n"
  "mode_interp 6\nz_default 0\n" +
  "".join(f"{v:.9g}\n" for v in a.ravel(order="C")),encoding="ascii")
 # preflight all pair inputs have byte-identical PRM, 41^2 roundtrip ZINI cells
 numeric=[float(t) for t in (case/"micro.ZINI").read_text().splitlines()[3:]]
 if len(numeric)!=N*N or not np.array_equal(np.array(numeric,dtype=np.float32),a.ravel()):
  raise RuntimeError("float32 ZINI roundtrip failure "+name)
 rows.append(dict(name=name,perturbed_sill=which,target_gap=gap,
  base_sill_m=original_left,east_sill_m=float(a[east]),west_sill_m=float(a[west]),
  actual_east_minus_west_m=float(a[east]-a[west]),
  PRM_sha256=hashlib.sha256((case/"micro.PRM").read_bytes()).hexdigest(),
  ZINI_sha256=hashlib.sha256((case/"micro.ZINI").read_bytes()).hexdigest(),
  no_fault_UNIT_files=True))
with (root/"INPUT_TABLE.csv").open("w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(root/"INPUT_SPEC.json").write_text(json.dumps({
"test":"03z native original TISC executable on paired tiny dual-sill lake toy",
"grid":(N,N),"dx_m":1000,
"ZINI_site_W":west,"ZINI_site_E":east,"basin_floor_center_m":float(surface[20,20]),
"geometry":"low centre, radial surrounding topographic barrier at r≈10km, two equal incised notches on E and W; outer slopes lower",
"all_physical_settings_fixed":True,"one_changed_initial_height_per_case":True,
"author_physics_baseline_pre_03y":True,"no_tectonic_UNITs":True,
"numerical_intervention":"input height perturbation ONLY, not route code threshold",
"experiments":rows},indent=2))
print("03Z_TINY_INPUT "+json.dumps({"grid":N,"arms":len(rows),"west_m":original_left,"east_m":original_right}))
