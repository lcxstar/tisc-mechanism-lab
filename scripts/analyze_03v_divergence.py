#!/usr/bin/env python3
"""03v stage test: compare author 6_tectonics float/double sediment arithmetic.

Scientific output is 0.1-m rounded, so first "visible" divergence is NOT
necessarily the first microscopic float64 arithmetic difference.
Check lake node memberships and outlet locations, not only .lak text hashes.
"""
import csv,hashlib,json,math,re,sys
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse_xyw(p,n):
    d={}
    with p.open(errors="replace") as f:
        for line in f:
            if not line.strip() or line.startswith("#"):continue
            a=line.split()
            if len(a)<9:raise RuntimeError("Bad .xyw data "+str(a))
            loc=(a[0],a[1])
            if loc in d:raise RuntimeError("Duplicate xyw "+str(loc))
            tp=float(a[5]);q=float(a[2]);sed=float(a[3])
            if not all(map(math.isfinite,(tp,q,sed))):raise RuntimeError("Non-finite xyw field")
            d[loc]=(tp,a[4],a[6],a[7],q,sed)
    if len(d)!=n*n:raise RuntimeError("xyw rows "+str(len(d))+" expected "+str(n*n))
    return d
def parse_lakes(path):
    lakes=[]
    curr=None
    with path.open(errors="replace") as f:
        for raw in f:
            s=raw.strip()
            if s.startswith(">Lake "):
                if curr:lakes.append(curr)
                curr={"nodes":set(),"outlets":set(),"header":s}
            elif curr and s and not s.startswith("#"):
                a=s.split()
                if len(a)>2:
                    try:point=(f"{float(a[0]):.3f}",f"{float(a[1]):.3f}")
                    except ValueError:continue
                    curr["nodes"].add(point)
                    if a[2]=="E":curr["outlets"].add(point)
    if curr:lakes.append(curr)
    return lakes
def lakes_comparison(a,b):
    pa, pb=parse_lakes(a),parse_lakes(b)
    all_a=set().union(*(p["nodes"] for p in pa)) if pa else set()
    all_b=set().union(*(p["nodes"] for p in pb)) if pb else set()
    out_a=set().union(*(p["outlets"] for p in pa)) if pa else set()
    out_b=set().union(*(p["outlets"] for p in pb)) if pb else set()
    canon=lambda ls:sorted(hashlib.sha256("\n".join(sorted(
        x+","+y for x,y in p["nodes"])).encode()).hexdigest() for p in ls)
    return {"lake_count_baseline":len(pa),"lake_count_double":len(pb),
      "lake_total_members_baseline":sum(len(x["nodes"]) for x in pa),
      "lake_total_members_double":sum(len(x["nodes"]) for x in pb),
      "lake_any_member_union_change":len(all_a^all_b),
      "lake_total_outlets_baseline":sum(len(p["outlets"]) for p in pa),
      "lake_total_outlets_double":sum(len(p["outlets"]) for p in pb),
      "lake_outlet_coordinates_changed":len(out_a^out_b),
      "component_member_sets_identical":canon(pa)==canon(pb)}
def parse_horizon(path,n):
    fields={}; densities=[]
    with path.open(errors="replace") as f:
        next(f)
        header=next(f)
        # first density is crust; following densities match Block[0..].
        if "Dens:" in header:
            numeric=header.split("Dens:",1)[1].split("water",1)[0].split()
            densities=[float(x) for x in numeric][1:]
        for line in f:
            if not line.strip() or line.startswith("#"):continue
            a=line.split()
            xy=(f"{float(a[0]):.3f}",f"{float(a[1]):.3f}")
            z=[float(x) for x in a[2:]]
            if len(z)!=len(densities)+1:raise RuntimeError("Unexpected horizon column to block-density mapping")
            sediment_proxy=sum(max(0.,z[k+1]-z[k]) for k,x in enumerate(densities) if abs(x-2200.)<1.)
            fields[xy]=(z,sediment_proxy)
    if len(fields)!=n*n:raise RuntimeError("Wrong horizon grid size")
    return fields
def compare(root,expect_horizon):
    root=Path(root)
    audit=json.loads((root/"INPUT_AUDIT.json").read_text())
    n=audit["Nx"]
    left=root/"reference";right=root/"optimized"
    code={};times={};budget={};binhash={}
    for typ,d in (("baseline",left),("double",right)):
        code[typ]=int((d/"EXIT_CODE.txt").read_text())
        text=(d/"RUN.log").read_text(errors="replace")
        xs=[float(t) for t in re.findall(r"(?m)^\s*T=\s*(\d+(?:\.\d+)?)\s*My",text)]
        times[typ]=xs[-1] if xs else None
        bs=[abs(float(t)) for t in re.findall(r"TISC_03T_CORRECTED_BALANCE[^\n]*balance_pct=([^\s]+)",text)]
        budget[typ]=max(bs) if bs else None
        binhash[typ]={ext:sha(d/("demo"+ext)) for ext in (".xyw",".st",".hrz",".lak",".bas",".pfl",".xyzt")}
    a,b=parse_xyw(left/"demo.xyw",n),parse_xyw(right/"demo.xyw",n)
    if set(a)!=set(b):raise RuntimeError("Comparison grid coordinates differ")
    altitude_sq=0.;changed=0;maxdelta=0.;type_changed=[];edge_changed=[];q_changed=0
    for xy,x in a.items():
        y=b[xy];diff=y[0]-x[0]
        altitude_sq+=diff*diff
        if diff!=0:changed+=1;maxdelta=max(maxdelta,abs(diff))
        if x[1]!=y[1]:type_changed.append([*xy,x[1],y[1]])
        if x[2:4]!=y[2:4]:edge_changed.append([*xy,*x[2:4],*y[2:4]])
        if x[4]!=y[4]:q_changed+=1
    lake=lakes_comparison(left/"demo.lak",right/"demo.lak")
    ha,hb=parse_horizon(left/"demo.hrz",n),parse_horizon(right/"demo.hrz",n)
    if set(ha)!=set(hb):raise RuntimeError("Horizon coordinate mismatch")
    sed_sum_a=sum(v[1] for v in ha.values())
    sed_sum_b=sum(v[1] for v in hb.values())
    sed_delta_sq=sum((ha[xy][1]-hb[xy][1])**2 for xy in ha)
    dx=(audit.get("author_model_extent_x_km",500.)/(n-1))
    dy=(audit.get("author_model_extent_y_km",500.)/(n-1))
    aarea=dx*dy/1000. # m thickness * km^2 /1000 -> km^3
    sed_vol_a=sed_sum_a*aarea
    sed_vol_b=sed_sum_b*aarea
    topology=bool(type_changed or edge_changed or lake["lake_count_baseline"]!=lake["lake_count_double"] or lake["lake_any_member_union_change"] or lake["lake_outlet_coordinates_changed"] or not lake["component_member_sets_identical"])
    success=(audit["reference_optimized_same_inputs"] and
          code["baseline"]==code["double"]==0 and
          all(v is not None and abs(v-float(expect_horizon))<1e-5 for v in times.values())
          and all(v is not None and v<.001 for v in budget.values()))
    result={"experiment":"03v first printed-field divergence, hydro topology and flux under controlled float/double local dh_sed",
     "Nx":n,"simulated_horizon_Myr":float(expect_horizon),"dt_Myr":audit["dt_Myr"],"dt_eros_Myr":audit["dt_eros_Myr"],
     "original_401_author_inputs_exact":audit["author_full_inputs_byte_exact"],
     "same_input":audit["reference_optimized_same_inputs"],
     "completed_pair":success,"exit_codes":code,"actual_last_times":times,"max_double_ledger_balance_pct":budget,
     "elevation_different_cells":changed,"elevation_max_abs_difference_m":maxdelta,
     "elevation_RMS_m":math.sqrt(altitude_sq/(n*n)),"elevation_output_rounded_0p1m":True,
     "drainage_type_changed_cells":len(type_changed),"downstream_direction_changed_cells":len(edge_changed),
     "different_printed_discharge_cells":q_changed,
     "topology_change_observed":topology,"lake_topology":lake,
     "sediment_horizon_compacted_proxy_volume_km3":{"baseline":sed_vol_a,"double":sed_vol_b,
     "difference_percent_of_baseline":100*(sed_vol_b-sed_vol_a)/sed_vol_a if sed_vol_a else None},
     "sediment_horizon_proxy_RMS_difference_m":math.sqrt(sed_delta_sq/(n*n)),
     "field_sha_identical":{key:binhash["baseline"][key]==binhash["double"][key] for key in binhash["baseline"]},
     "first_type_difference_locations":type_changed[:50],
     "first_direction_difference_locations":edge_changed[:50],
     "interpretation":"First differences are at output rounding threshold, not exact first microscopic numerical difference. Lake identity based on component membership, not arbitrary lake ID.",
     "model_is_all_double":False}
    (root/"03V_STAGE_QC.json").write_text(json.dumps(result,indent=2,allow_nan=False))
    simple={k:v for k,v in result.items() if k not in ("field_sha_identical","first_type_difference_locations","first_direction_difference_locations","lake_topology","sediment_horizon_compacted_proxy_volume_km3")}
    simple.update({"lake_count_a":lake["lake_count_baseline"],"lake_count_b":lake["lake_count_double"],
      "lake_component_set_equal":lake["component_member_sets_identical"],
      "sed_volume_a_km3":sed_vol_a,"sed_volume_b_km3":sed_vol_b})
    print("03V_STAGE_QC "+json.dumps(simple))
    if not success:raise SystemExit("03v: a model exited prematurely, inputs differ or mass balance fails")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("analyze_03v_divergence.py PAIRED_ROOT END_MYR")
    compare(sys.argv[1],sys.argv[2])
