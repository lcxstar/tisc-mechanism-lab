#!/usr/bin/env python3
"""03aa: compare original TISC forward results of mirror-paired unique low lake throats.

All physical tests run independently. Failure to mirror is scientific output,
NOT evidence of a code bug until source ordering/lake evolution is isolated.
"""
from pathlib import Path
import csv
import json
import math
import re
import sys
import numpy as np

root = Path(sys.argv[1])
spec = json.loads((root / "INPUT_SPEC.json").read_text())
assert spec["all_input_pairs_exact_bitwise_float32_EW_mirrors"]
cases = [arm["name"] for arm in spec["experiments"]]
side = 40.0
def key(x, y):
    return (round(float(x), 3), round(float(y), 3))
def mirror(k):
    return key(side-k[0], k[1])
def mirror_pointer(p):
    if 0 <= p[0] <= side and 0 <= p[1] <= side:
        return mirror(p)
    return p
def read_outlets(path):
    lakes, current = [], None
    for s in path.read_text(errors="replace").splitlines():
        if s.startswith(">Lake "):
            current = {"members":set(), "outlets":set()}
            lakes.append(current)
        elif current is not None and s.strip() and not s.startswith("#"):
            a = s.split()
            if len(a) > 2:
                try:
                    pos = key(a[0], a[1])
                except ValueError:
                    continue
                current["members"].add(pos)
                if a[2] == "E":
                    current["outlets"].add(pos)
    assert lakes, f"No lake objects parsed from {path}"
    dominant = max(lakes, key=lambda l: len(l["members"]))
    return dominant, len(lakes)
def read_case(name):
    d = root / name
    assert (d / "EXIT_CODE.txt").read_text().strip() == "0", f"failed solver {name}"
    log = (d / "RUN.log").read_text(errors="replace")
    last_times = [float(x) for x in re.findall(r"(?m)^\s*T=\s*(\d+(?:\.\d+)?)\s*My", log)]
    assert last_times and abs(last_times[-1]-.1) < 1e-5, f"wrong simulation horizon {name}"
    errors = [abs(float(x)) for x in re.findall(
        r"TISC_03T_CORRECTED_BALANCE[^\n]*balance_pct=([^\s]+)", log)]
    assert errors and max(errors) < .001, f"mass ledger QC {name}"
    xyw = {}
    for s in (d / "micro.xyw").read_text(errors="replace").splitlines():
        if s.startswith("#") or not s.strip():
            continue
        a = s.split()
        pos = key(a[0], a[1])
        xyw[pos] = {"topo":float(a[5]), "kind":a[4], "down":key(a[6],a[7])}
    assert len(xyw) == 1681, f"bad native grid {name}"
    wdata = np.loadtxt(d / "micro.xyzt", comments="#")
    assert wdata.shape == (1681,5)
    flex = {key(row[0],row[1]):float(row[2]) for row in wdata}
    with (d/"micro.hrz").open() as f:
        f.readline()
        hdr = f.readline()
    dens = [float(x) for x in hdr.split("Dens:")[1].split("water")[0].split()]
    hrz = np.loadtxt(d / "micro.hrz", skiprows=2)
    assert hrz.shape[0] == 1681
    thick = np.diff(hrz[:,2:], axis=1)
    selected = np.isclose(dens[1:],2200)
    assert len(selected) == thick.shape[1] and np.any(selected)
    deposited = np.maximum(0,thick[:,selected]).sum(axis=1)
    sed = {key(row[0],row[1]):float(h) for row,h in zip(hrz,deposited)}
    assert set(xyw) == set(flex) == set(sed)
    vol = 0.0
    for (x,y),h in sed.items():
        wx = .5 if x in (0.,40.) else 1.
        wy = .5 if y in (0.,40.) else 1.
        vol += wx*wy*h/1000.0
    lake, n_lakes = read_outlets(d / "micro.lak")
    return {"xyw":xyw,"flex":flex,"sed":sed,"lake":lake,
            "n_lakes":n_lakes, "vol":vol,"max_mass_error_pct":max(errors)}
result = {name:read_case(name) for name in cases}
pairs = []
for strength in ("ULP1","0p1m","1m"):
    wa, ea = result["W_LOW_"+strength], result["E_LOW_"+strength]
    keys = sorted(wa["xyw"])
    assert {mirror(k) for k in keys} == set(ea["xyw"])
    dif_top, dif_sed, dif_w = [], [], []
    different_down, different_class = 0,0
    mismatched_downstream_nodes = []
    for k in keys:
        vk, ve = wa["xyw"][k], ea["xyw"][mirror(k)]
        dif_top.append(vk["topo"]-ve["topo"])
        dif_sed.append(wa["sed"][k]-ea["sed"][mirror(k)])
        dif_w.append(wa["flex"][k]-ea["flex"][mirror(k)])
        if mirror_pointer(vk["down"]) != ve["down"]:
            different_down += 1
            mismatched_downstream_nodes.append(dict(west_node=k, mirrored_east_node=mirror(k),
                west_class=vk["kind"],east_class=ve["kind"],
                expected_east_destination=mirror_pointer(vk["down"]),
                actual_east_destination=ve["down"]))
        different_class += vk["kind"] != ve["kind"]
    wout = wa["lake"]["outlets"]
    eout = ea["lake"]["outlets"]
    mirrored_wout = {mirror(k) for k in wout}
    mirrored_wmembers = {mirror(k) for k in wa["lake"]["members"]}
    rms = lambda a: float(np.sqrt(np.mean(np.square(np.array(a,float)))))
    pairs.append(dict(strength=strength, west_original_main_outlets=str(sorted(wout)),
        east_original_main_outlets=str(sorted(eout)),
        actual_main_outlets_mirror_equal=mirrored_wout==eout,
        actual_main_lake_members_mirror_equal=mirrored_wmembers==ea["lake"]["members"],
        west_lake_count=wa["n_lakes"],east_lake_count=ea["n_lakes"],
        changed_reflected_downstream_nodes=different_down,
        exact_reflected_downstream_mismatches=str(mismatched_downstream_nodes),
        changed_reflected_node_types=different_class,
        reflected_topography_RMS_m=rms(dif_top),
        reflected_sediment_thickness_RMS_m=rms(dif_sed),
        reflected_true_flexure_w_RMS_m=rms(dif_w),
        west_deposition_km3=wa["vol"],east_deposition_km3=ea["vol"],
        west_minus_east_deposition_km3=wa["vol"]-ea["vol"],
        max_corrected_mass_residual_percent=max(wa["max_mass_error_pct"],ea["max_mass_error_pct"])))
assert len(pairs)==3 and len(result)==7
out=root/"03AA_RESULTS"
out.mkdir(exist_ok=True)
with (out/"03AA_MIRRORED_UNIQUE_SILL_QC.csv").open("w",newline="") as f:
    wr=csv.DictWriter(f,fieldnames=list(pairs[0]))
    wr.writeheader()
    wr.writerows(pairs)
summary={"status":"all seven original TISC physical runs and independent mass QC passed",
    "physical_solver_modified":False,
    "mirrored_input_float32_exact":True,
    "paired_results":pairs,
    "baseline_tie_main_outlets":str(sorted(result["TIE"]["lake"]["outlets"])),
    "interpretation":"A failed mirror-outlet equality is an observation requiring source-level isolation, not automatic evidence of a bug or geology."}
(out/"03AA_MIRRORED_UNIQUE_SILL_QC.json").write_text(json.dumps(summary,indent=2))
print("03AA_MIRROR_PHYSICAL_QC",json.dumps(summary))
