# 03z — Geographic micro-lake overflow saddle and local river routing sensitivity (2026-10-12)

**Status: real numerical experiments and continuous archival reports. No accepted TISC route algorithm has been changed.** Branch is isolated from [completed 03y](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38183870409). New 03z branch `v03z-local-lake-saddle-tests` maintains the known 03t mass-corrected reference and unchanged lake/river decision predicates. The prior global `1e-8` route-slope tolerance remains rejected.

## Question and two physically DISTINCT mechanisms

The earlier 03y showed that even a small finite-precision local calculation perturbation can amplify to different stream networks and sediment depocentres. It did NOT prove the lake-filling routine wrong. The focused 03z test separates:

1. **Instantaneous nearest-eight-neighbor derivative decisions** on real saved 401-grid t3Myr DEM, where precise `float32` values and empirical lake member/outlet flags are known;
2. **Original full hydrology and sediment transport of a controlled 41×41 two-sill lake** where exactly one starting topographic grid cell, not the source code, is perturbed.

Therefore no conflation between strict downhill route, lake-component membership, lake-outlet selection and subsequent sediment preservation.

## Test A — accepted original 401², t3Myr, real-snapshot local numerical replay — PASS

[Actions 38209933445](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38209933445), artifact `03Z_NATIVE_401_LOCAL_SADDLE_ULP_AUDIT`.

Paired input origin [03x 401 exact native float output 38183004799](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38183004799), case labels `reference` accepted 03t vs `optimized` local double `dh_sed` candidate. Four geographic points were tested:

| Selected synthetic-domain point (km) | Original node | Locally promoted `dh_sed` run | Why |
|---|---|---|---|
| (37.5, -246.25) | `L` lake member | `E` lake exit | actual south-rim outlet changes at t3Myr |
| (38.75, -247.5) | `E` lake exit | `R` river | adjacent outlet swaps classification |
| (-148.75, -246.25) | `R`, W/S alternative flow | `R`, changed downstream | flat-region equality and downhill choices |
| (-145, -185) | `R` to north | `R` to northeast | steepest-slope margin ~4.55×10^-10 dimensionless in reference |

The four 7×7 neighbourhoods were read from EACH of the 2 actual 401² runs, preserving genuine float32 stored precision. **360 frozen 1-cell ULP perturbations** (each candidate point ±1,±2 native ULPs, plus unchanged), applying the exact strict float32 derivative comparisons from `Define_Drainage_Net`:

- **6** one-cell/ULP tests change local strict steepest-descent direction.
- **13** change the number of adjacent slopes testing exactly zero.
- Reference (−145, −185) strict descent toggled on a height change of **one float32 ULP = 0.000007629 m**, i.e. 0.007629mm.
- Original lake component counts at t3 are 138/138, but original lake component node sets are **not identical** between the two source-preserving physical trajectories.
- Critically, lake nodes often have an assigned lake outlet whose pointer is **not** simply the nearest-eight-point steepest descending neighbour, e.g. at (37.5,−246.25) reference river's strict winner differs from lake-linked native downstream. Thus a regression test based only on `D8` path changes would miss lake functionality.

**Strict interpretation limit:** Test A is a **read-only final-frozen snapshot analysis**. Each ULP perturbation computes only a local derivative and negative/equal predicate; it does **not** re-simulate flow or update lake memberships, external water balance, sediment thickness, or TISC time evolution. It verifies exact local sensitivity of source predicates, not the root cause of the full 3 Myr plate simulation's earlier source of divergence.

## Test B — FULL real TISC 41×41 floating-precision dual-sill toy forward run — PASS

[Actions 38210167704](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38210167704), artifact `03Z_MICRO_41x41_ORIGINAL_TISC_DUAL_SADDLE`.

The accepted physical TISC 03t implementation (with the verified 03x **output-only** %.9g topography print), **unmodified** lake identification and routing, original author transport and isostatic parameters, no tectonic UNITs, 41×41 x 1km spacing over a 40×40km synthetic lake basin, identical `micro.PRM`, different single-cell `micro.ZINI` at artificially symmetric E/W notch cells (10km,20km) and (30km,20km). Full time 0–0.1Myr, `dt=0.05Myr`, `dt_eros=0.005Myr`; original initial ring basin has equal-height notches near 109m. 9 paired runs: unmodified TIE, four ±1 native float32 ULP variants and four mm/cm changes. **All 9 actual physics runs completed with corrected sediment budget QC pass** and scientifically finite output.

- Native lake count at t0.1Myr = **3** across all 9 runs; primary lake **222 nodes** and real outlet initially at (29km,20km), plus two small 2-node lakes near the E/W notches.
- ±1 ULP in a notch grid cell corresponds to ~7.629µm elevation (0.007629mm).
- Changing ONLY the notch cell by ±1 ULP, 1mm or 1cm in the chosen symmetrical DEM **did not change any final downstream graph connection or native lake outlet set**, despite tiny changes to local final topography. Two mm/cm trials exhibited very small (0.00244m) RMS sediment-horizon changes and ~1e-4 km³ integrated compacted output volume changes.
- This is an **important negative control**: not every near-level lake is numerically fragile, and a local D8 strict direction toggle does NOT automatically imply the full TISC lake outlet is unstable.
- Actual lake from `.lak` is **not** solely the initially chosen equal-height notch cell. The dominant lake outlets via (29km,20km) adjacent to the **lake entry throat**, so a symmetric notch perturbation probes an indirect route. That is why a second sweep below targets the physically controlling throat node instead.

## Test C — actual primary lake outlet throat-height sweep — running

[Actions 03z threshold sweep](https://github.com/lcxstar/tisc-mechanism-lab/actions/workflows/03z_micro_lake_sill_threshold.yml). Exact same 41×41 original physics and same original `micro.PRM`; change one original `.ZINI` cell only at **west lake-entry throat** (11km,20km) or **east throat** (29km,20km), leaving initial source topography and all other cells unchanged. Original two throat initial heights are equal (~114.16148m). West throat decreases by 0.00001,0.001,0.01,0.1,0.25,0.5,0.75,1,1.25,1.5,2,3,4m; east throat rises by 0.1,0.5,1,1.5,2,3m. Output precisely identifies the **largest lake's real outlet coordinates and member set** instead of comparing lake numeric labels, true flexure `w`, sediment thickness RMS and basin-integrated compacted sediment volume.

**Acceptance:** All original TISC forward cases reach 0.1Myr, `float32` ZINI values roundtrip correctly, every case has byte-identical PRM & no UNIT files, corrected independent sediment-budget max error <0.001%, and physical output valid. Only then identify if/where the primary outlet actually moves to a different destination. Do not claim a threshold before reading completed QC.

## Next scientific decision

- If changing the *actual lake throat* by a geologically interpretable centimetres or decimetres changes the primary outlet, the exact source of outlet choice is mainly **geometry / hydraulic topology near the saddle**, not necessarily a source-code error.
- If infinitesimal changes change the primary outlet in the full original physical solver, isolate the lake-cell membership order/equality comparisons and reproduce the same in a minimal source-level C harness. Arbitrary global slope margin is ruled out by completed 03y negative results.
- If no tested single-cell scenario changes the primary outlet even by several meters, the switch likely depends on multigrid morphology / lake-component overlap rather than single nominal notch height; design constrained two-cell or broad-spill crest tests, not global TISC changes.
- This synthetic experiment must not be used as a proxy geological reconstruction of Junggar. Existing Junggar full basin is 121×113 at 10km, requiring separate paleodivide/source-to-sink work before 5km mesh proof.
