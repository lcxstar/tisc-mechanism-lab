#!/usr/bin/env python3
"""Read physical outputs of pinned author 6_tectonics, preserving raw results."""
from __future__ import annotations
import argparse,csv,json,re,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def last_value(pattern,block):
    z=re.search(pattern,block)
    return float(z.group(1)) if z else None

def time_series(log):
    markers=list(re.finditer(r"(?m)^\s*T=\s*([-+\d.eE]+)\s*My",log))
    rows=[]
    for i,m in enumerate(markers):
        part=log[m.end(): markers[i+1].start() if i+1<len(markers) else len(log)]
        rows.append({"time_Myr":float(m.group(1)),
          "topography_max_m":last_value(r"topogr\.\s*:\s*max\s*=\s*([-+\d.eE]+)",part),
          "topography_min_m":last_value(r"topogr\.\s*:\s*max\s*=\s*[-+\d.eE]+\s*m\s*min=\s*([-+\d.eE]+)",part),
          "deflection_max_m":last_value(r"deflect\.\s*:\s*max\s*=\s*([-+\d.eE]+)",part),
          "deflection_min_m":last_value(r"deflect\.\s*:\s*max\s*=\s*[-+\d.eE]+\s*m\s*min=\s*([-+\d.eE]+)",part),
          "sediment_volume_km3":last_value(r"sediment vol:\s*([-+\d.eE]+)\s*km3",part),
          "erosion_rate_max_mm_yr":last_value(r"eros-sed\.\s*:\s*max=\s*([-+\d.eE]+)\s*mm/yr",part)
        })
    return rows

def final_blocks(log):
    m=list(re.finditer(r"(?m)^\s*(\d+)\s+Blocks:",log))
    if not m:return []
    tail=log[m[-1].end():]
    rows=[]
    for line in tail.splitlines():
        p=re.match(r"^\s*(\d+):\s+(.+)",line)
        if not p:continue
        tok=p.group(2).split()
        if len(tok)<8:continue
        try:
            rows.append({"block_id":int(p.group(1)),"density_kg_m3":float(tok[0]),
              "age_Myr":float(tok[1]),"volume_1000km3":float(tok[2]),
              "surface_1000km2":float(tok[3]),
              "velocity_x_km_Myr":float(tok[4]),"velocity_y_km_Myr":float(tok[5]),
              "shift_x_km":float(tok[6]),"shift_y_km":float(tok[7]),
              "raw_block_row":p.group(0)})
        except (ValueError,IndexError):continue
    return rows

def main(path):
    path=Path(path)
    audit=json.loads((path/"INPUT_AUDIT.json").read_text())
    n=audit["grid"]
    log=(path/"RUN.log").read_text(errors="replace") if (path/"RUN.log").exists() else ""
    code=int((path/"EXIT_CODE.txt").read_text().strip()) if (path/"EXIT_CODE.txt").exists() else -999
    steps=time_series(log)
    blocks=final_blocks(log)
    profile_file=path/"demo.xyzt"
    summary={"case":audit["case"],"grid":n,"timespan_Myr":[0,15],
      "actual_exit_code":code, "last_logged_time_Myr":steps[-1]["time_Myr"] if steps else None,
      "n_steps":len(steps),"final_block_count":len(blocks),
      "number_of_author_unit_files":len(list(path.glob("demo[0-9]*.UNIT"))),
      "end_time_log_present":"Time end:" in log,
      "has_xyzt":profile_file.exists(),"has_hrz":(path/"demo.hrz").exists(),
      "has_final_drainage":(path/"demo.xyw").exists(),"output_finite":False,
      "original_inputs_byte_exact":audit["case"]=="original_401",
      "numeric_pass":False}
    for name,rows in (("STEP_DIAGNOSTICS.csv",steps),("FINAL_BLOCKS.csv",blocks)):
        if rows:
            with (path/name).open("w",newline="") as f:
                wr=csv.DictWriter(f,fieldnames=list(rows[0]))
                wr.writeheader();wr.writerows(rows)
    if profile_file.exists():
        try:
            a=np.loadtxt(profile_file,comments="#")
            if a.ndim!=2 or a.shape[0]!=n*n or a.shape[1]<4 or a.shape[1]%2:
                raise ValueError(f"Unexpected xyzt shape={a.shape}")
            if not np.isfinite(a).all():raise ValueError("nonfinite displacement")
            f=a[:,-2]
            summary.update({"output_finite":True,"xyzt_columns":int(a.shape[1]),
              "final_downward_w_max_m":float(f.max()),
              "final_downward_w_min_m":float(f.min()),
              "final_downward_w_mean_m":float(f.mean()),
              "final_center_w_m":float(f[n*n//2])})
            grid=a.reshape(n,n,a.shape[1])
            mid=n//2
            with (path/"CENTERLINE_DEFLECTION.csv").open("w",newline="") as h:
                wr=csv.writer(h);wr.writerow(["x_km","y_km","final_deflection_w_m"])
                for val in grid[mid,:,:][:,[0,1,-2]]:wr.writerow(val)
            fig,axs=plt.subplots(1,2,figsize=(13,5.2),constrained_layout=True)
            im=axs[0].imshow(grid[:,:,-2],cmap="RdBu_r",origin="upper",
                  extent=[-150,350,-250,250])
            fig.colorbar(im,ax=axs[0],shrink=.75,label="w (m)")
            axs[0].set(title="Final TISC elastic deflection",xlabel="X (km)",ylabel="Y (km)")
            axs[1].plot(grid[mid,:,0],grid[mid,:,-2])
            axs[1].set(title="Final deflection at Y=0",xlabel="X (km)",ylabel="w (m)")
            axs[1].grid(alpha=.25)
            fig.suptitle("Official 6_tectonics | "+audit["case"])
            fig.savefig(path/"FINAL_DEFLECTION.png",dpi=150)
            plt.close(fig)
        except Exception as exc:summary["xyzt_read_error"]=str(exc)

    xyw=path/"demo.xyw"
    if xyw.exists():
        try:
            x=np.loadtxt(xyw,usecols=(0,1,5),comments="#")
            if x.shape!=(n*n,3) or not np.isfinite(x).all():raise ValueError(f"Invalid xyw {x.shape}")
            summary.update({"final_topography_max_m":float(x[:,2].max()),
              "final_topography_min_m":float(x[:,2].min()),
              "final_topography_mean_m":float(x[:,2].mean())})
        except Exception as exc:summary["xyw_read_error"]=str(exc)
    # Check time at 15 Myr with tolerance one 0.5 Myr model increment.
    summary["numeric_pass"]=bool(code==0 and summary["output_finite"]
      and summary["has_hrz"] and summary["end_time_log_present"]
      and summary["last_logged_time_Myr"] is not None
      and abs(summary["last_logged_time_Myr"]-15)<=.6)
    (path/"CASE_QC.json").write_text(json.dumps(summary,indent=2,allow_nan=False))
    print(json.dumps(summary,indent=2,allow_nan=False))
    if not summary["numeric_pass"]:raise SystemExit("Case did not pass numeric gates.")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("case_directory")
    args=ap.parse_args()
    main(args.case_directory)
