# Full 60-Myr Ebro audit — 2016 archived screen versus real 2017 and 2026 solver×input factorial

**All four source×input original author forward simulations have completed and passed numerical and native-grid QC.**
 The upstream 2026 source has ONLY the minimal V08 salt_model=0 patch (plus whitespace compilation fix), not 03t optimization. The older 2017 source is original (modern toolchain compatibility flags).

| Era / pairing | 2017 Ebro inputs 104×55 | 2026 Ebro inputs 208×110 |
|---|---|---|
| Original 2017 source | **OO** | ON |
| 2026 source + V08 salt gate | NO | **NN** |

The author 2016 reference is an archived **historical log**, not a compiled executable; therefore the source effect here is a **source-plus-inherited-default effect**. The 2003 paper is not assumed to use either input snapshot.

## Original input SHA256 provenance

Geological UNIT, ZINI and SLV files unchanged byte-for-byte between the two source checkouts: **True**.
Differences in PRM include grid size and erosion substep; other files are inventoried in V09_ORIGINAL_AUTHOR_INPUT_DIFF_MANIFEST.csv and textual diffs.

## Actual time-series residual RMS by tectonic/sedimentary age stage

| Age window | Records | OO zmax RMS | ON zmax RMS | NO zmax RMS | NN zmax RMS |
|---|---:|---:|---:|---:|---:|
| -60 to -48 Ma | 24 | 585.9 | 368.6 | 175.7 | 366.5 |
| -48 to -35 Ma | 26 | 2290.5 | 1326.3 | 1368.9 | 802.0 |
| -35 to -23.5 Ma | 23 | 4873.9 | 3022.2 | 2663.6 | 2080.2 |
| -23.5 to -12.5 Ma | 22 | 4925.0 | 3726.3 | 3140.0 | 2162.0 |
| -12.5 to -8 Ma | 9 | 4746.2 | 4181.9 | 3286.2 | 2970.6 |
| -8 to 0 Ma | 16 | 5200.1 | 4850.5 | 3917.1 | 3862.5 |

## Key stage topography and sediment overview

| Time | 2016 original (m) | OO (m) | ON (m) | NO (m) | NN (m) | V08 optimized-fixed (m) |
|---|---:|---:|---:|---:|---:|---:|
| initial | 1200.8 | 1190.9 | 1376.2 | 1197.9 | 1521.6 | 1521.6 |
| minus50 | 3284.2 | 2027.9 | 3164.4 | 2837.2 | 3483.5 | 3483.5 |
| minus35 | 6581.5 | 3246.7 | 4313.7 | 4175.3 | 4822.3 | 4822.3 |
| minus30 | 8505.0 | 3157.2 | 6935.6 | 5465.0 | 7483.6 | 7483.6 |
| minus23_5 | 9365.5 | 2804.4 | 3877.6 | 4639.7 | 5809.7 | 5809.7 |
| minus20 | 5734.9 | 3945.1 | 4620.0 | 5759.4 | 7283.2 | 7283.2 |
| minus12_5 | 6828.0 | 2254.7 | 3004.5 | 3808.5 | 4343.7 | 4343.7 |
| minus10 | 7002.9 | 2222.5 | 2728.2 | 3652.4 | 3914.0 | 3914.0 |
| minus8 | 7129.3 | 2909.2 | 2626.7 | 3723.2 | 3684.4 | 3684.4 |
| last_-0_5 | 7537.1 | 1872.9 | 2283.8 | 3127.9 | 3311.6 | 3311.6 |

## Scientific interpretation guards

1. These are global TISC *maximum topography and printed sediment volume*; not foredeep accommodation, sedimentary wedges, basin mean height or fixed-cell topographic cross sections.
2. The 2017 and 2026 source implementations have other differences including **inherited defaults**; a solver×input contrast does not isolate one line of C code by itself.
3. Printed sediment volume accounting may vary in implementation; use it first as a code-diagnostic metric, not an observational sediment mass balance.
4. These independent model comparisons have only the actual native final-grid archive and age-by-age logged scalar physical metrics, not full 3D palaeogeography at every age. Do not imply cell-level evolution is known at all time steps.
5. The 2026 source V09 is clean source + V08 salt-gate; the separately completed V08 optimized-03t + salt-gate full run is a third implementation variant, and its differences are reported but not silently pooled.

**Next work:** follow the first geological interval at which OO and 2016 historical values diverge most, then inspect the exact source functions controlling the matching field (structural topographic load, stratigraphic sediment, hydrology or lake routing); avoid global parameter tuning.
