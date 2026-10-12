# Ebro Basin — Initial-Condition and Version Audit

**Completed 12 October 2026.** Scope is the original author's TISC demonstration, **not** the Junggar geological-evolution project. All diagnosed source variants and simulations use unmodified original geology unless a precisely recorded experimental intervention is explicitly declared.

## Executive verdict

The modern **208 × 110** original-demo Ebro model is **numerically runnable but not numerically equivalent** to the author's 2016 archived `Ebro_evol.screen`. At the first half-Myr its maximum surface elevation is 9071.6 m, versus 1200.8 m historically.

**The root cause class has now been identified as a strong nonlinear interaction between solver/source generation and the refined model's grid/time/topography/hydrology controls, not merely an incorrect EET or asthenosphere density.** Cross-checking the 2017-04-20 original TISC source and 2017 Ebro input reproduces the historical initial elevation and first-step load/flexure within approximately 10 m / the correct order of magnitude. The exact 2016 binary is not publicly preserved in this Git history. No single faulty line of current C code has been identified.

- Precise **2016 old output**: [author `Ebro_evol.screen`](https://github.com/danigeos/tisc/blob/d18b7d270f4d671b80223e10dede329ad35cafdd/tisc/demo/8_Ebro_evol/Ebro_evol.screen).
- Pinned **2017 source**: [38c63ab5bacf2045530160ba8e41ae0071a04065](https://github.com/danigeos/tisc/tree/38c63ab5bacf2045530160ba8e41ae0071a04065) (source layout at repository root).
- Pinned **2026 source**: [d18b7d270f4d671b80223e10dede329ad35cafdd](https://github.com/danigeos/tisc/tree/d18b7d270f4d671b80223e10dede329ad35cafdd) (current layout `tisc/`).
- Reference geological paper, distinct from the 2016 executable: García-Castellanos et al. (2003), JGR Solid Earth, https://doi.org/10.1029/2002JB002073. Paper model settings must not be silently conflated with 2017 or 2026 demo files.

## 1. Actual source and input history

| Item | 2017 historical source checkout | Pinned 2026 checkout |
|---|---|---|
| Input file location | `demo/8_Ebro_evol/Ebro_evol.PRM` | `tisc/demo/8_Ebro_evol/Ebro_evol.PRM` |
| Grid | **104 × 55** | **208 × 110** |
| Main deformation/flexure dt | 0.5 Myr | 0.5 Myr |
| Surface-process dt_eros | **0.025 Myr** | **0.05 Myr** |
| PRM internal version label | `TISC_2016-08-30` | `TISC_2016-08-30` |
| Source template Te default | 15000 m | 15000 m |
| Source template densasthen default | 3250 kg/m³ | 3200 kg/m³ |
| Explicit Ebro PRM densmantle | 3250 kg/m³ | 3250 kg/m³ |
| Separate EET property grid included | No | No |

The source includes **two distinct density variables**, `densmantle` and `densasthen`. They cannot be treated as synonymous. The PRM version label remaining `TISC_2016-08-30` does not establish identical C source or model-input versions.

The 2003 paper's Table 2 describes its *published* calibrated scenario and does not establish an exact identity with the later Ebro demo. Its 0.05 Myr listed time step, regional space-varying Te of 5–25 km and selected kinematic/climate values should be tracked as a **third historical stage**, not substituted into an audit claimed to reproduce 2016.

## 2. Direct stage-by-stage original-log audit (06a, PASSED)

| Output diagnostic at -59.5 Ma | Original 2016 screen | 2026 source + 2026 author inputs |
|---|---:|---:|
| Max topography | **1200.8 m** | **9071.6 m** |
| Peak instantaneous load pressure | **3.50 MPa** | **195.0 MPa** |
| Signed sum of instantaneous load | **-4.21 × 10^15 N** | **+1.06 × 10^17 N** |
| Max positive model flexure | **10.7 m** | **60.3 m** |
| Printed sediment volume | **2820 km³** | **7780 km³** |

These are actual logged fields, not reconstructed spatial data. The aggregate load includes model-coupled loading terms; do not assign all of it directly to tectonics without source-specific separation. The first-step difference begins immediately. A merely ~50 m maximum-flexure difference alone cannot explain an ~7.9 km maximum-topography difference.

Archived [2016 vs 2026 first five stages CSV](../results/06_ebro_initial_version_audit/06a_historical_vs_current/FIRST_FIVE_TIMES_STEPWISE_2016_VS_2026.csv), [inherited input/default matrix](../results/06_ebro_initial_version_audit/06a_historical_vs_current/EFFECTIVE_INPUT_AND_DEFAULTS.csv). Logged precipitation integral outputs changed units/format between versions and must not be compared naively.

## 3. Current original-source short-run perturbations (06b, 10/10 PASS)

Each run copied the pinned original `.PRM/.UNIT/.ZINI/.SLV` inputs; exact changes and before/after SHA256 are in the per-case archive. The modern 2026 C source was changed **only to replace two invalid NBSP compile whitespaces**, with no 03t acceleration or slope patches.

| Intervention on current source | -59.5 Ma max topography | Max load | Max flexure |
|---|---:|---:|---:|
| Original current input baseline, 208 × 110 | **9071.6 m** | 195 MPa | 60.3 m |
| Explicit Te 25 km | 9071.6 m | 195 MPa | 53.3 m |
| Explicit densasthen 3250 kg/m³ | 9071.6 m | 195 MPa | 59.4 m |
| Both Te and density changes | 9071.6 m | 195 MPa | 52.6 m |
| Both hydrology and erosion off | **1201.9 m** | Not reported | Not reported |
| Initial first-unit velocity set to zero | 9071.6 m | 195 MPa | 60.3 m |
| Delay first thrust until -58 Ma | 8085.9 m | 174 MPa | 45.8 m |
| Delay all five tectonic events until -57 Ma | 8085.9 m | 174 MPa | 45.8 m |
| Main dt reduced from 0.5 to 0.05 Myr | 5246.5 m | 3.48 MPa | 38.0 m |
| Initial first-unit 10000 m geometry changed to 1000 m | 8920.9 m | 192 MPa | 58.2 m |

**Interpretation:** Wrong Te and soft-layer density are **real provenance differences but not causes of the 7870.8 m first-step elevation jump** under these controlled experiments. A hydrology/transport interaction is implicated. A simple first-thrust event shift is insufficient.

[06b original trial logs and native fields](../results/06_ebro_initial_version_audit/06b_early_parameter_interventions/) — 10 runs, all numerically completed.

## 4. Pristine 2017-source replay (06c, PASS)

Earliest located version close to 2016 comes from 20 April 2017 Git history, **not** the original August 2016 executable. It is explicitly the older source architecture before 2017 May UNIT/Block renaming. It was compiled on GitHub Actions with GNU C portability flag `-fcommon` and **recompiled legacy prebuilt `lib/libreria.o` from original 2017 source**. No geological or physics-source C line was changed.

| Diagnostic at -59.5 Ma | Original 2016 log | 2017 source and 2017 input |
|---|---:|---:|
| Max topography | 1200.8 m | **1190.9 m** |
| Peak load pressure | 3.50 MPa | **4.21 MPa** |
| Max flexure | 10.7 m | **11.7 m** |

[Native 2017 replay output and source manifest](../results/06_ebro_initial_version_audit/06c_2017_historical_solver/) · [successful CI run](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38241706953).

The result is **close numerical agreement, not bitwise identity or proof that the exact original 2016 executable was restored**.

## 5. Isolating first-step hydrology, initial roughness, grid and timestep (06d)

| 2026 author source, intervention | Max topography at -59.5 Ma |
|---|---:|
| Refined original 208×110 / erosion dt=0.05 Myr | **9071.6 m** |
| Disable hydrology only | **1201.8 m** |
| Disable erosion only (hydrology retained) | **SEGFAULT -11**, no valid first-step observation |
| Reduce surface-process timestep to 0.025 Myr | 3782.0 m |
| Reduce surface-process timestep to 0.005 Myr | **1200.1 m** |
| Main dt=0.05, surface dt=0.005 Myr | **1207.1 m** |
| Remove 5 m initial random relief | **1198.3 m** |
| Remove fluvial transport capacity only | 8483.0 m |
| Set hillslope diffusion coefficient to zero | 9107.6 m |
| Change only grid 208×110 → **104×55**, keep surface dt=0.05 Myr | **1197.9 m** |
| Change grid to 104×55 and surface dt to 0.025 Myr | **1197.9 m** |

All data are archived even for the single failing `erosed_model=0` / `hydro_model=1` combination; hence 06d overall GitHub Action shows **failure for 1/11 tests**, not an unrecorded failed suite. A crash in an unsupported combination should not be conflated with the original fully coupled model being unexecutable.

**Interpretation:** On this current-source Ebro case, small source topographic randomness coupled with spatial resolution and erosion/runoff time stepping produces enormous first-step differences. Coarsening the grid alone restores near historical maximum elevation, but this is not a proof of basin-scale convergence or an endorsed tuning strategy. Reducing dt_eros to 0.005 Myr likewise passes only the short diagnostic window.

[06d cases and failure log](../results/06_ebro_initial_version_audit/06d_surface_grid_timestep/INTERVENTION_SUMMARY.md) · [run and archived evidence](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38241780748).

## 6. Crucial 2×2 source × input factorial (06e, 5/5 PASS)

The exact old PRM and the exact new PRM were each supplied to both independently compiled original 2017 and 2026 source versions, all clipped at -59 Ma. The fifth experiment tests the default asthenosphere density on the modern solver using the old input.

| C source code / input | 2017 source input (104×55; erosion dt .025) | 2026 source input (208×110; erosion dt .05) |
|---|---:|---:|
| 2017 source | **1190.9 m** | **1376.2 m** |
| 2026 source | **1197.9 m** | **9071.6 m** |

- **Change input with 2017 source fixed:** +185.3 m.
- **Change input with 2026 source fixed:** +7873.7 m.
- **Change source with 2017 input fixed:** +7.0 m.
- **Change source with 2026 input fixed:** +7695.4 m.
- **Difference-in-differences (interaction): +7688.4 m.**
- For 2026 source + 2017 input, changing inherited 2026 densasthen from 3200 to 3250 kg/m³ changed early max topography by **0.0 m** (within original log precision).

**Scientific verdict:** Neither the input revision *alone* nor the source revision *alone* creates the 9-km early high, whereas combining the 2026 source with its finer-grid author input produces that spike. Hence this is demonstrably a **solver–input interaction**. Grid resolution, surface dt and relief noise are independently established strong modifiers; individual hydrological/erosion subroutines are **not yet independently proven faulty**.

[06e five-case source/input cross-results and native logs](../results/06_ebro_initial_version_audit/06e_source_input_factorial/FACTORIAL_SUMMARY.md) · [successful 2×2 CI run](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38242086249).

## 7. Correct publication/research claims and pending next diagnostic

**Allowed**
- All seven original demo projects including 60-Myr Ebro have completed numeric execution in v04.
- Modern Ebro default run does not numerically match author 2016 output.
- The 2017 original C source + 2017 input closely matches the 2016 **first half-Myr**.
- Matching source/input controls prove an input–solver interaction and profound resolution/time-step sensitivity.

**Not allowed yet**
- Claim full 60-Myr historical reproducibility; historical 2016 executable still unavailable.
- Diagnose this as *only* a Te, density, first tectonic UNIT or current 03t optimization error.
- Claim river capture, lake overtopping or specific erosion routine is the sole demonstrated origin of this Ebro instability; no cell-level time-slice origin or numerical flux-budget localization is yet available.
- Adopt a coarse grid or short dt_eros as a validated 60-Myr geologic reproduction without doing the full calibrated time history and matching independent paleogeographic evidence.

**Next targeted experiment if mechanism-level precision is required:** localize the first unstable cells at -60 to -59.5 Ma and inspect runoff/receivers, sediment gains, water depth, initial surface gradient and actual load map. Focus the native transport sub-step, not basinwide parameter fitting. Then compare 2017 and 2026 hydrological routines at those coordinates. After verifying exact cause, attempt a 60-Myr test with unchanged 2017 original inputs and historical solver, rather than claiming scientific closure from the five short-window runs.

## 8. Artifact locations and reproducibility

| Stage | Contents | GitHub location |
|---|---|---|
| 06a | Historical 2016 vs 2026 first five time points, parameter defaults | [06a](../results/06_ebro_initial_version_audit/06a_historical_vs_current/) |
| 06b | Ten pristine-source one-variable interventions, run logs and native states | [06b](../results/06_ebro_initial_version_audit/06b_early_parameter_interventions/) |
| 06c | Successfully compiled 2017 source and native early 2017 Ebro replay | [06c](../results/06_ebro_initial_version_audit/06c_2017_historical_solver/) |
| 06d | Eleven climate/transport/grid/time perturbations, includes saved SEGFAULT outcome | [06d](../results/06_ebro_initial_version_audit/06d_surface_grid_timestep/) |
| 06e | Five full 2×2 source × input old/new controls | [06e](../results/06_ebro_initial_version_audit/06e_source_input_factorial/) |

Workflows are preserved under `.github/workflows/06a...06e...`. The short-run raw model inputs, full logs, final native output and SHA256 are permanently committed on this public branch. This entire forensic audit leaves original author's demos unchanged and does **not** modify the paused Junggar basin evolution model.
