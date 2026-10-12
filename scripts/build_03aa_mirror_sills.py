#!/usr/bin/env python3
"""03aa: generate E/W exact-mirror, unique-controlling-throat inlet DEM pairs.
Input DEM generator is original accepted 03z TIE. Physical TISC source remains unchanged.
"""
from pathlib import Path
import csv
import hashlib
import json
import sys
import numpy as np

if len(sys.argv) != 2:
    raise SystemExit("python scripts/build_03aa_mirror_sills.py ROOT_WITH_03Z_TIE")
root = Path(sys.argv[1])
tie = root / "TIE"
assert (tie / "micro.ZINI").exists()
prm = (tie / "micro.PRM").read_bytes()
zini_lines = (tie / "micro.ZINI").read_text().splitlines()
base = np.array([float(z) for z in zini_lines[3:]], dtype=np.float32).reshape(41, 41)
assert base.shape == (41, 41)
assert np.array_equal(base, np.fliplr(base)), "TIE input is not bitwise east-west symmetric"
wpos, epos = (20, 11), (20, 29)
assert base[wpos] == base[epos], "Inner throat is not equal-height baseline"
base_sha = hashlib.sha256(prm).hexdigest()
names = [("TIE", "none", 0.0)]
for strength, delta in (("ULP1", "ulp"), ("0p1m", 0.1), ("1m", 1.0)):
    for side in ("W", "E"):
        names.append((side + "_LOW_" + strength, side, delta))
rows = []
inputs = {}
for name, side, dheight in names:
    target = tie if name == "TIE" else root / name
    a = base.copy()
    if side != "none":
        idx = wpos if side == "W" else epos
        if dheight == "ulp":
            a[idx] = np.nextafter(a[idx], np.float32(-np.inf))
        else:
            a[idx] = np.float32(a[idx] - float(dheight))
        target.mkdir(parents=True, exist_ok=True)
        (target / "micro.PRM").write_bytes(prm)
        (target / "micro.ZINI").write_text(
            zini_lines[0] + "\nmode_interp 6\nz_default 0\n" +
            "".join(f"{float(z):.9g}\n" for z in a.ravel()), encoding="ascii")
    assert (target / "micro.PRM").read_bytes() == prm
    nums = [float(x) for x in (target / "micro.ZINI").read_text().splitlines()[3:]]
    assert np.array_equal(np.array(nums, dtype=np.float32).reshape(41, 41), a)
    inputs[name] = a
    rows.append(dict(name=name, branch=side, requested_decrement=str(dheight),
        true_west_throat_m=float(a[wpos]), true_east_throat_m=float(a[epos]),
        west_minus_east_m=float(a[wpos]) - float(a[epos]),
        PRM_sha256=base_sha,
        ZINI_sha256=hashlib.sha256((target / "micro.ZINI").read_bytes()).hexdigest()))
for strength in ("ULP1", "0p1m", "1m"):
    w = inputs["W_LOW_" + strength]
    e = inputs["E_LOW_" + strength]
    assert np.array_equal(np.fliplr(w), e), "Failed bitwise float32 mirror-input gate"
with (root / "INPUT_TABLE.csv").open("w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0]))
    wr.writeheader()
    wr.writerows(rows)
(root / "INPUT_SPEC.json").write_text(json.dumps({
    "stage":"03aa", "author_source_original":True,
    "physical_change":"only a single ZINI inner throat cell per arm",
    "grid":[41,41], "grid_spacing_m":1000, "horizon_Myr":0.1,
    "mirror_axis_x_km":20, "same_prm_sha256":base_sha,
    "all_input_pairs_exact_bitwise_float32_EW_mirrors":True,
    "experiments":rows}, indent=2))
print("03AA_INPUT_QC", json.dumps({"cases":len(rows),"same_prm":True,
      "exact_EW_pairs":True,"baseline_throat_m":float(base[wpos])}))
