# 03h — New 401-grid bottleneck after validated fast lake merge

**Date:** 2026-10-11. **Measured status:** the verified 03g performance optimization fixes the previously pathological original lake-node duplicate search, but it does **not** yet complete the author's 401² `6_tectonics` first 0–0.5 Myr history.

## Reference and audit

- [03g original vs optimized four-pair PASS (81²/121²)](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38152768335).
- [03g optimized 401 first-step artifact](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38152768335/artifacts/11706859188). Controlled 480-s process timeout, exit code 124, last model time 0.0 Myr. Green GitHub workflow means completed diagnostic, **not completed model**.
- [03h 401 stage trace](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38153223479).
- [03h full timing artifact / source diffs](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38153223479/artifacts/11707950045).
- Fixed original TISC commit `d18b7d270f4d671b80223e10dede329ad35cafdd`; original PRM/UNIT/PRFL inputs exact SHA256 copy, physical overrides only `-tf0.5 -qisost_model=0 -qplotting_mode=0`.
- 03h temporary executable combines the reviewed 03g membership optimization plus timing probes. Original reference and geological input files are preserved in the original repository; `main` has not been modified.

## Timed 401² stages in 03h

| Stage | Observation |
|---|---|
| Topographic sort | 2 completed calls totaling 0.03189 s |
| `Define_Drainage_Net` inner ascending node scan | **4.452350 s** (largest of 2 completed calls, all 160,801 nodes) |
| `Define_Drainage_Net` whole function | **8.861618 s** (largest of 2 completed calls) |
| `Calculate_Discharge` first completed call (substep 0) | **77.830661 s** |
| `Calculate_Discharge` second call (substep 1) | Entered, **not complete by 150-s diagnostic timeout** |
| Post-discharge equal-height reorder | First call 0.000653 s |
| Fluvial transport | First call 0.008133 s |
| Process exit | 124 due to deliberate 150-s cap |
| Model time | Still 0.0 Myr; **first 0.5 Myr timestep NOT complete** |

Original unoptimized pinned source 03e at 401² processed only 136,224 / 160,801 lake nodes by 113.763 seconds and had not completed its FIRST node scan at the 120-s timeout. The optimized source completes the entire same class of node scan in ~4.45 s in 03h. Comparing different hosted runners and 03e vs 03h timing probes is approximate, so this supports a large removal of the initial bottleneck, **not** a precisely calibrated whole-model speedup.

## Source-level explanation to investigate next

The new first-order bottleneck is original author `Calculate_Discharge` (in `tisc/src/surf_proc.c`). Within its per-cell loop, it recomputes lake-wide evaporative flux for each lake node, and in outlet cases also iterates over `Lake[il].n` and calls `Lake_Input_Discharge`. On the original 100-m flat-topography initial surface, one lake can contain a large fraction of 160,801 nodes. Repeated per-node lake sums are a **credible O(N²) hypothesis**, not yet isolated by per-inner-loop timings.

Next verification should count and time the following subexpressions inside `Calculate_Discharge` without altering physics:
- per-lake evaporation summation over `Lake[il].n`;
- each `Lake_Input_Discharge` invocation;
- lake outlet `E` processing, and any lake deletion/recalculation.

Then test an explicitly tagged per-lake cached evaporation total, invalidated whenever lake membership/evaporation changes, and compare 81²/121² deterministic output fields against the author before retrying 401². Do not modify physical runoff, climate, erosion or tectonics parameters as a shortcut.

## Physical/scientific boundary

Full author 401² 0–15 Myr reproduction is **not complete**. Even 81/121 full histories have a separate original `outp_seds: -nan` problem requiring sediment-budget diagnosis. No conclusion about mass conservation should be derived from the green Actions run.
