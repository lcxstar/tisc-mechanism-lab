# TISC Ebro V07 — first surface substep cell and solute-flux causal audit

**12 October 2026 — original full demonstration kept unchanged.** [GitHub branch V07](https://github.com/lcxstar/tisc-mechanism-lab/tree/v07-ebro-first-surface-cell-flux-audit).

## Executive conclusion, supported by executed source-level counterfactuals

We identified the cause of the approximately **7.4 km spurious surface rise at the first -60 to -59.95 Ma surface substep** of the current 208×110 Ebro demonstration.

It is **unconditional gypsum + halite deposition in the modern 2026 TISC `Calculate_Discharge()` implementation**, even though the author PRM inherits **`salt_model=0`**. The code adds `dh_salt` directly to topography, newest sediment block and `Dq`; no call to `Sediment()` or `Erode()` occurs for that salt deposition, so ordinary sediment-transport mass ledger does not record it.

Five independent simulations on identical original author PRM, UNIT, ZINI and SLV files establish the causal pathway. Turning the ostensibly off switch off again changes nothing; removing ions removes the salt rise; temporarily making the salt accumulation conditional on the existing switch removes the rise; deliberately enabling that conditional recreates the anomaly exactly. This is a source-semantics issue, **not** solely the random-cell outlet rule, crustal elastic thickness, tectonic loading or Ebro input topography.

The root cause for this **large early-step spike** is resolved; **full 60-Myr numerical equivalence with author's 2016 history is not**.

## Model provenance

- Original current upstream: `danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd` (2026).
- Original historical comparison: author's `Ebro_evol.screen` created November 2016 (`TISC_2016-08-30`).
- Old solver: `danigeos/tisc@38c63ab5bacf2045530160ba8e41ae0071a04065` (20 April 2017). Older source has no `salt_model` / `gypsum_flux_grid` implementation.
- Current `tisc/doc/template.PRM` specifies `salt_model 0`. The `8_Ebro_evol/Ebro_evol.PRM` does not override it.
- Original input model 208×110 grid, `dt=0.5 Myr`, `dt_eros=0.05 Myr`; first 0.5 Myr has ten transport substeps.
- No parameter edits, extra geological load, routing epsilon or 03t optimized patches were used in the **baseline diagnostic**. Only two invalid nonbreaking-space compiler characters were normalized, plus audited read-only C instrumentation.
- Temporary `if(salt_model)` was used **only in one independently compiled experimental binary**, not committed as a production solver change.

## 07a and 07b: locate the first abnormal native cell in the first 10 transport steps

| Step within initial 0.5 Myr | Maximum before hydro (m) | Max after hydro/routing (m) | Max after fluvial erosion/sedimentation (m) |
|---|---:|---:|---:|
| 1 | 1201.859 | **7555.547** | **7518.477** |
| 3 | 7178.362 | **9551.676** | **9501.920** |
| 8 | 7705.225 | **10134.687** | **10073.848** |
| 10 | 9478.601 | 9478.601 | 9107.566 |

At step 1 the first extreme is **row=83, col=130, x=396.938 km, y=119.266063 km** in model-local coordinates. The local surface starts at **154.448 m**, rises to **7555.547 m during hydrology**, then decreases slightly to **7518.477 m** during fluvial sediment transport. It is **not** a 7-km instantaneous elastic flexure or an error introduced by `Fluvial_Transport()`.

The same coordinate after fluvial transport records about **0.115 m³/s** runoff, **0 kg/s** remaining transported sediment flux, **1.0736×10^12 kg** ordinary erosion mass in that substep and **0 kg** ordinary deposited mass. These are end-of-step/native per-cell diagnostic definitions; runoff and transported sediment at this point do not measure full upstream flux histories.

[Full all-substep time series](../results/07_ebro_first_cell_flux/07a_native_substep/ALL_SURFACE_SUBSTEPS.csv) · [7×7 neighbor drainage/flux table](../results/07_ebro_first_cell_flux/07a_native_substep/FIRST_ANOMALY_7x7_CELL_FLUX.csv) · [all 22880×3×10 raw stage samples compressed](../results/07_ebro_first_cell_flux/07a_native_substep/CELL_SUBSTEPS.csv.gz) · [first-spike model map PDF](../results/07_ebro_first_cell_flux/07a_native_substep/FIRST_ANOMALOUS_STEP_TOPOGRAPHY.pdf) · [model-local candidate GeoJSON](../results/07_ebro_first_cell_flux/07a_native_substep/FIRST_ANOMALY_CELLS_LOCAL_MODEL_M.geojson).

### Function boundary isolation (07c)

Full-grid outputs before and after each original C function (no numerical changes) indicate:

| Original C stage | Max native surface height (m) |
|---|---:|
| After tectonic incremental topography / `ReSort_Matrix()` | 1201.859 |
| After `Define_Drainage_Net()` | 1201.859 |
| After `Calculate_Precipitation_Evaporation()` | 1201.859 |
| After `Ice_Flow()` | 1201.859 |
| After `read_file_node_defs()` | 1201.859 |
| **After `Calculate_Discharge()`** | **7555.547** |

In `Calculate_Discharge()` specifically, 21 cells gain more than 100 m and at the first extreme cell `Dq` increases from zero to **+160,885,264 Pa** while ordinary `Sediment()`/ `Erode()` recorded mass increments remain **zero**. This is consistent with direct material-height and isostatic-load updates from another branch, rather than regular fluvial transport.

[07c exact function-stage CSV and first 60 rising cells](../results/07_ebro_first_cell_flux/07c_function_source/).

## 07e: confirm source-level unguarded gypsum/halite deposition

The relevant modern `surf_proc.c` procedure calculates gypsum/halite precipitation from river ions and adds height directly to the state through two code blocks:

```c
/* Distribute salt deposition */
...
ctx->topo[r][c] += dh_salt;
Dq[r][c] += dh_salt * g * (avg_dens - cfg->densenv);
```

In pinned 2026 code, **the complete `Calculate_Discharge()` function contains no reference to `salt_model`**, even though the model's configuration has the switch `salt_model=0`. There are two direct salt height-update sites, one at individual cells and another distributing precipitation across lake cells. They also increase the thickness of the uppermost block. The original 2017 `surf_proc.c` has no salt chemistry / gypsum flux model at all.

### Five independent original-input runs

| Intervention on disposable original solver | Max topo at -59.5 Ma | Peak instantaneous load | Diagnostic salt sinks >50m |
|---|---:|---:|---:|
| A Original modern source, default salt_model=0 | **9071.6 m** | 195 MPa | 557 |
| B Original source, explicitly `-qsalt_model=0` | **9071.6 m** | 195 MPa | 557 |
| C Original source, set all eight SEA/RIV major ion inputs to zero | **1521.6 m** | 28.9 MPa | 0 |
| D Experimental source with deposition inside `if(salt_model)`, `-qsalt_model=0` | **1521.6 m** | 28.9 MPa | 0 |
| E Identical experimental source, `-qsalt_model=1` | **9071.6 m** | 195 MPa | 557 |

All five experiments **EXIT 0**; each has independent original physical input copies, compiler hashes, source diff, full logs, native short model result tarball and QC. The source-proximate event counter counts records where deposit height exceeds 50m, plus specifically observed first-extreme cell. It is not a count of every salt-deposition operation.

### Exact source event at first extreme cell

```text
V07SALTEVENT branch=direct salt_model=0 row=83 col=130
precip_gypsum_kg_s=67.6605072
precip_halite_kg_s=95.584877
rise_m=7401.09863
dt_sec=1.57783674e+12
```

- **This source statement and event account for the entire 7401.09865 m high jump observed independently in the earlier function-boundary mapping.**
- Accumulated `Dq` is about 160.885 MPa at that coordinate immediately after the call.
- Crucially, the model does this **while reporting `salt_model=0`**, so it is not an intended explicit salt-rich scenario.
- With an effective off switch, the subsequent full first-half-Myr output maximum is **1521.6 m**, no longer 9071.6 m. The remaining difference from author's -59.5 Ma **1200.8m** result is **320.8m** and remains to be investigated in grid/time/source behavior.

[Five-source/ion controls report](../results/07_ebro_first_cell_flux/07e_salt_cause/SALT_CAUSAL_EXPERIMENT_SUMMARY.md) · [direct raw C salt-flux event lines](../results/07_ebro_first_cell_flux/07e_salt_cause/A_original_salt_default_0/SALT_SINK_EVENTS.txt) · [auditable instrumented vs conditionally gated source diffs](../results/07_ebro_first_cell_flux/07e_salt_cause/) · [successful 07e action](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38245090977).

## Root cause and limits

**Confirmed local error:** Source code applies highly amplified halite and gypsum precipitation to model relief when the salt chemistry mode is configured off. The source-level material flux and the reported height increment agree. This explains the enormous first-substep terrain rise, a primary contributor to modern Ebro 2016 mismatch.

**Open items:**
1. A purely opt-in patch to sediment height operations has **not** established that all 2026 salt-ion routines respect the `salt_model` control or the original 2016 geology. Only two direct height-update loops were guarded in an experimental binary.
2. A corrected first-step max of 1521.6 m is still 320.8m above 2016 history. Grid/dt/source changes and ordinary sediment routing still require stage-scoped verification.
3. A full -60 to 0 Ma run using a safely gated and thoroughly regression-tested source has **not** yet been performed. Existing 60-Myr original modern-solver results are known to diverge from 2016.
4. The five counterfactuals are **not** a code fix that has been submitted to author's upstream repository. No changes have been made to the science pause of Junggar.

**Recommended next source engineering steps:**
- Move **all ion/salt computations and deposition** behind a logically consistent explicit `salt_model` check (when off, no chemical height, no chemical block thickness, no `Dq` effect).
- Add an invariant test that `salt_model=0` gives strictly zero gypsum/halite formation, and preserve parity for intentionally enabled cases.
- Re-run 2017-source and 2026-corrected variants at both 104×55 and 208×110, using identical short time stepping and native initial topology before deciding any geological inputs are wrong.
- Only after short-run convergence, attempt original 60-Myr model and compare author surface height, sediment volume and drainage evolution with caveat that 2016 binary is unavailable.

## Permanent audit artifacts and execution

- [V07 07a native 10-substep full raw grids and fluxes](../results/07_ebro_first_cell_flux/07a_native_substep/) — 07a main physical calculation complete, initial CI action red only because an analyzer file was committed after it started; diagnostic raw grids were committed.
- [V07 07b successful independent analysis and figures](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38243879846)
- [V07 07c original-source precise routine boundary and per-cell source mass table](../results/07_ebro_first_cell_flux/07c_function_source/) — [successful job](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38244406783)
- [V07 07e five active C-source counterfactuals and direct solute-flux events](../results/07_ebro_first_cell_flux/07e_salt_cause/) — [successful job](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38245090977)

**Status:** Ebro first-step catastrophic terrain spike causally located and verified. Full Ebro numerical restoration to 2016 is not yet finished. Original author inputs and Junggar geological evolution remain untouched.

## V07f map completion — final original-grid chemistry height and load figures

Native 208×110 grids before/after the exact first `Calculate_Discharge()` call were plotted without spatial interpolation and permanently archived (read-only analysis, no new TISC run).

- [Vector PDF — salt precipitation topography increase in first -60 to -59.95 Ma surface substep](../results/07_ebro_first_cell_flux/07f_spatial_causal_figures/SALT_DEPOSITION_HEIGHT_FIRST_005MYR.pdf)
- [Vector PDF — matching isostatic load increment Dq (MPa)](../results/07_ebro_first_cell_flux/07f_spatial_causal_figures/SALT_DEPOSITION_LOAD_FIRST_005MYR.pdf)
- [PNG and plot QC including 21 cells above 100m rise](../results/07_ebro_first_cell_flux/07f_spatial_causal_figures/)
- [Successfully archived figure-generation workflow](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38245920393)

At first extreme grid row 83, column 130, the source-attributed local topographic rise is **7401.098653m** and load increment **160.885264MPa**. A total of **21 cells** rose by over 100m in that initial hydrological substep. Model axes are local TISC kilometres, not latitude/longitude. The spatial diagnosis has no paleogeographic CRS and must not be overlaid directly on WGS84 basemaps.
