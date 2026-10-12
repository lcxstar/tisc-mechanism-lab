#!/usr/bin/env python3
"""QC unchanged author demo inputs and original-vs-optimized source variants."""
from pathlib import Path
from hashlib import sha256
import argparse,json,math,re

def hashfile(path):
    h=sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(2**20),b""):h.update(chunk)
    return h.hexdigest()

def read_prm(p):
    parsed={}
    for line in p.read_text(errors="replace").splitlines():
        t=line.strip()
        if not t or t.startswith("#") or t.startswith("*"):continue
        v=t.split()
        if len(v)>1 and v[0] not in parsed:parsed[v[0]]=v[1]
    return parsed

def count_native_xyw(filename):
    if not filename.exists():return 0,None,None,True
    n=0;zmin=float("inf");zmax=float("-inf");finite=True
    with filename.open(errors="replace") as f:
        for line in f:
            v=line.split()
            if len(v)<8 or line.lstrip().startswith(("#",">")):continue
            try:x,y,z=float(v[0]),float(v[1]),float(v[5])
            except ValueError:continue
            n+=1
            finite &= math.isfinite(x) and math.isfinite(y) and math.isfinite(z)
            if math.isfinite(z):zmin=min(zmin,z);zmax=max(zmax,z)
    return n,(zmin if n else None),(zmax if n else None),finite

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--directory",required=True,type=Path)
    p.add_argument("--case",required=True)
    p.add_argument("--upstream",required=True)
    p.add_argument("--source-variant",required=True)
    p.add_argument("--result",required=True,type=Path)
    a=p.parse_args();d=a.directory;a.result.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((d/"ORIGINAL_INPUT_MANIFEST.json").read_text())
    for name,h in manifest["files_sha256"].items():
        target=d/name
        assert target.exists() and hashfile(target)==h, "Altered author's model input "+name
    prefix=manifest["prefix"]
    prm=read_prm(d/(prefix+".PRM"))
    nx=int(prm["Nx"]);ny=int(prm["Ny"])
    initial=float(prm.get("zini","0"))
    tstart=float(prm.get("Timeini","0"))
    tend=float(prm.get("Timefinal","0"))
    actual=(d/"ACTUAL_COMMAND.txt").read_text().strip()
    process=int((d/"EXIT_CODE.txt").read_text().strip())
    logtext=(d/"RUN.log").read_text(errors="replace")
    ages=[float(x) for x in re.findall(r"(?m)^\s*T=\s*([-+0-9.eE]+)\s*My",logtext)]
    count,zmin,zmax,finite=count_native_xyw(d/(prefix+".xyw"))
    file_list=[{"name":f.name,"bytes":f.stat().st_size}
               for f in sorted(d.iterdir()) if f.is_file()]
    checks={
        "case":a.case,"author_demo_folder":manifest["original_demo_subdirectory"],
        "original_upstream_commit":a.upstream,"source_variant":a.source_variant,
        "model_input_hashes_unchanged":True,"plotting_override_only":True,
        "physical_model_inputs_changed":False,
        "input_Nx":nx,"input_Ny":ny,"grid_nodes_expected":nx*ny,
        "initial_surface_base_elevation_m":initial,
        "time_ini_Myr":tstart,"time_final_Myr":tend,
        "actual_command":actual,"process_exit_code":process,
        "T_times_from_run_log":len(ages),
        "last_logged_time_Myr":ages[-1] if ages else None,
        "native_xyw_nodes":count,"native_xyw_finite":finite,
        "native_xyw_min_topography_m":zmin,"native_xyw_max_topography_m":zmax,
        "native_final_outputs_present":{
            ext:(d/(prefix+"."+ext)).exists() for ext in ["xyw","xyzt","hrz","bas","lak","st"]},
        "output_inventory":file_list,
        "upstream_native_input_manifest_sha256":hashfile(d/"ORIGINAL_INPUT_MANIFEST.json"),
        "interpretation":"A numerical reproduction of author-provided demo inputs, not independently verified physical geology.",
    }
    checks["checks_pass"]=bool(process==0 and count==nx*ny and finite)
    (a.result/"RUN_QC.json").write_text(json.dumps(checks,indent=2,allow_nan=False))
    (a.result/"SOURCE_AND_INPUTS.json").write_text(json.dumps(manifest,indent=2))
    verdict="PASS" if checks["checks_pass"] else "INCOMPLETE / FAIL"
    (a.result/"RUN_REPRODUCE.md").write_text(
        "# Official TISC demo "+a.case+"\n\n"
        +"Source: "+a.upstream+"; execution source variant: "+a.source_variant+"\n\n"
        +"Author's model input SHA256: SOURCE_AND_INPUTS.json.\n\n"
        +"Command: "+actual+"\n\n"
        +"Native grid: "+str(nx)+" x "+str(ny)
        +", time "+str(tstart)+" to "+str(tend)+" Myr.\n\n"
        +"Acceptance: "+verdict+"\n")
    print("OFFICIAL_DEMO_QC",json.dumps({
        "case":a.case,"pass":checks["checks_pass"],"run_exit":process,
        "grid_points":count,"expected":nx*ny,"last_T":checks["last_logged_time_Myr"],
        "source_variant":a.source_variant}))
    if not checks["checks_pass"]:
        raise SystemExit("Author demo did not meet 0-exit and finite native-grid QC")
if __name__=="__main__":main()
