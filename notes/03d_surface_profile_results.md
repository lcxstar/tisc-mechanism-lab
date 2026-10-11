# Experiment 03d — Measured first 401x401 surface bottleneck

**Date:** 2026-10-11. **Result:** The 401-grid first-step delay enters
`Define_Drainage_Net()` before `Calculate_Discharge()` or the separate
post-discharge equal-height reorder. This is an observed active function,
not yet the root-cause line within the function.

- [Successful tracing workflow #38147766529](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38147766529)
- [Raw timing, JSON, input audits, source diffs and 121/401 logs](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38147766529/artifacts/11705620556)
- Exact pinned source: `danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd`.
- Exactly copied PRM, UNIT1, UNIT2 and PRFL for 401x401, checked against SHA256.
- **DIAGNOSTIC source build**, not a byte-exact original executable. Source changed only to emit wall-clock stage timing; exact patch preserved in artifacts. Previous two-byte whitespace normalization remains compile-only.
- Command in both cases: `tisc demo -V1 -tf0.5 -qisost_model=0 -qplotting_mode=0`. Thus flexure and plotting are disabled to isolate water/surface processes, and history is cut to the first 0–0.5 Myr step. These cases are **not** the author's full 0–15 Myr reproduction.

## Observations

| First step | 121x121 (14,641 nodes) | 401x401 (160,801 nodes) |
|---|---|---|
| Whole command | exited 0, advanced to 0.5 Myr in ~14 s | exited 124 after controlled 180-s timeout, stayed at 0.0 Myr |
| `ReSort_Matrix` topography sort | all 10 calls completed in ~0.0011 s | first call completed in **0.029923 s** |
| `Define_Drainage_Net` | all 10 calls completed in **5.081545 s** | entered first call, **no END within 180 s** |
| `Calculate_Discharge` | all 10 calls completed in **7.333783 s** | **not reached** |
| Outer post-discharge equal-height reorder | all 10 calls completed in **1.492867 s** | **not reached** |
| `Fluvial_Transport` | all 10 calls completed in **0.00798 s** | **not reached** |

Caution: timing for completed 121 calls adds per-step wall time. The 401
drainage-network duration is a lower bound, not a measured finished duration.
Some nested group events in 03d share a common start time and must not be
summed as independent subroutine costs.

**Physical explanation not yet determined.** Inspection of pinned
`surf_proc.c` confirms `Define_Drainage_Net()` itself performs lake-node
creation, lake merging, outlet assignment, and another internal
equal-height sorting pass. Therefore one cannot yet conclude whether the
critical hotspot is lake allocation/merging, the ascending node sweep,
the function's internal flat-node reordering, or its final validation.

## Follow-on

The separate [03e nested drainage workflow](../.github/workflows/03e_drainage_internal_profile.yml)
adds timed markers for lake reset, ascending node scan and progress, lake
finalization, internal equal-height sorting and final checks. Any changed
source is explicitly diagnostic and is archived with a full diff and hashes.

Only after identifying the responsible inner stage should any separate
performance-optimized upstream derivative be attempted and verified against
the author's numerics on smaller grids. No edits to geologic loads, Te,
tectonic velocities, hydrology or erosion physics should be made as a
shortcut. Sediment conservation is independently unresolved because of
nonfinite `outp_seds` in completed smaller grids.
