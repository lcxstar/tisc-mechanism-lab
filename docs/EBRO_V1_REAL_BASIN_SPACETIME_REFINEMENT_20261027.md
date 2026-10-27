# Public real-Ebro native refinement study — 2026-10-27

## Official real geographic examples

This public laboratory reproduces exactly two distinct author examples with a **real named geographic region**, not just an idealized teaching geometry:

1. `8_Ebro_evol` — Ebro Basin, Pyrenees, Iberian Ranges and Catalan Coastal Ranges, real **regional tectonic, hydrological, and sedimentary evolution**, age -60 to 0 Ma.
2. `9_Iberian_drainage` — Iberian Peninsula **present-day river and drainage network** on real geography. Not a real tectonic sedimentary 60 Ma evolution model.

The 1–7 official examples (flexural loads, conic island, idealized lakes, synthetic deformation, climate) illustrate physics; do not label them calibrated geological reconstructions. The separate upstream `tAo` cross-section code has illustrative Zagros material but is **not** an additional completed real 3-D TISC basin case in this public laboratory.

## Original author's current Ebro geometry and timing

`danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd`; original author `tisc/demo/8_Ebro_evol/Ebro_evol.PRM`, `Ebro_evol1–5.UNIT`, `Ebro_evol.ZINI`, `Ebro_evol.SLV`, etc. `xmin=-48160,xmax=660573,ymin=0,ymax=500000` m. Original `Nx=208 Ny=110 dt=0.5Myr dt_eros=0.05Myr`. Preserve the entire physical input domain and exact tectonic input hashes for all tests. Maintain nodes at the same domain edge positions. Strict twofold *node-coincident* refinement is `(Nx-1)*2+1=415`, `(Ny-1)*2+1=219`, not 416×220.

## Native solver

All new tests use pinned original 2026 TISC with:
- portability-only NBSP normalization;
- **independently verified V08 salt_model=0 physics gate** (necessary because original upstream source spuriously deposits salt when chemistry is disabled);
- four isolated V3 performance changes to sorts, lake evaporation calculation, outlet scans and lake membership.
- Separate **V08-only without V3** controls for large-grid peak causality.
- No Junggar private data, fault geometries or author original geological coefficients changed.

Source, build logs, original inputs with SHA256, native .xyw and other output, status JSON, diagnostic peak locations and actual map PNG/PDF live in GitHub Actions artifacts.

## Completed original first 0.5 Myr factorial (all solver native exit 0, age -59.5 Ma)

| Experiment | Nx×Ny | dt (Myr) | dt_eros (Myr) | First-stage maximum height (m) | Cell count >3000 m |
|---|---|---:|---:|---:|---:|
| original | 208×110 | 0.5 | 0.05 | 1521.6 | 0 |
| time_only | 208×110 | 0.25 | 0.025 | 1777.1 | 0 |
| space_only | 415×219 | 0.5 | 0.05 | 1766.2 | 0 |
| refined | 415×219 | 0.25 | 0.025 | 12410.9 | 8 |
| space_dt_only | 415×219 | 0.25 | 0.05 | 14454.8 | 4 |
| space_eros_only | 415×219 | 0.5 | 0.025 | 10757.1 | 16 |
| moderate_both | 312×165 | 0.25 | 0.025 | 1203.7 | 0 |

Actual runs: [4-factor sensitivity #40472472638](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/40472472638), [additional three refinements #40473083122](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/40473083122).

The 415×219 numerical extremes are **isolated spurious peaks**, not basin-wide mountain uplift. The maximum 12,410.9-m node at original-model-local `(624.62,222.48)` km has direct eight neighboring elevations predominantly **151–256 m**. The highest 99.99th percentile is only 1,204.2 m in the 415×219 refined test. Mean elevation stays near 335 m. The 1.5x-grid moderate-both test has a contiguous topography peak ~1204 m with nearby neighbors ~1174–1202m, and no isolated nodes above 3000m.

The severe full-2x spikes are **NOT attributable to V3 speed patches alone**: an entirely separate pinned **V08-only original sorting, drainage, and lake solver** (no V3 optimization) reproduced the same maximum 12,410.9 m and identical eight extreme peak coordinates at 415×219/dt.25/dt_eros.025. The V08-only mean was 334.9407526m versus optimized 334.9407735m; water-discharge maxima differed (499.16 vs 499.57 m³/s), therefore there is NOT yet proven full-byte physical identity for V3 at Ebro, even though extreme peak placement agrees. [Independent V08-only controls #40472743933](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/40472743933).

**A model can exit 0 and render a map and still have numerically/geologically pathological cells.** Never smooth away these spikes and claim convergence. The large-grid instability, specific node correlation with fault geometry / lake boundaries, and full 60-Myr mass budget remain unresolved.

## Full 60-Myr candidate: separate work, no premature claim

The conservative numerical candidate `moderate_both` is **312×165**, fixed domain ~709×500km, horizontal spacing 2.279km × 3.049km, and `dt=0.25Myr; dt_eros=0.025Myr` over -60–0 Ma. It is not an exactly node-coincident strict factor-two grid, but it uses identical original-author geological parameters and coordinate boundaries. The native first 0.5-Myr test passes a robust extreme-height screen. A separate [full 60 Ma original-vs-moderate workflow](https://github.com/lcxstar/tisc-mechanism-lab/actions/workflows/ebro_v1_full60_moderate_forward.yml) is issued, but full historical simulation, source–sink physical validity and geological calibration **MUST be reported only after actual native process completion**. The GitHub workflow treats final-age `0 Ma` and unphysical >5000m peaks as independent gates; source outputs and failure logs are preserved.

The original author's 2016 Ebro simulation and its exact binary source remain unavailable. Prior full runs in the public V08/V09 branches show strong disagreement in maximum topography between 2016 historical printed output and reproducible 2017/2026 source. Refining the 2026 numerical grid does not by itself resolve this fundamental historical-geological discrepancy.

## Correct plot semantics

- `.xyw` column 3 is water discharge, column 4 sediment flux, column 5 drainage node class, **column 6 actual terrain [m]**.
- X/Y are native model coordinates, **not latitude/longitude**; plots are labeled local km and must not be directly georeferenced without independent control points or a verified CRS.
- Full-history stage snapshots / paleorelief / sediment thickness maps require reading authoritative native age-specific outputs or deliberately saving selected-age runs. A final native `.xyw` map alone is not a multi-stage geological reconstruction.
- The plot/postprocessing script in this branch regenerates native terrain planviews from actual new TISC executions, not previous low-resolution maps resampled by interpolation.
