# Experiment 03e — Internal drainage-network bottleneck at 401x401

**Date:** 2026-10-11. **Measured result:** the original 401x401
`6_tectonics` demo is not hanging in topographic sorting or post-discharge
sediment transport at its first step. Its **first** call of
`Define_Drainage_Net` spends most of its time in the ascending,
per-grid-node lake/network identification sweep.

## Provenance and reproducibility

- [GitHub Actions run 38148228724](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38148228724), workflow status SUCCESS, which denotes successful profiling, NOT a completed full TISC history.
- [Diagnostic artifact with complete log and audited C source diffs](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38148228724/artifacts/11705820761).
- Permanent observed progress [CSV](../results/03_tectonics/DRAINAGE_401_PROGRESS_03E.csv).
- Pinned author source `danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd`.
- Author `demo.PRM`, `demo.PRFL`, `demo1.UNIT` and `demo2.UNIT` copied without modification and verified by SHA256.
- **Temporary diagnostic source was instrumented**, so executable bytes differ from upstream; source patch, before/after hashes and normalization audit preserved.
- Diagnostic runtime overrides: `-tf0.5 -qisost_model=0 -qplotting_mode=0`. Hydrology and erosion input choices remain the author's. This tests the first 0–0.5 Myr step, not the original complete 0–15 Myr coupled model.

## Instrumented results

| Operation or progress milestone | Observed wall time |
|---|---:|
| Initial topography sort, 160,801 nodes | 0.030134 s (finished) |
| Lake/reset setup in drainage-network builder | 0.000725 s (finished) |
| 50,208 nodes processed in initial ascending node sweep | 6.867904 s |
| 99,360 nodes processed | 39.272168 s |
| 119,840 nodes processed | 85.652318 s |
| 136,224 nodes processed | 113.763200 s |
| Drainage node scan overall | **no END before 120 s timeout** |
| Subsequent lake finalization, internal flat sorting and final checks | NOT REACHED |
| Discharge and fluvial sediment transport | NOT REACHED |

Exit code `124` is imposed by the diagnostic timeout. The model time did
not advance past 0 Myr, and neither numerical completion nor sediment
conservation has been established. Approximately 85% of the grid nodes
had been reached at the last progress marker (136,224 / 160,801), so
**the source is making progress rather than proven to be deadlocked.**

The processing cost increases dramatically with node count. The first
~50,000 nodes need under 7 s, while reaching ~136,000 nodes needs over
113 s. This is compatible with costly repeated lake-list operations, but
these aggregate timings do not yet isolate a single library routine.

## Source-level causes to test, not yet proven by direct profiling

The original `surf_proc.c` includes these potentially superlinear data
structures inside the measured node-identification loop.

- `New_Lake()` grows the global lake array with one `realloc` per newly created lake (original `surf_proc.c` near lines 3214–3234).
- `Add_Node_To_Lake()` linearly searches existing nodes for duplicates and repeatedly reallocates the row/column arrays (near lines 2482–2514).
- `Unify_Lakes()` re-adds every node from one lake to another by calling `Add_Node_To_Lake()` (near lines 3238–3259).
- In the author demo, initial topography is uniform 100 m. Large connected flats generate many lake and union operations. These operations are a **strong candidate** for the observed increase but must be confirmed with call counts/timings before altering algorithms.

## Scientific and engineering next step

Time the actual `Add_Node_To_Lake`, `Unify_Lakes` and `New_Lake` calls
without emitting a log line on every call, and save aggregated call counts,
total elapsed time and largest lake size every several thousand nodes.
Then, if a clear bottleneck is established, implement a separately
tagged performance patch and compare the original and patched outputs
at 81x81 and 121x121 by numerical arrays, stage state and sediment
budgets. Do not modify geological parameters or use this result to claim
the full official 401x401 example has been reproduced.
