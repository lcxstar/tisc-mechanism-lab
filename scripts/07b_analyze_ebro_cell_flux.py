#!/usr/bin/env python3
"""Find the first unstable TISC erosion substep and its exact grid cells/flux.

Consumes V07 read-only C output: three aligned 208x110 snapshots per surface
substep. Does not alter numerical simulation.
"""
from pathlib import Path
import argparse,gzip,csv,math,json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FIELDS=["topo_m","discharge_m3s","masstr_kg_s","eroded_kg","deposited_kg","Dq_Pa",
        "lake_id","node_type","dr_row","dr_col"]
NMAP={"topo_m":"z","discharge_m3s":"q","masstr_kg_s":"sedflux",
     "eroded_kg":"erosion","deposited_kg":"deposit","Dq_Pa":"Dq",
     "lake_id":"lake","node_type":"type","dr_row":"dr_row","dr_col":"dr_col"}
def jfinite(x):
    x=float(x)
    return None if not math.isfinite(x) else x
def build(inpath):
    groups={}
    with gzip.open(inpath,"rt",newline="") as f:
        reader=csv.DictReader(f)
        for q in reader:
            s=int(q["step"]);phase=q["phase"]
            k=(s,phase)
            bucket=groups.setdefault(k,[])
            bucket.append(q)
    return groups
def grid(rows):
    assert rows
    nr=max(int(r["row"]) for r in rows)+1
    nc=max(int(r["col"]) for r in rows)+1
    assert nr*nc==len(rows),(nr,nc,len(rows))
    arrays={name:np.full((nr,nc),np.nan) for name in FIELDS}
    x=np.full((nr,nc),np.nan);y=x.copy()
    for r in rows:
        i=int(r["row"]);j=int(r["col"])
        for v in FIELDS:arrays[v][i,j]=float(r[v])
        x[i,j]=float(r["x_km"]);y[i,j]=float(r["y_km"])
    assert np.isfinite(arrays["topo_m"]).all()
    return arrays,x,y
def pt(i,j,x,y,**kwargs):
    return dict(row=int(i),col=int(j),x_km=float(x[i,j]),y_km=float(y[i,j]),**kwargs)
def output_map(a,loc,out):
    fig,ax=plt.subplots(figsize=(10,5.8),layout="constrained")
    xmin,xmax=float(loc["x"].min()),float(loc["x"].max())
    ymin,ymax=float(loc["y"].min()),float(loc["y"].max())
    z=a["topo_m"]
    im=ax.imshow(z,origin="upper",extent=(xmin,xmax,ymin,ymax),
        interpolation="nearest",aspect="auto",cmap="terrain",vmin=float(np.nanpercentile(z,1)),
        vmax=max(1500,float(np.nanpercentile(z,99.5))))
    ax.scatter([loc["peak"]["x_km"]],[loc["peak"]["y_km"]],marker="*",s=170,
        c="red",edgecolors="black",zorder=5,label="Largest simulated topography")
    ax.set(xlabel="TISC model x (km)",ylabel="TISC model y (km)",
      title="Ebro V07 — first anomalous substep, original 208×110 model grid")
    ax.legend()
    fig.colorbar(im,ax=ax,shrink=.75,label="Simulated topography (m)")
    fig.text(.11,.01,"LOCAL TISC model coordinates, not geographic longitude/latitude. Diagnostics-only original-source build.",fontsize=8)
    fig.savefig(str(out)+".png",dpi=170);fig.savefig(str(out)+".pdf")
    plt.close(fig)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--csv",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    groups=build(a.csv)
    steps=sorted({k[0] for k in groups})
    assert steps and all((s,phase) in groups for s in steps
       for phase in ["after_increment","after_routing","after_transport"])
    events=[]; summaries=[]; geo=[]
    chosen=None; chosen_grids=None
    for step in steps:
        pre,x,y=grid(groups[(step,"after_increment")])
        routing,_,_=grid(groups[(step,"after_routing")])
        post,_,_=grid(groups[(step,"after_transport")])
        dz=post["topo_m"]-pre["topo_m"]
        r,c=np.unravel_index(np.nanargmax(post["topo_m"]),post["topo_m"].shape)
        dr,dc=np.unravel_index(np.nanargmax(dz),dz.shape)
        er,de=np.unravel_index(np.nanargmax(post["eroded_kg"]),dz.shape),np.unravel_index(np.nanargmax(post["deposited_kg"]),dz.shape)
        xpt=pt(r,c,x,y,after_increment_topo_m=jfinite(pre["topo_m"][r,c]),
           after_routing_topo_m=jfinite(routing["topo_m"][r,c]),
           after_transport_topo_m=jfinite(post["topo_m"][r,c]),
           within_substep_topography_gain_m=jfinite(dz[r,c]),
           receiver_row=int(post["dr_row"][r,c]),
           receiver_col=int(post["dr_col"][r,c]),
           runoff_discharge_m3_s=jfinite(post["discharge_m3s"][r,c]),
           transported_sediment_kg_s=jfinite(post["masstr_kg_s"][r,c]),
           eroded_mass_kg=jfinite(post["eroded_kg"][r,c]),
           deposited_mass_kg=jfinite(post["deposited_kg"][r,c]),
           Dq_Pa=jfinite(post["Dq_Pa"][r,c]),lake_id=int(post["lake_id"][r,c]),
           type=int(post["node_type"][r,c]))
        summary={
          "substep":step,"grid_nodes":int(post["topo_m"].size),
          "max_topography_after_increment_m":float(pre["topo_m"].max()),
          "max_topography_after_routing_m":float(routing["topo_m"].max()),
          "max_topography_after_transport_m":float(post["topo_m"].max()),
          "min_topography_after_transport_m":float(post["topo_m"].min()),
          "n_cells_height_over_1500m":int((post["topo_m"]>1500).sum()),
          "n_cells_height_over_2000m":int((post["topo_m"]>2000).sum()),
          "n_cells_height_over_4000m":int((post["topo_m"]>4000).sum()),
          "n_cells_height_over_8000m":int((post["topo_m"]>8000).sum()),
          "max_substep_topo_gain_m":float(dz.max()),
          "max_substep_topo_loss_m":float(dz.min()),
          "largest_absolute_water_discharge_m3s":float(np.nanmax(np.abs(post["discharge_m3s"]))),
          "largest_abs_sediment_kg_s":float(np.nanmax(np.abs(post["masstr_kg_s"]))),
          "total_eroded_mass_kg":float(np.nansum(post["eroded_kg"])),
          "total_deposited_mass_kg":float(np.nansum(post["deposited_kg"])),
          "peak_location":xpt,
          "max_growth_location":pt(dr,dc,x,y,topo_gain_m=float(dz[dr,dc])),
          "max_erosion_location":pt(*er,x,y,eroded_kg=float(post["eroded_kg"][er])),
          "max_deposition_location":pt(*de,x,y,deposited_kg=float(post["deposited_kg"][de]))
        }
        summaries.append(summary)
        if chosen is None and summary["n_cells_height_over_1500m"]>0:
            chosen=summary;chosen_grids=dict(pre=pre,routing=routing,post=post,x=x,y=y,dz=dz)
        # For exact growth-max, not only highest altitude, export local top20 annual flux.
        ranking=np.argsort(dz.ravel())[::-1][:30]
        for idx in ranking:
            i,j=np.unravel_index(idx,dz.shape)
            if not np.isfinite(dz[i,j]):continue
            obj=pt(i,j,x,y,substep=step,topography_before_m=float(pre["topo_m"][i,j]),
               topography_after_m=float(post["topo_m"][i,j]),
               substep_growth_m=float(dz[i,j]),
               discharge_m3_s=float(post["discharge_m3s"][i,j]),
               sediment_flux_kg_s=float(post["masstr_kg_s"][i,j]),
               eros_kg=float(post["eroded_kg"][i,j]),sed_kg=float(post["deposited_kg"][i,j]),
               receiver_row=int(post["dr_row"][i,j]),receiver_col=int(post["dr_col"][i,j]),
               lake_id=int(post["lake_id"][i,j]))
            events.append(obj)
    assert chosen is not None,"No cell reached 1500m: no first anomaly to locate"
    # pin local neighborhood and drainage at first step that exceeds 1500m
    q=chosen_grids
    peak=chosen["peak_location"];pr=peak["row"];pc=peak["col"]
    neighborhood=[]
    for i in range(max(0,pr-3),min(q["x"].shape[0],pr+4)):
        for j in range(max(0,pc-3),min(q["x"].shape[1],pc+4)):
            neighborhood.append(pt(i,j,q["x"],q["y"],
               topo_pre_m=float(q["pre"]["topo_m"][i,j]),
               topo_route_m=float(q["routing"]["topo_m"][i,j]),
               topo_post_m=float(q["post"]["topo_m"][i,j]),
               substep_delta_m=float(q["dz"][i,j]),
               water_discharge_m3_s=float(q["post"]["discharge_m3s"][i,j]),
               sediment_flux_kg_s=float(q["post"]["masstr_kg_s"][i,j]),
               eroded_kg=float(q["post"]["eroded_kg"][i,j]),
               deposited_kg=float(q["post"]["deposited_kg"][i,j]),
               Dq_Pa=float(q["post"]["Dq_Pa"][i,j]),
               lake=int(q["post"]["lake_id"][i,j]),
               receiver_row=int(q["post"]["dr_row"][i,j]),
               receiver_col=int(q["post"]["dr_col"][i,j])))
    foci=events+neighborhood
    for e in foci:
        geo.append({"type":"Feature","geometry":{"type":"Point",
           "coordinates":[e["x_km"]*1000,e["y_km"]*1000]},
           "properties":e})
    (a.out/"FIRST_ANOMALY_CELLS_LOCAL_MODEL_M.geojson").write_text(json.dumps({
         "type":"FeatureCollection","properties":{"coordinate_reference":"TISC local Cartesian model m; no WGS84/EPSG implied"},
         "features":geo}))
    cols=list(summaries[0]);cols.remove("peak_location");cols.remove("max_growth_location");cols.remove("max_erosion_location");cols.remove("max_deposition_location")
    with (a.out/"ALL_SURFACE_SUBSTEPS.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for r in summaries:w.writerow({k:r[k] for k in cols})
    with (a.out/"TOP30_GROWTH_CELLS_EACH_SUBSTEP.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=events[0]);w.writeheader();w.writerows(events)
    with (a.out/"FIRST_ANOMALY_7x7_CELL_FLUX.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=neighborhood[0]);w.writeheader();w.writerows(neighborhood)
    diagnostic={"first_anomalous_substep":chosen["substep"],
      "first_anomalous_substep_start_Ma":-60.+.05*(chosen["substep"]-1),
      "first_anomalous_substep_end_Ma":-60.+.05*chosen["substep"],
      "first_anomaly_threshold_m":1500.0,
      "first_anomalous_step":chosen,
      "all_steps":summaries,
      "pre_routing_transport_snapshots_original_native_source":True,
      "sediment_flux_is_kg_per_second_snapshot_not_integrated_mass":True,
      "eroded_and_deposited_mass_integrate_each_substep_only":True,
      "mass_per_cell_includes_all_Sediment_and_Erode_calls":True,
      "the_diagnostic_pass_is_not_a_sediment_mass_conservation_proof":True,
      "local_xy_coordinate_system":"TISC local km as defined by original PRM (not longitude latitude)"}
    (a.out/"FIRST_UNSTABLE_CELL_REPORT.json").write_text(json.dumps(diagnostic,indent=2))
    with (a.out/"FIRST_UNSTABLE_CELL_REPORT.md").open("w") as f:
        f.write("# Original Ebro 208x110 surface transport: first unstable native cell\n\n")
        f.write("This diagnostic instrumented the **original current-source** TISC fluvial loop "
         "without changing its physics expressions; original PRM/UNIT/ZINI inputs remain byte-identical. "
         "The first 0.5 Myr tectonic step consists of 10 × 0.05 Myr surface substeps. "
         "Snapshots are from after Dtopo increment, after runoff routing, and after fluvial erosion/deposition.\n\n")
        f.write("**Earliest maximum exceeding 1500m:** substep **"+str(chosen["substep"])+
          "**, time "+str(diagnostic["first_anomalous_substep_start_Ma"])+" to "+
          str(diagnostic["first_anomalous_substep_end_Ma"])+" Ma.\n\n")
        f.write("| Substep | Max pre transport (m) | Max post transport (m) | Max gain (m) | Cells above 2000m | Total deposition (kg) | Max flux (kg/s) |\n|---|---:|---:|---:|---:|---:|---:|\n")
        for d in summaries:
            f.write("| "+str(d["substep"])+" | "+str(round(d["max_topography_after_increment_m"],2))+
                " | "+str(round(d["max_topography_after_transport_m"],2))+
                " | "+str(round(d["max_substep_topo_gain_m"],2))+
                " | "+str(d["n_cells_height_over_2000m"])+
                " | "+str(round(d["total_deposited_mass_kg"],2))+
                " | "+str(round(d["largest_abs_sediment_kg_s"],2))+" |\n")
        f.write("\n## First peak cell (model Cartesian coordinates)\n\n\`\`\`json\n"+
           json.dumps(peak,indent=2)+"\n\`\`\`\n\n")
        f.write("The top 30 growth cells per step and precise 7x7 neighborhood, "
        "with receiver graph, lake identity, discharge, sediment mass and native load, are "
        "saved as CSV and GeoJSON. **Do not infer real-world longitude/latitude** from model x/y. "
        "Mass flux and accumulated mass must not be interchanged, and this diagnosis "
        "does not establish full 60 Myr scientific agreement.\n")
    output_map(q["post"],dict(x=q["x"],y=q["y"],peak=peak),a.out/"FIRST_ANOMALOUS_STEP_TOPOGRAPHY")
    fig,ax=plt.subplots(figsize=(9,5),layout="constrained")
    ax.plot([s["substep"] for s in summaries],[s["max_topography_after_transport_m"] for s in summaries],marker="o")
    ax.axhline(1500,ls="--",label="First anomaly criterion 1500m")
    ax.set(xlabel="Within first 0.5 Myr: 0.05-Myr surface substep",ylabel="Maximum TISC simulated topography (m)",
           title="Ebro 208x110 first-step numerical runaway")
    ax.grid(alpha=.2);ax.legend()
    fig.savefig(a.out/"SUBSTEP_TOPOGRAPHY_MAX_TIMELINE.png",dpi=175)
    fig.savefig(a.out/"SUBSTEP_TOPOGRAPHY_MAX_TIMELINE.pdf")
    plt.close(fig)
    print("EBRO_07_ORIGINAL_CELL_RESULT",json.dumps({
        "first_step":chosen["substep"],"peak":peak,
        "max_each_step":[round(s["max_topography_after_transport_m"],2) for s in summaries]}))
if __name__=="__main__":main()
