# Experiment 02 numerical results — **PASS**

Successful GitHub Actions run: https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38139533984

Complete raw result artifact (expires after 30 days): https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38139533984/artifacts/11702094791

Upstream software: danigeos/tisc, pinned commit d18b7d270f4d671b80223e10dede329ad35cafdd.

## Author baseline reproduced without -T

| Grid | Author center w (m) | Calculated center w (m) | Absolute error |
|---|---:|---:|---:|
| 11 x 11 | 675.1 | 675.1 | 0.0 |
| 51 x 51 | 711.0 | 711.0 | 0.0 |

## One-factor Te sensitivity with the *same original square pressure load*

| Te (km) | Grid | Center w (m) | Maximum w (m) | Minimum w (m) | Width >= 50% max on central X profile (km) |
|---:|---:|---:|---:|---:|---:|
| 5 | 51 x 51 | 634.4 | 674.3 | -19.8 | 210 |
| 20 | 51 x 51 | 695.4 | 695.4 | -11.6 | 210 |
| 40 | 51 x 51 | 480.2 | 480.2 | 42.0 | 250 |
| 5 | 101 x 101 | 633.8 | 676.6 | -21.4 | 205 |
| 20 | 101 x 101 | 690.8 | 690.8 | -12.5 | 205 |
| 40 | 101 x 101 | 469.0 | 469.0 | 30.0 | 255 |

**Hard QC**: 8/8 calculations completed; 2/2 original author's center values reproduced; 51 and 101 coordinate grids each have identical applied pressure arrays across all three Te values; results are finite; Te-specific outputs differ; overall experiment status PASS.

## Interpretation

- Te=5 km: sharp-edged square-shaped flexure close to the load. The largest response occurs around model (x=-60 km, y=60 km), not at the center. The center value is only 634.4 m at 51 nodes.
- Te=20 km: smoother central deflection with largest value of 695.4 m *at the center* for 51 nodes.
- Te=40 km: still broader deflection; the entire modeled range has positive down-deflection (min 42.0 m, 51 nodes), and the center peak falls to 480.2 m.
- Unexpected result: **for this particular square pressure load and finite plate, center displacement is NOT monotonic as Te changes from 5 to 20 to 40 km**. Therefore Te should never be chosen by assuming that a thinner plate necessarily gives a larger center deflection at every node. Load footprint, where the metric is measured, boundaries, and elastic coupling matter.
- Grid refinement 51 -> 101 changes central responses by -0.6 m, -4.6 m, and -11.2 m respectively, suggesting reasonable but not identical numerical convergence. More resolution checks may be useful at high Te.
- The study only isolates **static elastic loading**; it says nothing yet about how many km of North Tianshan thrust shortening, how much erosion, or how much Junggar sediment fill TISC can generate.

## Provenance and reproducibility

Original unmodified pressure: upstream tisc/demo/2nd_example_load.xyp, identical within each grid verified cell-by-cell (pressure column). The only changed physical parameter is -T, interpreted by TISC in metres. All six solver stdout logs, the exact source checksum, two-character compile-only whitespace normalization report, original reference logs, pressure validation and plot data are available in the artifact. The small results CSV is committed permanently alongside this report. Full plotting source is tracked in scripts/qc_official_te_sensitivity.py.

**Next step**: apply the same strict one-factor approach to author's 6_tectonics example, in particular fault motion, ride=0 versus ride=1, unit age and block displacement. Preserve a raw official baseline first.
