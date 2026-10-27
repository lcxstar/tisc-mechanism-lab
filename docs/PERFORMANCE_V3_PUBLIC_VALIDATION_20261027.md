# Public TISC V3 performance experiment (2026-10-27)

This branch stages the transferable **solver-only** performance candidates first tested separately in the private Junggar modelling laboratory. It deliberately contains **no private Junggar geometry, constraints, experimental input decks, file paths, or output data**.

## Experiment controls

- Upstream author and license: Daniel García-Castellanos and contributors; [danigeos/tisc](https://github.com/danigeos/tisc), GPL-3.0 code. Official solver fixed at commit `d18b7d270f4d671b80223e10dede329ad35cafdd`.
- Build and compare **two separate binaries** within a temporary GitHub Actions runner: (a) the pinned source with a strictly whitespace-only portability normalization, and (b) identical source plus four explicitly listed speed candidates.
- The candidate source is patched **only in a CI checkout**. Neither the official upstream GitHub repository nor this laboratory's original solver or `main` is replaced.
- Official author demo `6_tectonics`: identical physical inputs for the reference and candidate; independent N81/N121 grids, first 0.5 Myr isolation and complete 0–15 Myr forward runs.
- Strict QC requires native return code 0, matching model ages, identical deterministic field files (`.st`, `.hrz`, `.xyw`, `.xyzt`, `.pfl`, `.bas`, `.lak` when present), finite expected hydrology fields and equal input hashes. Raw `.all` includes C pointers and padding, so bytes alone cannot prove restart equivalence.
- Workflow status MUST NOT be read as a scientific pass unless `VALIDATION_QC.json` confirms `numerical_equivalence_pass: true`. Any diagnostic timeout must be reported as native exit 124 and cannot be called completion.

## Four experimental changes

1. `patch_tisc_stable_sort_v3.py`: replace original insertion sort with **stable** mergesort, preserving equal-elevation ordering.
2. `patch_tisc_lake_evap_v3.py`: reuse per-lake evaporation sums with invalidation after lake mutation; short-circuit a zero-evaporation condition only under original nonnegative inflow assumptions.
3. `patch_tisc_outlet_scan_v3.py`: skip lake sweeps at elevations where no outlet was inserted.
4. `patch_tisc_lake_membership_v3.py`: avoid re-scanning a lake for an unrelated node, retaining the original duplicate check for nodes already marked with that lake.

These candidates were carried over as source patches, NOT certified physical models. Private 23–0 Ma tests included project-specific V74/V65 patches and C0/C1 geologic inputs; those results **do not substitute for** tests with the clean author's demos. The public demo can have very different evaporation, outlet, tectonic and lake-merge patterns.

## Validation plan and release gate

Run the four N81/N121 reference–candidate pairs under `.github/workflows/performance_v3_official_demo_regression.yml`. Archive input hashes, both native logs, every deterministic output, exact-file comparisons, source revision and wall times. If all four pass, run a 401×401 official demo first-step benchmark with an explicit native timeout; only after further full-size/history and sediment-budget checks consider publishing a separate verified optimized derivative.

**Not changed:** PRM coefficients, EET, ZINI, tectonic UNIT, erosion law, climate forcing, timestep, floating-point precision, boundary modes or upstream Git history.

See historic independent [03g benchmark](https://github.com/lcxstar/tisc-mechanism-lab/tree/v03g-fast-lake-merge-validation) for the previously validated merge-stamp candidate; the V3 branch intentionally re-tests the newer combined implementation.