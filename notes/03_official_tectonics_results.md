# Official TISC 6_tectonics — results from controlled 81x81 tests

**Numerical status:** Four same-grid cases completed and passed QC (0–15 Myr, 31 logged steps, finite 5-column demo.xyzt, outputs demo.hrz and demo.xyw, clean exit code 0).

Source: the official danigeos/tisc commit d18b7d270f4d671b80223e10dede329ad35cafdd, demo/6_tectonics. Physical parameters were unchanged except for the explicitly documented perturbations. Original author's full 401x401 version is tracked separately and is **not** claimed to have completed in this four-case summary.

Successful run (control cases): https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38140725340

## Permanent data files

- [Full numerical endpoint table](../results/03_tectonics/CASE_SUMMARY.csv)
- [Actual fault-block displacements, using ages and block IDs](../results/03_tectonics/FAULT_BLOCK_SHIFTS.csv)
- [Selected intermediate stages (5, 6, 10, 12 Myr)](../results/03_tectonics/STAGE_SNAPSHOTS.csv)
- Every step's raw log, five-column demo.xyzt (x, y, flexural w, w-rate, topo), drainage demo.xyw, final horizons demo.hrz, and individual input files with SHA256 are saved as GitHub Actions per-case artifacts. Full artifacts are available for 30 days, separate from the permanently committed numeric CSV and scripts.

## What has been proven

1. The author's second fault starts at t=6 Myr, and the first two models' stage diagnostics, including initial controls, are identical through t=6 Myr.
2. Same-resolution baseline (second fault ride=1): first fault-associated block shifts +125 km, second fault-associated block +62.5 km, center downward flexure at 15 Myr = 2,034.3 m, highest domain relief = 1,689.0 m.
3. Changing ONLY ride=1 to ride=0 in second UNIT: first block shift reduces to 100.0 km while second stays 62.5 km; center flexure reduces to 1,535.7 m. Therefore ride influences other overlying Blocks and the loading architecture, not just the position of the newest fault.
4. Changing ONLY second fault vel_x from 10 to 5 km/Myr under ride=1 yields final shifts 93.8 km (first) and 31.2 km (second), and center flexure 1,479.1 m.
5. Removing the second UNIT removes the second fault block altogether; the first shifts 100 km and final center flexure is 1,190.6 m.
6. Grid Nx=Ny=81 across all controlled cases means node spacing is 6.25 km. Actual fault shifts are integer multiples of 6.25 km; do not interpret prescribed velocity multiplied by time as an exact continuous shift.
7. Removing the second fault is an **event omission** test, not a one-parameter comparison. And the author's unmodified original 401x401 case must be analyzed separately: its finer node spacing can produce quantitatively different results.

## Quantitative results

| Case | First fault Block displacement (km) | Second fault Block displacement (km) | Final center w (m) | Final domain maximum topography (m) |
|---|---:|---:|---:|---:|
| baseline_81, ride=1 | 125.0 | 62.5 | 2034.3 | 1689.0 |
| ride0_81 | 100.0 | 62.5 | 1535.7 | 1507.1 |
| slow2_81 | 93.8 | 31.2 | 1479.1 | 1105.5 |
| no2_81 | 100.0 | – | 1190.6 | 1118.7 |

**Physical caution.** Center elastic deflection is NOT total tectonic subsidence nor sediment thickness. Topographic uplift and relief involve fault kinematics, loading and surface transport. Before calibrating the North Tianshan, we need cross-sections that distinguish imposed fault geometry, Block motion and resulting flexure rather than only final elevation maps.

## Provenance

Experiment code: scripts/prepare_official_tectonics.py, scripts/qc_official_tectonics.py, scripts/compare_official_tectonics.py. Input source was copied byte-for-byte for the literal 401 run and decoded in Latin-1 only when creating modified 81-node PRM or UNIT text; physical parameter edits are audited in INPUT_AUDIT.json. The pinned source contains two nonstandard whitespace bytes normalized solely for GCC compilation.
