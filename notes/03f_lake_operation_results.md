# Experiment 03f — Quantified cost of lake-node duplicate scans

**Date:** 11 October 2026. **Status:** instrumentation runs completed and archived. The two 401x401 first-step tests timed out deliberately. **This is not a completed official 401x401 0–15 Myr reproduction.**

## Evidence

- [First 03f run #38149226002](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38149226002) contains a complete 401-grid profile and a 121-grid successful numerical run whose initial CSV summary parser incorrectly expected globally monotonic node counts.
- [Second 03f run #38149385843](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38149385843) fixes the report parser to recognize 10 water-routing substeps per model time step. Both profiling jobs and the final CSV and JSON generation succeed.
- [Permanent 03f numeric summaries](../results/03_tectonics/LAKE_03F_SUMMARY.csv).
- [Permanent 401-grid progression data from first run, 36 snapshots](../results/03_tectonics/LAKE_401_PROGRESS_03F.csv).
- Original GitHub Actions artifacts also preserve the actual full `RUN.log`, per-call sampled CSV, per-interval sampled CSV, input hashes, and full C source diffs; their retention is 30 days.

## Actual measurements

| Item | 121x121, complete 0–0.5 Myr (10 surface substeps) | 401x401 first run, interrupted | 401x401 repeat, interrupted |
|---|---:|---:|---:|
| Nodes reached in last scan | 14,641 / 14,641 | 144,416 / 160,801 | 156,704 / 160,801 |
| Add_Node_To_Lake calls | 1,776,916 | 8,957,749 | 10,327,263 |
| Duplicate nodes detected | 0 | 0 | 0 |
| Time in Add_Node_To_Lake (all operations) | 2.260184 s | 137.404451 s | 132.730656 s |
| **Linear duplicate search inside Add_Node_To_Lake** | **2.070742 s** | **136.039505 s** | **131.630049 s** |
| realloc of lake node arrays | 0.061660 s | 0.457922 s | 0.407664 s |
| Unify_Lakes calls | 270 | 126 | 135 |
| Node re-additions during merging | 1,630,736 | 8,813,333 | 10,170,559 |
| Unify_Lakes inclusive wall time | 2.044510 s | 134.480645 s | 130.053296 s |
| New_Lake calls | 340 | 143 | 143 |
| New_Lake total wall time | 0.000039 s | 0.000021 s | 0.000015 s |
| Execution | exit 0, first time step complete | exit 124, 140-s cutoff | exit 124, 140-s cutoff |

The 401 run's profile reports the completed portions of its first scan only. When the 140-second cutoff interrupts a function, no final unprinted timing remainder is attributed.

## Key finding

**The dominant measured bottleneck is the O(current-lake-size) duplicate-node search in Add_Node_To_Lake(), amplified by mass re-insertion during Unify_Lakes().** In the 401 repeat, over **98% of all Add_Node_To_Lake calls** were caused by merging nodes into other lakes (10,170,559 / 10,327,263). More than 99% of observed Add_Node_To_Lake time was spent scanning lists for duplicates (131.630 / 132.731 s), not reallocating arrays (~0.408 s).

The 121 run similarly executed 1.78 million add calls during its first time step, despite having only 14,641 grid nodes. For the 401 first run, 50,208 processed nodes already incurred 6.90 s of duplicate searching, 99,360 nodes incurred 39.35 s, and 144,416 nodes incurred 136.04 s. The increasing cost is directly measured.

Do NOT add Unify_Lakes time to Add_Node_To_Lake time; the former includes the latter. Also avoid treating two wall times on different GitHub runners as deterministic benchmark durations. The instrumentation itself adds clock calls.

## Provenance and scientific limits

- Original author: `danigeos/tisc` at exact commit `d18b7d270f4d671b80223e10dede329ad35cafdd`.
- The original 401-grid demo PRM/UNIT/PRFL files are copied byte-for-byte (SHA256 verified). The 121 grid changes only Nx/Ny.
- Actual runtime override for both sizes: `-tf0.5 -qisost_model=0 -qplotting_mode=0`. These disable flexure and plotting and stop at the first time step, while hydrology/erosion settings remain from the author.
- Temporary C code has **diagnostic timing inserts** beyond the compile-only NBSP normalization; compiled executable therefore is **not** byte-for-byte original. All changes are documented as diffs. No physical parameter or mathematical step is intentionally changed.
- These measurements are an engineering diagnosis, not a validated sediment history. The earlier independent problem of `outp_seds: -nan` remains unresolved.

## Next benchmark (03g), not yet implemented

1. Preserve this original slow solver as the numerical reference. Build a clearly named, separately tagged `performance-patched` branch rather than silently changing the teaching baseline.
2. Replace only the expensive linear duplicate-membership check, preferably with an O(1) node membership/index check that preserves duplicate detection even across lake merges. Simply deleting the check because 03f saw no duplicates is **not** acceptable without tests.
3. On 81 and 121 grids, compare original versus optimized run for each model stage, node-to-lake membership, lake outflow, block displacements, topography, flexure and sediment mass values; require explained numerical differences and no newly introduced NaNs.
4. Benchmark first 401-grid hydrology step with identical physical inputs; only then rerun complete coupled 401x401 0–15 Myr and solve the separate sediment mass-budget failure.
