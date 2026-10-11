# Experiment 03b — Why the exact official 401 × 401 tectonics run did not finish

## Confirmed failure from GitHub Actions

Latest unsuccessful full original case:
https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38140725340

The three independent original 401 × 401 attempts in Actions runs 38140532982,
38140607947 and 38140725340 terminated the TISC command with **exit code 124**.
That is the exit code of the workflow's explicit `timeout 1800` wrapper,
not a compiler error or a TISC-detected failed numerical solution.

Key evidence from raw TISC `RUN.log` and `CASE_QC.json`:

- Pinned official input files (PRM, two UNITs, PRFL) were copied byte-for-byte.
- TISC initialized and printed `T= 0.0000 My`, initial topography 100 m and sea-level information.
- The run never printed a completed `T= 0.5000 My` time step within 1800 s.
- The initial-grid `demo.xyzt` and `demo.hrz` output files exist, but they **do not** prove the calculation reached 15 Myr.
- Automatic QC correctly reported `numeric_pass = false`.
- `tisc.gmt.job not found` and `magick not found` were plotting utility warnings; they did **not** produce exit code 124.

## Why 401 is expensive

TISC's official documentation describes its elastic flexure solver as a banded matrix
method with runtime approximately proportional to `Nx × Ny × min(Nx,Ny)^2`.
For a square N × N grid, the scaling is approximately N^4. A 401-node side
therefore entails (401 / 81)^4 = **roughly 600 times** the core elastic solve
work of the 81 × 81 benchmark, before considering surface-process overhead.
The author also notes severe runtime costs with large flat drainage/lake areas.

We cannot infer from a stalled initial time step alone whether the dominant
cost was the **elastic solver** or **hydrology/sediment routing**. That is why
this experiment isolates the mechanisms rather than guessing.

## Precise diagnostic controls

All 401 experiments retain the **identical original demo.PRM, demo1.UNIT,
demo2.UNIT, demo.PRFL bytes**. Short simulations pass explicit command-line
overrides; they are **performance diagnosis, NOT a reproduction of the author's
complete coupled 0–15 Myr history**.

| Case | Changed computational conditions | What this isolates |
|---|---|---|
| N121_FULL | Nx=Ny=121 only; plotting disabled (nonphysical) | Can full 0–15 Myr run at modestly finer mesh? |
| N401_ISO_OFF | time 0–0.5, isost_model=0 | Performance of hydrology and sediment alone at 401 |
| N401_SURFACE_OFF | time 0–0.5, hydro_model=0, erosed_model=0 | Performance of static/tectonic elastic flexure alone at 401 |
| N401_BOTH_OFF | time 0–0.5, isost_model=0, hydro_model=0, erosed_model=0 | Minimal parser/time-loop overhead at 401 |

No upstream physical equations or constants were edited. As in earlier
experiments, the two illegal no-break spaces in C code are replaced solely
for GCC compilation.

TISC process exit codes and real wall seconds are captured in
`PERFORMANCE_QC.json`, explicitly recording partial progress and timeouts.
A successful performance-control case cannot be used to claim that the
full original 401 × 401 model has been reproduced.

[Actions diagnosis workflow](https://github.com/lcxstar/tisc-mechanism-lab/actions/workflows/03b_401_performance.yml)

## Computational policy

- Four 81 × 81 tectonic controls passed numerical QC and their summary data
  are permanently committed in `results/03_tectonics`.
- Do **not** automatically repeat 30-minute full original 401 trials on
  every change to tectonics QC or documentation. A more efficient strategy
  is to use 81 and 121 resolution while validating mechanisms.
- For a literal original 401 × 401 0–15 Myr reproduction, choose a
  capable HPC node with a known resource budget, or first validate a
  faster solver with numerical equivalence to the original. Simply raising
  GitHub Actions timeout is not a validated fix.


**Measured root-cause follow-up:** [full performance diagnosis](03b_401_performance_results.md) identifies active surface processes as the primary contributor to stalled 401-grid initial advancement, while keeping author input files byte-identical. Full-coupled 121 grid ends in 39.13 s but still logs nonfinite sediment outflow; mass-budget QC remains open.
