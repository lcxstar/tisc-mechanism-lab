#!/usr/bin/env python3
"""03y factorial QC for tiny down-slope route tie-breaking experiment.

Four independent physics runs with same geological and temporal inputs:
F0 original local float dh_sed, exact steepest slope
D0 local double dh_sed, exact steepest slope
F1 original local float, tol 1e-8 slope before replacing selected downhill
D1 local double, tol 1e-8 slope before replacing selected downhill.
This makes no determination of which physical trajectory is the true one.
"""
import csv,hashlib,json,math,re,sys
from pathlib import Path
import numpy as np
def read(root,n):
    d=root
    with (d/"demo.hrz").open() as f:
        f.readline()
        hdr=f.readline()
        densities=np.array([float(v) for v in hdr.split("Dens:")[1].split("water")[0].split()])
        xyz=np.loadtxt(f)
    if len(xyz)!=n*n or xyz.shape[1]!=len(densities)+2:raise RuntimeError("Bad .hrz shape")
    vals=xyz[:,2:]
    thick=np.diff(vals,axis=1)
    unit_select=np.isclose(densities[1:],2200)
    sed=np.maximum(0,thick[:,unit_select]).sum(axis=1).reshape(n,n)
    bas=vals[:,0].reshape(n,n)
    with (d/"demo.xyw").open() as f:
        lines=[s.split() for s in f if s.strip() and not s.startswith("#")]
    if len(lines)!=n*n:raise RuntimeError("Bad .xyw size")
    if not np.allclose(xyz[:,:2],np.array([[float(x[0]),float(x[1])] for x in lines]),atol=.009,rtol=0):
        raise RuntimeError("Grid coordinates mismatch")
    z=np.array([float(a[5]) for a in lines]).reshape(n,n)
    typ=np.array([a[4] for a in lines])
    dst=np.array([[float(a[6]),float(a[7])] for a in lines])
    xyzt=np.loadtxt(d/"demo.xyzt",comments="#")
    if xyzt.shape!=(n*n,5) or not np.allclose(xyzt[:,:2],xyz[:,:2],atol=.009,rtol=0):
        raise RuntimeError("Missing true flexural w")
    w=xyzt[:,2].reshape(n,n)
    xx=np.unique(xyz[:,0]); yy=np.unique(xyz[:,1])
    assert len(xx)==len(yy)==n
    # Arrays are ordered north->south, integrate with pixel index-independent area.
    # Cell area per vertex applied with 0.5 boundary weights (trapezoidal integral).
    wx=np.ones(n);wx[[0,-1]]=.5
    wy=np.ones(n);wy[[0,-1]]=.5
    dx=500/(n-1);area=dx*dx
    wt=wy[:,None]*wx[None,:]
    vol=float((sed*wt).sum()*area/1000)
    mass=(sed*wt)
    center_x=float((mass*xx[None,:]).sum()/mass.sum()) if mass.sum() else None
    center_y=float((mass*yy[::-1,None]).sum()/mass.sum()) if mass.sum() else None
    flat=sed.ravel()
    ii=int(np.argmax(flat)); row,col=divmod(ii,n)
    ext={}
    for suf in (".xyw",".hrz",".st",".bas",".pfl",".lak",".xyzt"):
        p=d/("demo"+suf);ext[suf]=hashlib.sha256(p.read_bytes()).hexdigest()
    log=(d/"RUN.log").read_text(errors="replace")
    times=[float(x) for x in re.findall(r"(?m)^\s*T=\s*(\d+(?:\.\d+)?)\s*My",log)]
    mass_balance=[abs(float(x)) for x in re.findall(r"TISC_03T_CORRECTED_BALANCE[^\n]*balance_pct=([^\s]+)",log)]
    return dict(sed=sed,topo=z,w=w,base=bas,typ=typ,dst=dst,xy=xyz[:,:2],
       sed_vol_km3=vol,sed_max_m=float(flat.max()),sed_mean_m=float(flat.mean()),
       sediment_center_x_km=center_x,sediment_center_y_km=center_y,
       depocentre_x_km=float(xx[col]),depocentre_y_km=float(yy[::-1][row]),
       topo_max_m=float(z.max()),topo_min_m=float(z.min()),
       flex_min_m=float(w.min()),flex_max_m=float(w.max()),
       max_balance_pct=max(mass_balance) if mass_balance else None,
       last_time=times[-1] if times else None,
       exitcode=int((d/"EXIT_CODE.txt").read_text()),
       hash=ext)
def compare(a,b):
    z=b["topo"]-a["topo"]
    s=b["sed"]-a["sed"]
    w=b["w"]-a["w"]
    bas=b["base"]-a["base"]
    return dict(
      topo_rms_m=float(np.sqrt((z*z).mean())),topo_max_abs_m=float(np.max(np.abs(z))),
      changed_topo_cells=int(np.count_nonzero(z)),
      sediment_rms_m=float(np.sqrt((s*s).mean())),
      sediment_max_abs_m=float(np.max(np.abs(s))),
      flexure_w_rms_m=float(np.sqrt((w*w).mean())),
      flexure_w_max_abs_m=float(np.max(np.abs(w))),
      basal_interface_rms_m=float(np.sqrt((bas*bas).mean())),
      changed_downstream_count=int(np.count_nonzero(np.any(np.abs(a["dst"]-b["dst"])>.001,axis=1))),
      changed_drain_types=int(np.count_nonzero(a["typ"]!=b["typ"])),
      sed_volume_diff_km3=b["sed_vol_km3"]-a["sed_vol_km3"],
      sed_volume_diff_pct=float(100*(b["sed_vol_km3"]/a["sed_vol_km3"]-1)),
      sed_center_shift_km=float(np.hypot(b["sediment_center_x_km"]-a["sediment_center_x_km"],
        b["sediment_center_y_km"]-a["sediment_center_y_km"])),
      depocentre_shift_km=float(np.hypot(b["depocentre_x_km"]-a["depocentre_x_km"],b["depocentre_y_km"]-a["depocentre_y_km"])))
def main(root,n,horizon):
    root=Path(root);d={k:read(root/k,n) for k in ["F0","D0","F1","D1"]}
    for key,x in d.items():
        if x["exitcode"]!=0 or x["last_time"] is None or abs(x["last_time"]-horizon)>1e-4:
            raise RuntimeError(key+" simulation did not complete requested geologic interval")
        if x["max_balance_pct"] is None or x["max_balance_pct"]>=.001:
            raise RuntimeError(key+" double sidecar mass balance failed")
    pairs={"float_tie_F0_F1":("F0","F1"),
        "double_tie_D0_D1":("D0","D1"),
        "original_precision_F0_D0":("F0","D0"),
        "controlled_precision_F1_D1":("F1","D1")}
    diff={k:compare(d[l],d[r]) for k,(l,r) in pairs.items()}
    metric={k:{q:v for q,v in d[k].items() if q not in
        ("sed","topo","w","base","typ","dst","xy","hash")} for k in d}
    same_input={k:json.loads((root/k/"INPUT_AUDIT.json").read_text()) for k in d}
    src={k:hashlib.sha256((root/k/"demo.PRM").read_bytes()).hexdigest() for k in d}
    if len(set(src.values()))!=1:raise RuntimeError("Not a controlled same input experiment")
    if not all(v["reference_optimized_same_inputs"] for v in same_input.values()):
        raise RuntimeError("Input audit failed")
    result={"experiment":"03y pre-registered single-mechanism route tie threshold factorial",
      "grid":n,"horizon_Myr":horizon,"source":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd",
      "slope_epsilon_0_vs_1e_minus8_m_per_m":True,
      "four_exact_same_input_PRM_sha256":src,
      "physical_states_all_float_except_candidate_temporary":True,
      "standalone_candidate_patch_not_a_validated_fix":True,
      "QC_pass":True,"runs":metric,"pairs":diff,
      "field_sha256":{k:d[k]["hash"] for k in d},
      "analysis_note":"One-point maximum difference and named lake counts alone do not prove reliability. A reduction of F1-D1 sensitivity is not same-scheme convergence or true solution accuracy."}
    (root/"03Y_4WAY_SCIENCE_QC.json").write_text(json.dumps(result,indent=2,allow_nan=False))
    with (root/"03Y_SCIENCE_METRICS.csv").open("w",newline="") as f:
        fields=["run"]+list(next(iter(metric.values())))
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for k,v in metric.items():w.writerow(dict(run=k,**v))
    with (root/"03Y_PAIRED_DIFFERENCES.csv").open("w",newline="") as f:
        fields=["pair"]+list(next(iter(diff.values())))
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for k,v in diff.items():w.writerow(dict(pair=k,**v))
    # No change to physical test input; epsilon arm is deliberately not asserted to improve.
    print("03Y_QC "+json.dumps({"grid":n,"horizon_Myr":horizon,
       "runs":metric,"pairs":diff,"pass":True},allow_nan=False))
if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("analyze_03y_tie_sensitivity.py ROOT GRID HORIZON_MYR")
    main(sys.argv[1],int(sys.argv[2]),float(sys.argv[3]))
