# Experiment 03c — 401x401 first-step hydrology/erosion isolation

**Result:** exact original demo input files; separate *diagnostic* command-line toggles; the stalled first step is strongly associated with the HYDRO-ENABLED branch of surface processes.

Workflow: https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38145334108

| Case | Grid | TISC overrides | Time reached | Wall seconds | Exit |
|---|---|---|---:|---:|---|
| Original full official 6_tectonics | 401x401 | None (except verbose) | 0.0 Myr | 1800 | 124 timed out |
| Water-dependent path ON, `erosed_model=0`, isostasy OFF | 401x401 | `-tf0.5 -qisost_model=0 -qerosed_model=0 -qplotting_mode=0` | 0.0 Myr | 120 | 124 timed out |
| Water-dependent path OFF, `erosed_model=6`, isostasy OFF | 401x401 | `-tf0.5 -qisost_model=0 -qhydro_model=0 -qplotting_mode=0` | 0.5 Myr | 0.42 | 0 (finished) |
| Both water and erosion path OFF, isostasy OFF (earlier 03b) | 401x401 | `-tf0.5 -qisost_model=0 -qhydro_model=0 -qerosed_model=0 -qplotting_mode=0` | 0.5 Myr | 0.21 | 0 (finished) |

Author input files (`demo.PRM`, `demo1.UNIT`, `demo2.UNIT`, `demo.PRFL`) are byte-identical for the 401 trials (SHA256 audited). TISC source is pinned to `d18b7d270f4d671b80223e10dede329ad35cafdd`. The two-byte compile-only U+00A0 fix is separately documented. **No physical TISC source algorithm was altered.**

**Interpretation limits:** Keeping `hydro_model=1` with `erosed_model=0` does not isolate only a hydrology equation: the routine `Surface_Transport` can still enter drainage sorting, lakes and fluvial transport. We have isolated the water-dependent execution path, not yet a specific bottleneck subroutine.

**Source-level suspected hotspot:** the `Surface_Transport` routine in pinned `surf_proc.c` has a nested equal-elevation reordering section, comparing and inserting nodes across each equal-height group following `Calculate_Discharge`. The original demo starts from 100 m uniformly flat topography at all 160,801 nodes. Its potential worst-case cost is huge. This is a technically grounded hypothesis and **needs timed instrumentation**, not an already demonstrated root cause.

**Independent scientific issue:** our archived 81x81 cases, as well as 121x121, complete the evolution but the TISC log sometimes contains `outp_seds: -nan N`. This invalidates sediment-export mass-balance claims even though deflection and tectonic block-shift arrays are finite. The mass diagnostic must be traced back to `total_lost_sed_mass` in `Surface_Transport` / `Fluvial_Transport`.

### Strict reproduction protocol still to complete

1. Time *without changing physics* the `ReSort_Matrix`, `Define_Drainage_Net`, `Calculate_Discharge`, equal-height re-sort and `Fluvial_Transport` calls at fixed 401 input; identify actual hotspot.
2. If a pathological equal-height algorithm is responsible, implement a correct stable alternative in an **explicitly tagged performance-patched branch** and prove identical numerical results against official solver at 81 and 121 nodes (not merely similar appearance). Never label modified upstream as byte-for-byte original.
3. Investigate and clear nonfinite `total_lost_sed_mass`, including its first invalid timestep, before accepting a sediment mass balance.
4. Run complete 401 x 401, 0–15 Myr, same original physical files, with a tracked source tag and record the complete stage series, block shifts, topography, flexure and sediment/water budget; check numerical resolution dependence.
5. Only then resume changes to `ride`, velocity or North Tianshan geometry.

The official `6_tectonics` directory has only input PRM/UNIT/PRFL files, no published numerical final grids, so full original successful execution and physically interpretable outputs are the direct software reproduction criterion; cross-version exact output matching would need a verified reference dataset.
