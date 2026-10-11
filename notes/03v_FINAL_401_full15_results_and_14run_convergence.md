# 03v FINAL PASS REPORT — 401×401 15 Myr and 14-group sensitivity results

**Date checked:** 2026-10-12. This is a science acceptance report for a modified, source-pinned version of the official synthetic `6_tectonics` demonstration. All five final workflow runs below have completed with **GitHub Actions success**.

## Source and comparisons

- Original reference source: `danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd`. The full 401 reference has original geological input files, Te, prescribed kinematics and original main `dt=.5 Myr`, erosional `dt_eros=.05 Myr`, plus the explicitly tracked 03g/03j acceleration, 03k numerical slope guard, and 03s/03t **observation/bookkeeping-only double ledger**.
- Candidate: **only `Sediment()` temporary `dh_sed` promoted from float to double**. Model grids `Blocks[].thick`, `ctx->topo`, deflection `w`, fluvial transfer and persisted/restart structures remain float. This is NOT a whole-model double-precision experiment and not an unmodified-author reproduction.

## Final 401 × 401, 0–15 Myr control: PASSED physically executable, FAILED criterion of low precision sensitivity

[Full N401 15 Myr paired run 38178743124](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178743124) **GitHub Actions success**, two independent executables both reached 15 Myr, original parameter file identical per pair; 30 corrected ledger records per variant.

| Field/QC | Float baseline | Local-double candidate | Absolute discrepancy or observation |
|---|---:|---:|---|
| Author time step | .5 Myr | .5 Myr | identical |
| Author surface step | .05 Myr | .05 Myr | identical |
| Max corrected mass-ledger residual | 0.0001675273% | 0.00007009892% | BOTH <0.001% |
| Maximum surface elevation over whole domain | 2349.5 m | 2346.0 m | extrema at different nodes; do not compare as local error |
| Minimum surface elevation | −432.3 m | −508.7 m | domain extrema |
| **Local maximum absolute surface elevation difference** | | | **722.8 m**, at (x=100, y=173.75) km in synthetic domain |
| **Spatial RMS surface elevation difference** | | | **48.0279 m** |
| Different *printed* terrain nodes | | | **156,283 / 160,801 = 97.2%** (includes 0.1m rounded differences) |
| Nodes with abs surface elevation difference >10m | | | ~22.12% |
| Nodes with abs surface elevation difference >100m | | | ~5.04% |
| Different direct downstream connections | | | **82,656 nodes** |
| Different drainage type (river/lake/outlet) | | | **4,715 nodes** |
| **Number of current lakes** | **126** | **164** | component membership differs substantially |
| **Local maximum abs sediment-unit thickness difference** | | | **~490 m**, at (x=111.25, y=75) km |
| **Spatial RMS output sediment thickness difference** | | | **~30.018 m** |
| Integrated output compacted sediment-thickness proxy | **~59,928.58 km³** | **~60,080.22 km³** | **~+0.253%** |

*Sediment thickness is reconstructed from `demo.hrz` upper sedimentary interfaces with 2200kg/m³ block tags, compacted at output, rounded to 0.1m and integrated at constant 1.25 km × 1.25 km spacing. The volume is **not un-compacted original sediment mass** and is not a substitute for comparing physically stored Block and mass ledger directly.*

**Important distinction:** two simulations can have nearly identical **integrated sediment volume** yet vastly different **where sediment accumulates**, changes to lakes, local relief and maximum layer thickness. A low global mass residual or similar total sediment volume is therefore insufficient to validate sediment-center predictions.

## True sub-step sensitivity and lake threshold

[Per-substep raw native state FNV audit, 121 and 401 grids 38179009871](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38179009871) passed both original-domain 401 and coarser 121 checks. Earliest observed native float state mismatch for **both grids**:

- Topography and last sedimentary Block thickness **t≈0.55 Myr**
- Plate deflection `w` **t≈2.05 Myr**
- Drainage / lake type or indexing / downstream link state **t≈2.55 Myr**
- In **401 original grid**, printed topographic difference already appears as 0.1m at t=1.5 Myr, while **real observable changed river/ lake component graph** first appears between 2.5 and 3.0 Myr: t=3.0 has **15 different downstream links and 5 changed drainage type nodes**, even though both have 138 lakes then. By 6Myr, there are 17,385 changed downstream links, with candidate lakes 534 vs reference 492.

These are measured chronology and associated changes, **not a causal proof** that particular lake toggling is the only amplification driver.

## 14-group spatial and temporal control completed: convergence NOT established

[14/14 GitHub Actions successful jobs 38178558812](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178558812) with archived full summary [03V_FINAL_GRID_TIMESTEP_14_GROUPS.csv](../results/03_tectonics/03V_FINAL_GRID_TIMESTEP_14_GROUPS.csv).

**At identical original dt=.5 / dt_eros=.05 and t=15 Myr, the RMS difference between local-double and float baseline as grids are refined is:**

| grid | paired RMS topo difference (m), original dt |
|---|---:|
| 81² | 43.7366 |
| 121² | 48.0548 |
| 201² | 68.5167 |
| 401² | 48.0279 |

It is **nonmonotonic**, so finer grid does not automatically eliminate precision sensitivity. This is a comparison **between precision variants at fixed grid**, not rigorous grid-to-grid convergence of one numerical scheme.

**At N401, t=2 Myr**, changing temporal resolution gives very different precision sensitivity:

| main dt / erosional dt Myr | paired topo RMS (m) | changed downstream link nodes | float-baseline compacted-sediment proxy (km³) |
|---|---:|---:|---:|
| .5 / .05 | 0.000432 | 0 | 2697.74 |
| .5 / .025 | 0.065653 | 99 | 2567.60 |
| .25 / .025 | 1.70509 | 1017 | 3348.49 |

**At N401, t=6 Myr**, baseline step .5/.05 yields RMS 15.412m and 17,385 changed edges; smaller step .25/.025 yields RMS **35.214m** and **25,413** changed edges. Again, reducing time step does **not** monotonically reduce precision-variant difference at original 401 grid.

This observation does not mathematically disprove asymptotic convergence as mesh → 0, dt → 0, but does not satisfy practical refinement stability for the geologic outputs tested. Also true solution convergence requires **grid-aligned physical observables (integrated load, volume, thickness and basin-scale loci) compared across runs of the SAME precision**, not just different precisions on each grid.

## Decisions and next gate

**Completed:** author official synthetic (x,y) tectonic flexure / erosion / sedimentation forward run with documented local fixes; 401/15Myr mass transaction QC; paired 401/15Myr local-precision sensitivity; 14/14 dt-grid controls; bit-level first divergent time and true lake membership bifurcation.

**Not established:** unmodified-original bitwise equality, full-64-bit physical model, stable original-grid long-time river/lake topology, absolute sediment thickness/grid convergence, or true Junggar tectonic-geological calibration.

**Prioritized next experiment:** focus on the **near-flat lake/outlet numerical decisions** around t2.5–3 Myr; identify first differing topo/Block cell and candidate flow tie, compare runoff/outlet and lake-filling discontinuities; trial a deterministic tolerance / local lake-routing stabilization as an explicitly separate physics alteration, with baseline paired mass checks and full 401/15 Myr before choosing a production TISC code. In parallel perform **same-scheme** grid-convergence checks on basin-scale sediment-volume maps and representative transects with aligned spatial averaging and extracted geological stages. 801² not currently warranted before mechanism isolation; cost rises ~4x storage at least, but no guarantee of meaningful accuracy.
