# Controlled Ebro original-author three-arm longterm response (fourth heavy arm pending)

Real entire -60 to 0Ma forward runs, all complete 121 age labels, unlike the incomplete 2×2.
2016 historical is a saved original stdout log and **not** a runnable 2016 binary.

| Age | Historic 2016 max topo | 2017 solver + old grid | 2026 fixed + old grid | 2026 fixed + new grid |
|---|---:|---:|---:|---:|
| -59.5 | 1200.8 | 1190.9 | 1197.9 | 1521.6 |
| -50 | 3284.2 | 2027.9 | 2837.2 | 3483.5 |
| -35 | 6581.5 | 3246.7 | 4175.3 | 4822.3 |
| -30 | 8505.0 | 3157.2 | 5465.0 | 7483.6 |
| -20 | 5734.9 | 3945.1 | 5759.4 | 7283.2 |
| -10 | 7002.9 | 2222.5 | 3652.4 | 3914.0 |
| -0.5 | 7537.1 | 1872.9 | 3127.9 | 3311.6 |

## Inference allowed with these three complete results

2017 old to 2026 fixed on the same 2017 input isolates **source implementation plus inherited defaults**.
2026 fixed old to 2026 fixed new isolates **joint grid and dt_eros input differences**.
Do not separately attribute this difference solely to grid or solely to erosion time step.
The fourth source×input cross (2017 source on new fine grid) is required to compute a complete interaction effect.
2016 historical extrema are not physical calibration targets; integrated terrain and other outputs must be checked independently.

The source-controlled phase RMS and all 121 time-stage physical values are stored in machine-readable JSON/CSV.
