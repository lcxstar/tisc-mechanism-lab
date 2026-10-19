#!/usr/bin/env python3
"""Public, strictly synthetic TISC fault-sign benchmark. No field data.

Two opposite velocity signs on the SAME dipping planar fault versus no-fault
control. This screens whether an input produces observable kinematic/topographic
response; it does not presuppose a physically valid normal-fault solution.
"""
import argparse
import csv
import hashlib
import json
import re
import shutil
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream/tisc/demo/6_tectonics"
DEST = ROOT / "work_synthetic_fault"
CASES = {"control": 0, "slip_positive": 5, "slip_negative": -5}
GRID = (61, 11)  # 300 km by 100 km; dx=5 km, dy=10 km
SOURCE = "d18b7d270f4d671b80223e10dede329ad35cafdd"


def param(text, key, old, new):
    pattern = rf"(?m)^({re.escape(key)}\s+){re.escape(str(old))}(?=\s|$)"
    result, n = re.subn(pattern, lambda m: m.group(1) + str(new), text)
    if n != 1:
        raise ValueError(f"Expected exactly one parameter {key}={old}; got {n}")
    return result


def prepare():
    raw = (UPSTREAM / "demo.PRM").read_text(encoding="latin-1")
    edits = [
        ("Nx", "401", "61"), ("Ny", "401", "11"),
        ("xmax", "3.5e+05", "1.5e+05"),
        ("ymin", "-2.5e+05", "-5.0e+04"),
        ("ymax", "2.5e+05", "5.0e+04"),
        ("Timefinal", "15", "2"),
        ("dt_record", "5", "1"),
        ("hydro_model", "1", "0"),
        ("erosed_model", "6", "0"),
        ("water_load", "1", "0")
    ]
    for k, old, new in edits:
        raw = param(raw, k, old, new)
    # Author's original PRM, otherwise unchanged; no observed geometry.
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    audit = {
        "dataset": "SYNTHETIC ONLY; no Junggar or proprietary information",
        "upstream_commit": SOURCE,
        "base_project": "tisc/demo/6_tectonics",
        "grid_Nx_Ny": list(GRID),
        "spacing_km_xy": [5, 10],
        "time_Myr": [0, 2],
        "initial_topography": "flat 100 m (official PRM parameter)",
        "disabled_for_isolation": ["hydrology", "surface erosion/sediment transport", "water load"],
        "fault": "One identical hypothetical west-dipping shallow-to-deep 0-to-4km surface",
        "motions_km_per_Myr": CASES,
        "time_stop_Myr": 1.5,
        "hypothesis": "An opposite velocity sign might NOT implement normal-fault accommodation",
    }
    for case, velocity in CASES.items():
        directory = DEST / case
        directory.mkdir()
        (directory / "demo.PRM").write_text(raw, encoding="latin-1")
        shutil.copy2(UPSTREAM / "demo.PRFL", directory / "demo.PRFL")
        if velocity:
            fault = [
                "# Fully synthetic fault sign test: NOT a mapped fault or validated normal fault",
                "time 0", "fault 1", f"vel_x {velocity}", "vel_y 0",
                "time_stop 1.5", "ride 0", "cut_units 0", "cut_all 0",
                "gradual 0", "hidden 0", "move 0",
                "z_default -1000000", "mode_interp 4", "z_absol 0",
                "# Shallow 0-m reference polygon; x=-200..0 km, y=-75..75 km",
                "0",
                "-200000 -75000", "0 -75000", "0 75000", "-200000 75000",
                "# Deep 4000-m reference polygon; the same synthetic west-side block",
                "4000",
                "-200000 -75000", "-40000 -75000",
                "-40000 75000", "-200000 75000",
            ]
            (directory / "demo1.UNIT").write_text("\n".join(fault) + "\n")
        with (directory / "INPUTS.sha256").open("w") as f:
            for p in sorted(directory.glob("demo*")):
                f.write(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n")
    (DEST / "EXPERIMENT_AUDIT.json").write_text(json.dumps(audit, indent=2))
    print(json.dumps(audit, indent=2))


def block_rows(log):
    markers = list(re.finditer(r"(?m)^\s*(\d+)\s+Blocks:", log))
    if not markers:
        return []
    text = log[markers[-1].end():]
    out = []
    for line in text.splitlines():
        m = re.match(r"^\s*(\d+):\s+(.+)", line)
        if not m:
            continue
        z = m.group(2).split()
        if len(z) < 8:
            continue
        try:
            out.append({"id": int(m.group(1)), "density": float(z[0]),
                        "velocity_x_km_Myr": float(z[4]),
                        "shift_x_km": float(z[6]), "shift_y_km": float(z[7])})
        except ValueError:
            continue
    return out


def read_case(case):
    directory = DEST / case
    log = (directory / "RUN.log").read_text(errors="replace")
    code = int((directory / "EXIT_CODE.txt").read_text().strip())
    datafile = directory / "demo.xyzt"
    result = {"case": case, "exit_code": code, "has_xyzt": datafile.exists(),
              "has_horizon": (directory / "demo.hrz").exists(),
              "end_time_detected": "Time end:" in log,
              "final_blocks": block_rows(log),
              "outp_seds_nan_reported": "outp_seds: -nan" in log}
    times = [float(x) for x in re.findall(r"(?m)^T=\s*([-+\d.]+)\s+My", log)]
    result["final_logged_time_Myr"] = times[-1] if times else None
    if code != 0 or not datafile.exists():
        raise RuntimeError(f"{case}: TISC did not complete. Exit={code}")
    dat = np.loadtxt(datafile, comments="#")
    if dat.shape != (GRID[0]*GRID[1], 5) or not np.isfinite(dat).all():
        raise ValueError(f"{case}: unexpected/nonfinite xyzt {dat.shape}")
    # Use stable topography columns from author's native demo.xyzt:
    # x, y, elastic downward deflection, deflection-rate, elevation.
    center_y = dat[:, 1]
    ys = np.unique(np.round(center_y, 5))
    midy = ys[np.argmin(np.abs(ys))]
    centerline = dat[np.isclose(center_y, midy)]
    centerline = centerline[np.argsort(centerline[:, 0])]
    x = centerline[:, 0]
    # Coordinates are kept in exactly the units supplied by native TISC;
    # don't infer km vs m when comparing spatial regions.
    scale = 1.0 if max(abs(x.min()), abs(x.max())) < 1000 else 1000.0
    xkm = x / scale
    if not (np.isclose(xkm.min(), -150, atol=1) and np.isclose(xkm.max(), 150, atol=1)):
        raise ValueError(f"{case}: unexpected cross section X range {x.min(), x.max()}")
    if centerline.shape[0] != GRID[0]:
        raise ValueError(f"{case}: unexpected centerline size {centerline.shape}")
    np.savetxt(directory / "CENTERLINE_NATIVE.csv",
               np.column_stack((xkm, centerline[:, 2], centerline[:, 4])),
               delimiter=",", comments="",
               header="x_km,deflection_downward_m,topography_m", fmt="%.6f")
    result.update({
        "output_finite": True,
        "topo_min_m": float(dat[:, 4].min()),
        "topo_max_m": float(dat[:, 4].max()),
        "w_min_m": float(dat[:, 2].min()),
        "w_max_m": float(dat[:, 2].max()),
        "topo_left_mean_m": float(centerline[xkm < -30, 4].mean()),
        "topo_right_mean_m": float(centerline[xkm > 30, 4].mean()),
        "native_west_to_east_topo_difference_m":
            float(centerline[xkm > 30, 4].mean() - centerline[xkm < -30, 4].mean()),
    })
    if result["final_logged_time_Myr"] is None or abs(result["final_logged_time_Myr"] - 2) > 0.51:
        raise ValueError(f"{case}: wrong endpoint: {result['final_logged_time_Myr']}")
    (directory / "CASE_QC.json").write_text(json.dumps(result, indent=2))
    return result, xkm, centerline[:, 2].copy(), centerline[:, 4].copy()


def compare():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output = [read_case(name) for name in CASES]
    base = output[0][3]
    base_w = output[0][2]
    summary = []
    fig, axs = plt.subplots(2, 1, figsize=(9, 7), sharex=True, layout="constrained")
    for (result, xx, ww, elev), case in zip(output, CASES):
        de = elev-base
        dw = ww-base_w
        result["delta_vs_control_min_m"] = float(de.min())
        result["delta_vs_control_max_m"] = float(de.max())
        result["delta_vs_control_left_mean_m"] = float(de[xx < -30].mean())
        result["delta_vs_control_right_mean_m"] = float(de[xx > 30].mean())
        result["delta_vs_control_deflection_min_m"] = float(dw.min())
        result["delta_vs_control_deflection_max_m"] = float(dw.max())
        (DEST / case / "CASE_QC.json").write_text(json.dumps(result, indent=2))
        axs[0].plot(xx, de, label=case)
        axs[1].plot(xx, dw, label=case)
        summary.append(result)
    axs[0].axvline(0, ls=":", color="0.5")
    axs[0].set_ylabel("Topography minus control (m)")
    axs[1].set_ylabel("Downward deflection minus control (m)")
    axs[1].set_xlabel("Synthetic X (km), center line")
    for ax in axs:
        ax.grid(alpha=0.2)
        ax.legend()
    fig.suptitle("Synthetic TISC fault sign test: NOT validated extension")
    fig.savefig(DEST/"SYNTHETIC_FAULT_SIGN_COMPARISON.png", dpi=150)
    (DEST / "SUMMARY.json").write_text(json.dumps(summary, indent=2))
    fields = ["case", "exit_code", "final_logged_time_Myr", "topo_min_m", "topo_max_m",
              "w_min_m", "w_max_m", "delta_vs_control_min_m",
              "delta_vs_control_max_m", "delta_vs_control_left_mean_m",
              "delta_vs_control_right_mean_m",
              "delta_vs_control_deflection_min_m", "delta_vs_control_deflection_max_m",
              "outp_seds_nan_reported"]
    with (DEST / "SUMMARY.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summary)
    print(json.dumps(summary, indent=2))
    print("NUMERICAL PASS: native computations and centerline comparisons completed")
    print("PHYSICAL NORMAL FAULT PASS: NOT CERTIFIED. Must verify actual block slip and hangingwall geometry.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["prepare", "compare"])
    args = ap.parse_args()
    {"prepare": prepare, "compare": compare}[args.mode]()
