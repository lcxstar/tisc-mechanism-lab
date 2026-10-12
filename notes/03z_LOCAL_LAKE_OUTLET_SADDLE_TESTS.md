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

## Completed Test C — pinned original TISC main-lake outlet saddle threshold sweep, 20/20 PASS

[Actions run 38210578478](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38210578478) **COMPLETED SUCCESS** after fixing an audit-file key mismatch that had made earlier [run 38210494464](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38210494464) appear failed despite completing all original physics simulations. The audit correction is *only* the analysis metadata lookup, not C source, numerics or geology. Successful run archive `03Z_MICRO_41x41_TRUE_OUTLET_SADDLE_THRESHOLD` ID 11728493161 includes each of 20 independent original `.PRM`, `.ZINI`, raw `.xyw`, `.lak`, `.hrz`, `.xyzt`, log, exit code, source diffs, JSON QC. [Permanent 20-case scientific outcome CSV](../results/03_tectonics/03Z_LAKE_THROAT_20CASE_SCIENCE.csv).

**Strong first-order result from ACTUAL lake code:**

| Indicator | Exact equal-throat base | West throat lowered by 1 float32 ULP |
|---|---:|---:|
| Same model source and physical parameters? | yes | **yes** |
| Modified initial ZINI nodes | 0 | **1 of 1681** |
| Initial right/east lake entry throat elevation | 114.16148376464844m | same |
| Initial left/west throat elevation | 114.16148376464844m | **114.1614761352539m** |
| Actual initial west/east throat difference | 0 | **7.62939453125e-6 m = 0.007629mm** |
| **MAIN lake outlet from true `.lak` component geometry** | (29,20)km, **east** | (11,20)km, **west** |
| Main lake component nodes | 222 | 222 |
| Total lake components, identified by original source | 3 | 3 |
| Changed outlet node classification / position | reference | **2 nodes** |
| Changed terminal downstream pointers across all 41² nodes | reference | **229** of 1681 (13.62%) |
| Basin-wide compacted sediment volume proxy after 0.1Myr | **0.0092km³** | **0.0104km³** |
| Basin-wide compacted sediment volume delta | reference | **+0.0012km³**, about **+13.0%** relative to tiny baseline |
| Spatial sediment thickness RMS delta after 0.1Myr | reference | **0.02649m** |

**Crucial location control:** Prior [Test B (9 full original TISC runs)](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38210167704) perturbed the outward notch locations (10,20)km or (30,20)km by ±1 ULP through 1cm. **No native lake outlet or downstream link changed there**. Test C changes only the **inward throat controlling the dominant lake's overflow connection**, the next cell in toward its interior, at (11,20)km or (29,20)km. **One ULP now flips the dominant lake from east to west**, and 229 network links also change. Therefore not all same-looking lowland nodes are physically topologically equivalent. In this artificial example, outlet-location sensitivity is strongly local to the controlling saddle connectivity.

**20-case envelope:**
- All of **13** progressively lower west-throat scenarios (requested 10µm through 4m) switch the primary outlet from east to the **west side**; the west endpoint is (11,20)km through 3m lowering, and (12,20)km for the 4m test.
- All **6** east-throat raising scenarios (requested 0.1–3m) also switch primary outlet from east to **west**.
- Initial TIE remains east; 229 downstream cells change in all tested nonbaseline cases except 4m west has 230 changes; the lake-component count stays 3 even though outlet locations change.
- Real TISC solver produces sediment thickness spatial RMS ~0.0226–0.0266m in the series; the 0.1Myr integrated sedimentary volume perturbation is **small in absolute units** despite sharply changing basin-scale flow direction.
- All C source and model lake/river rules stay the accepted 03t baseline; the output-only 03x float printer is applied; ALL cases have identical `.PRM`, no `.UNIT`, independent fresh initial condition, and satisfy corrected mass-budget <0.001%.

### Interpretation — positive mechanism result, not an author code bug finding

The **degenerate initial equal-height pair** yields an algorithmic tie; in source `Define_Drainage_Net()`, neighbor ordering, strictly negative and zero-slope comparisons, lake membership and connected-component sorting can control which side is chosen. Changing just one truly controlling saddle by 1 float32 ULP shows original full hydrology can select an opposite outlet. This is **strong proof of finite-precision/geometry sensitivity near a degenerate two-saddle configuration**, but **NOT** proof that the hydrological algorithm is faulty for a realistic nondegenerate basin. One-cell exact-equality ties may be underconstrained physically and mathematically. The outcome is not a palaeoclimatic or palaeogeographic prediction.

The natural next numerical-only question is to benchmark a **unique obvious low outlet** separately from **exact equal outlets**, verify symmetry/rotation invariance and whether native C component/neighbor traversal order controls which exact-tie outlet is chosen, using a tiny explicitly logged C test or the same miniature model with rotated mirrored ZINI. Only promote a code correction if the original chooses a **physically higher unique saddle** when a resolvably lower spillway exists, or violates outlet/mass invariance beyond benign tie selection.

The implication for Junggar: the original V10.2B whole-domain 98.75% net erosion export cannot be explained from these miniature results; one must identify the real stage-dependent eastern/northern source-to-sink corridors and **palaeodivide/closed basin entry heights** at the Junggar 10km grid, then test high-resolution 5km stage cases with explicit geological constraints and balanced sediment mass. A micro TISC algorithm test cannot itself create missing long-term subsidence or sediment input.
