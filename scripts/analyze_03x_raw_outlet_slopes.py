#!/usr/bin/env python3
"""03x experimental output-only high-precision inspection at first changed outlets.
Float32 storage is printed with %.9g (roundtrip precision) rather than %.1f.
Both binaries receive SAME tiscio patch, only their dh_sed intermediate differs.
"""
import csv,json,sys
from pathlib import Path
import numpy as np

def read(path):
    d={}
    with path.open() as f:
        for line in f:
            if line.startswith("#") or not line.strip():continue
            a=line.split()
            d[round(float(a[0]),2),round(float(a[1]),2)]=(float(a[5]),a[4],
                (round(float(a[6]),2),round(float(a[7]),2)))
    return d

def slopes(z,point,dx):
    x,y=point; cand=[]
    for di in (-1,0,1):
        for dj in (-1,0,1):
            if not di and not dj:continue
            pt=round(x+dx*dj,2),round(y+dx*di,2)
            if pt not in z:continue
            v=(z[point][0]-z[pt][0])/(dx*np.hypot(di,dj))
            cand.append((float(v),pt))
    return sorted(cand,reverse=True)

def main(droot):
    root=Path(droot);left=read(root/"reference/demo.xyw");right=read(root/"optimized/demo.xyw")
    if set(left)!=set(right):raise RuntimeError("XY grid mismatch")
    xx=sorted({t[0] for t in left});dx=xx[1]-xx[0]
    output=[]
    for p in sorted(left):
        za,ta,ea=left[p];zb,tb,eb=right[p]
        if ta==tb and ea==eb:continue
        a=slopes(left,p,dx);b=slopes(right,p,dx)
        output.append({"x_km":p[0],"y_km":p[1],
          "height32_rawfloat_m":za,"height64variant_rawfloat_m":zb,
          "height_delta_m":zb-za,
          "type32":ta,"type64":tb,
          "downstream32":str(ea),"downstream64":str(eb),
          "best_grad32_m_per_km":a[0][0] if a else None,
          "best_grad64_m_per_km":b[0][0] if b else None,
          "top2_grad_margin32_m_per_km":a[0][0]-a[1][0] if len(a)>1 else None,
          "top2_grad_margin64_m_per_km":b[0][0]-b[1][0] if len(b)>1 else None,
          "outlet_changed":ta!=tb,
          "route_changed":ea!=eb,
          "same_raw_float_height":za==zb})
    (root/"03X_RAWFLOAT_OUTLET.json").write_text(json.dumps({
       "paired_grid_n":len(xx),"changed_nodes":len(output),
       "same_rawfloat_height_at_changed_nodes":sum(x["same_raw_float_height"] for x in output),
       "route_changed":sum(x["route_changed"] for x in output),
       "type_changed":sum(x["outlet_changed"] for x in output),
       "interpretation":"Slope maxima estimated from final saved float32 topo; not exact moment of saddle branch; first divergence predates 3Myr",
       "nodes":output},indent=2))
    if output:
       with (root/"03X_RAWFLOAT_CHANGED_EDGES.csv").open("w",newline="") as f:
          w=csv.DictWriter(f,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
    print("03X_RAWFLOAT_QC "+json.dumps({"N":len(xx),"changed":len(output),
          "same_exact_float_height":sum(x["same_raw_float_height"] for x in output),
          "changed_edges":sum(x["route_changed"] for x in output),
          "changed_types":sum(x["outlet_changed"] for x in output)}))
    assert output,"Expected t=3 Myr changed runoff topology at first probe stage"
if __name__=="__main__":
   if len(sys.argv)!=2:raise SystemExit("analyze_03x_raw_outlet_slopes.py PAIR_ROOT")
   main(sys.argv[1])
