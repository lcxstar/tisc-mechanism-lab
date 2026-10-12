#!/usr/bin/env python3
"""Create provenance-labeled timeline figures from three archived Ebro model logs."""
from pathlib import Path
import csv,math,argparse,json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
def read(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))
def series(rows,key):
    a=[];b=[]
    for r in rows:
        try:v=float(r[key]);t=float(r["time_Myr"] if "time_Myr" in r else r["age_Ma"])
        except (ValueError,TypeError,KeyError):continue
        if math.isfinite(v):a.append(t);b.append(v)
    return a,b
def figure(out,title,ylabel,rows,plots):
    fig,ax=plt.subplots(figsize=(9,5.5),layout="constrained")
    for label,col,table in plots:
        x,y=series(rows if table is None else table,col)
        if x:ax.plot(x,y,label=label,linewidth=1.8)
    ax.set(xlabel="Simulation age (Ma)",ylabel=ylabel,title=title)
    ax.grid(alpha=.25);ax.legend(loc="best",fontsize=9)
    fig.text(.12,.015,"Historical 2016 reference and 2026 pinned code are NOT numerically equivalent. Source: original TISC model logs.",fontsize=8)
    fig.savefig(str(out)+".png",dpi=175);fig.savefig(str(out)+".pdf")
    plt.close(fig)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--reference",type=Path,required=True)
    p.add_argument("--surface",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    h=read(a.reference);s=read(a.surface)
    figure(a.out/"EBRO_2016_VS_2026_VS_NO_SURFACE_MAX_HEIGHT",
           "Ebro foreland model: distinct historical and modern runs",
           "Max simulated topography (m)",h,[
             ("Author archived 2016", "author_model_surface_max_m",None),
             ("Pinned 2026 full model", "current_model_surface_max_m",None),
             ("Pinned 2026, hydro and erosion off", "no_surface_surface_max_m",s)])
    figure(a.out/"EBRO_2016_VS_2026_SEDIMENT_VOLUME",
           "Ebro foreland model: author's 2016 versus current model",
           "Printed cumulative sediment volume (km³)",h,[
             ("Author archived 2016", "author_printed_sediment_volume_km3",None),
             ("Pinned 2026 full model", "current_printed_sediment_volume_km3",None)])
    (a.out/"FIGURE_PROVENANCE.json").write_text(json.dumps({
      "source_2016":"Historical author-provided Ebro_evol.screen",
      "source_2026":"Pinned original input / audited 03t current source 60 Ma full",
      "surface_disabled":"Same input / CLI -qerosed_model=0 -qhydro_model=0",
      "data_ref":"Original logs aligned at matching 0.5 Myr stage intervals",
      "historical_equality_proven":False,
      "not_original_GMT_Pc":True,
      "figures":["EBRO_2016_VS_2026_VS_NO_SURFACE_MAX_HEIGHT","EBRO_2016_VS_2026_SEDIMENT_VOLUME"]
    },indent=2))
if __name__=="__main__":main()
