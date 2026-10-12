#!/usr/bin/env python3
"""Follow-up micro lake saddle thresholds, ONLY one 41x41 ZINI cell changes.

Compare lake *throat* cells (11,20) and (29,20), immediately inside two
notches, as inferred from accepted 03z real TISC TIE model: true main-lake
outlet after t0.1 is (29,20), NOT the original notch (30,20). Each case
independently restarts TISC from unchanged t=0 conditions.
"""
from pathlib import Path
import hashlib,json,csv,sys,shutil
import numpy as np
if len(sys.argv)!=2:raise SystemExit("build_03z_threshold_sweep.py 41GRID_ROOT")
root=Path(sys.argv[1]);orig=root/"TIE";base=np.array(
 [float(v) for v in (orig/"micro.ZINI").read_text().splitlines()[3:]],
 dtype=np.float32).reshape(41,41)
assert len(base.ravel())==1681
assert base[20,11]==base[20,29],(base[20,11],base[20,29])
# Steps from numerical tiny to changes of >1 m at the real outlet-entry sills.
scan=[0.00001,0.001,0.01,0.1,0.25,0.5,0.75,1,1.25,1.5,2,3,4]
cases=[("TIE","none",0.0)]
cases.extend([(f"WIN_{str(x).replace('.','p')}_DOWN","west",-x) for x in scan])
cases.extend([(f"EIN_{str(x).replace('.','p')}_UP","east",x) for x in (0.1,0.5,1,1.5,2,3)])
results=[]
base_prm=(orig/"micro.PRM").read_bytes()
for name,branch,difference in cases:
 if name=="TIE":a=base.copy();d=orig
 else:
  a=base.copy();where=(20,11) if branch=="west" else (20,29)
  a[where]=np.float32(a[where]+difference)
  d=root/name;d.mkdir(exist_ok=True)
  (d/"micro.PRM").write_bytes(base_prm)
  (d/"micro.ZINI").write_text(
    (orig/"micro.ZINI").read_text().splitlines()[0]+"\nmode_interp 6\nz_default 0\n"+
    "".join(f"{z:.9g}\n" for z in a.ravel()),encoding="ascii")
  reread=np.array([float(x) for x in (d/"micro.ZINI").read_text().splitlines()[3:]],dtype=np.float32)
  if not np.array_equal(reread,a.ravel()):raise RuntimeError("ZINI roundtrip mismatch")
 real=(float(a[20,11]-base[20,11]),float(a[20,29]-base[20,29]))
 results.append(dict(name=name,branch=branch,initial_single_cell_delta_input_m=difference,
   west_throat_initial_delta_m=real[0],east_throat_initial_delta_m=real[1],
   original_equal_throat_height_m=float(base[20,11]),
   PRM_sha256=hashlib.sha256((d/"micro.PRM").read_bytes()).hexdigest(),
   ZINI_sha256=hashlib.sha256((d/"micro.ZINI").read_bytes()).hexdigest()))
with (root/"INPUT_TABLE.csv").open("w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
(root/"INPUT_SPEC.json").write_text(json.dumps({
 "grid":[41,41],"experiment":"03z threshold sweep of actual model main-lake west/east inlet throat",
 "original_TIE_case_kept_unchanged":True,"cell_site_west_rc":[20,11],
 "cell_site_east_rc":[20,29],"basin_floor_row_col":[20,20],
 "all_physical_settings_fixed":True,"one_initial_elevation_cell_modified":True,
 "no_tectonic_UNITs":True,"experiments":results},indent=2))
print("03Z_THRESHOLD_INPUT "+json.dumps({"cases":len(results),"base_throat_m":float(base[20,11])}))
