# 03L / 03N Geological acceptance and sediment-balance forensics

## Official 6_tectonics first-order geological acceptance

**Status: 401×401 full 0–15 Myr forward model completed; first-order geometric response conditionally passes; total sediment mass accounting DOES NOT pass.** The author 401 PRM, UNIT and profile files were unchanged. Original upstream commit was `danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd`. Actual execution uses validated 03g+03j hydro performance patches plus explicitly labeled experimental 03k negative fractional-power-slope guard. The scientifically modified erosion formula is NOT byte-identical to upstream, although the final seven exported forward-field files from unguarded vs guarded 401 whole runs were byte-exact.

**Source of six/ten/twelve/fifteen Myr spatial snapshots:** [03L GitHub Actions run 38160184315](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38160184315), every job completed successfully at its requested horizon. [Complete official 15-Myr run](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38158590091). Input C diffs are in artifact bundles.

The figure pack includes:

- `FIG03L_01_4stage_fields`, four-stage comparable-scale elevations, flexure and sediment-thickness maps.
- `FIG03L_02_stratigraphic_sections`, the author's y=-50 km cross section from actual stage-specific `demo.hrz` unit-density metadata.
- `FIG03L_03_structural_migration_and_sediment`, peak indicators vs total deposited sediment volume.
- `FIG03L_04_sediment_budget_audit`, deliberately UNCORRECTED sediment-mass deficits.

These figures were generated from existing 03L QGIS-ready geotiffs and the original direct numerical `demo.st`, `demo.hrz` and `demo.xyzt` fields. **Synthetic local x-y kilometers are not Junggar real-world coordinates.** The model's time axis measures elapsed simulation time, not geologic Ma before present. The 6/10/12 outputs are independent t=0-anchored runs, not multi-step resumes.

### The four-stage quantitative control table

| elapsed Myr | Maximum elevation (m) | Peak downward w (m) | Peak deposited thickness (m) | Area-weighted deposited volume (km³) | Thickness-peak model x (km) |
|---|---:|---:|---:|---:|---:|
| 6 | 2,207.2 | 1,407.8 | 1,158.3 | 31,904 | 61.25 |
| 10 | 1,771.0 | 1,860.2 | 1,396.0 | 41,766 | 141.25 |
| 12 | 2,523.2 | 2,268.7 | 1,767.5 | 49,660 | 163.75 |
| 15 | 2,349.5 | 2,011.1 | 1,493.9 | 59,834 | 161.25 |

[Permanent four-stage source table](../results/03_tectonics/03L_FORMAL_GEOLOGICAL_QC_STAGES.csv). Peak x is a **cell extremum**, not the objectively traced centroid of one individual depositional basin; the plot explicitly distinguishes peak indicators and a weighted upland centroid.

The 0–6, 6–10, 10–12 and 12–15 Myr windows match the two specified external motion regimes. The results clearly exhibit migrating uplift, downward plate flexure and sediment wedges on both sides of the prescribed uplift; peak sediment thickness migrates about +102.5 km in synthetic x from 6 to 12 Myr. Total sediment volume continues increasing to 15 Myr even as the locally thickest sediment decreases between 12 and 15 Myr. This is not an external geological validation of real foreland basin evolution, and not emergent stress-produced thrust propagation.

Spatial grid comparison from 121 to 401: flexure correlation ~0.999, topography ~0.951, sediment thickness ~0.975, but total sediment volume differs around **15.5%**. Therefore tectonic/flexural first-order shape conditionally passes; sedimentary convergence does not.

### What is proven about the early sediment-mass gap

Measured in 03M with original author physical inputs and no logging-roundoff approximations:

| interval begin (Myr) | erosion (kg) | net deposition (kg) | export (kg) | unexplained three-term gap (kg) | gap/erosion |
|---|---:|---:|---:|---:|---:|
| 0.5 | 6.01694×10¹⁴ | 2.91313×10¹⁴ | 3.05992×10¹⁴ | 4.38879×10¹² | 0.729% |
| 1.0 | 1.92309×10¹⁵ | 1.23657×10¹⁵ | 3.95240×10¹³ | 6.46997×10¹⁴ | 33.64% |
| 1.5 | 2.75691×10¹⁵ | 1.75727×10¹⁵ | 6.66448×10¹³ | 9.33004×10¹⁴ | 33.84% |

[03M exact accumulator diagnosis](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38160629828), [permanent gap table](../results/03_tectonics/03N_EARLY_EXACT_MASS_GAPS.csv).

At each interval's end the `drainage[].masstr` in-flight suspended sediment is zero. These are genuine missing terms from the model's **three-term reported budget**, not a printed two-digit exponent artifact. Conservation across all model reservoirs is NOT proven.

**03N narrowing**: [401 node-interval tracking run 38161854457](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38161854457) repeatedly scanned the evolving model stock after every 1024 processed nodes within `Fluvial_Transport()`, without physical changes. In the 1.0-Myr interval, the 10 substep residuals were (×10¹² kg) 9.876, 24.758, 29.459, 67.557, 73.440, 76.608, 80.008, 81.714, 90.145, 113.431. Their sum is exactly 646.997×10¹² kg, independently reproducing the overall missing three-term budget. Therefore the imbalance is being created in the per-node routing/erosion/deposition calculations, not by the final summary printout.

The explicit 03N `closed_lake_mass_reset_kg` diagnostic remained **zero** across examined substeps. Hence the simple `Lake_Fill` closed-lake end-of-call clearing is not the observed missing-mass source. Do **not** incorrectly assert that lake sediment clearing is the cause on present evidence.

Next, 03O is targeting the most imbalanced 1024-node chunks with read-only whole-grid suspension scans before and after **each** cell, to identify the first responsible flow-transfer and drainage types. A more granular evidence-backed cause is not yet established. Do not set a nominal correction factor or tune basin sedimentation to hide residuals.

## 03O per-cell forensic result, updated

The separately instrumented [03O 401-grid node check](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38162346883) **completed successfully**. This rerun of the coupled author 401 benchmark made a whole-grid in-flight suspended-mass inventory immediately before and immediately after individual cells in the worst 03N chunks. Source equations and inputs were not altered by this tracer.

Two targeted windows produced **90 significant single-cell positive discrepancies (>10¹⁰ kg)**. Every flagged node is an ordinary **river ('R') with lake index 0**, rather than a lake/outlet boundary node. All previously checked closed-lake cleared mass values were zero. The largest tracked single-cell discrepancy was **8.1288×10¹⁰ kg** at time 1.0 Myr, call 24, sorted node 136214, (row=146,col=130), flowing to (147,131). Another focused cell at 0.5 Myr, sorted node 149193, (63,83), flows to (63,84), with discrepancy **2.2412×10¹⁰ kg**.

This is an **identification of the problematic per-node stream-process category**, not yet proof of the precise defective formula. In particular, do not attribute the discrepancy to lake clearing. The follow-up targeted [03P erosion source/ledger/transport trace](https://github.com/lcxstar/tisc-mechanism-lab/actions) will compare exact requested `d_mass`, the changes to `ctx->total_bedrock_eros_mass` and `ctx->total_sed_mass` in `Erode()`, and the forwarded `drainage.masstr*dt_st` for these same nodes. A proposed correction must pass a changed-vs-baseline physical field and full mass-budget test.

## 03P further source-path identification

The separately labeled [03P official 401 source–sediment trace](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38162722788) finished, exited 0. Both targeted source cells show **negative `d_mass`**, so the offending river operations are the **sedimentation branch, not calls into `Erode()`**:

- At t=0.5 Myr, fluvial call 20, sorted cell 149193, (row63,col83), `d_mass=-1,184,502,784 kg`, inlet suspended sediment rate ~0.02183775 kg/s, and rate remaining after local sedimentation ~0.02108704 kg/s, routed toward cell (63,84).
- At t=1.0 Myr, call 24, sorted cell 136214, (row146,col130), `d_mass=-15,543,129,088 kg`, inlet suspended rate ~0.18883418 kg/s, after local sedimentation ~0.17898327 kg/s, routed toward cell (147,131).

No `TISC_03P_ERODE` log was emitted for either cell because `Erode()` is not invoked when `d_mass<0`. The physically relevant next checks therefore concern `Sediment()`, the updating of `drainage[row][col].masstr`, `transfer_mass`, and the `processed[downstream]` branch. **03P does not yet identify one executable line as the entire root cause.** Do not silently patch the algorithm before checking local mass equivalence and rerunning the full budget.

## Scientific decision

- Full 401 simulated tectonic evolution, original flexure and corresponding stage exports: **PASS**.
- Large-scale forward-generated uplift/flexural response and dual sediment wedges: **CONDITIONAL PASS as method verification**, not geology-calibrated.
- Water-routing aggregate mass budget: **preliminary PASS at reported precision**.
- 121/401 sediment-grid volume consistency: **NOT CONVERGED**.
- Sediment three-term mass-accounting closure: **FAIL / SOURCE STILL UNDER FORENSIC AUDIT**.
- Approved as foundation for quantitative Junggar sediment thickness predictions: **NOT YET**.

Preserve the original author's baseline, the separately labeled 03k scientific guard, and all source patches. Do not describe 03k as a physically unmodified upstream reproduction.
