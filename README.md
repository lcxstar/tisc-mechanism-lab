## 03v — Benchmark reproduced with corrections; numerical convergence under audit

**Status:** The author's official `6_tectonics` synthetic tectonic/flexure/erosion/sedimentation example completes its **original 401×401 grid, 0–15 Myr** with *documented* computational optimizations (03g/03j), a separately labeled physical domain guard (03k) and the validated 64-bit mass ledger (03t). This is a **successful operational/mechanistic reproduction using a modified implementation**, **not** an unchanged-source bitwise or author-published field-perfect reproduction.

**New controlled precision finding:** only raising `Sediment()` local `dh_sed` from `float` to `double`, without making Block/topography/deflection grid state double, significantly changes long-time output. A read-only native state hash on 121 grid first differs in topography/Block at **0.55 Myr**, in plate deflection at **2.05 Myr**, and in drainage state at **2.55 Myr**. First printed 0.1m topography differences are visible at 2.5 Myr; lake/outlet graph differences are visible by 3 Myr, and prominent by 6–15 Myr. This is computational sensitivity, not proof double is more geologically correct.

**Preliminary time refinement:** terrain RMS differences between the paired variants at full 15 Myr decline from **43.74→21.53→19.39 m** on 81 grid, and **48.05→26.46→24.94 m** on 121 grid, across `(dt,dt_eros)=(.5,.05)→(.5,.025)→(.25,.025)` Myr. A 201-grid test yielded **68.52 m** at author dt and **57.96 m** with half erosional dt. Thus increasing grid resolution does **not** automatically reduce numerical divergence; rigorous grid convergence remains unproven.

- [Full documented 03v audit plan](notes/03v_reproduction_and_precision_convergence_audit.md)
- [Audited first-divergence, topology and time-step findings](notes/03v_initial_results_and_reproduction_status.md)
- [121-grid 0.5–15 Myr check CSV](results/03_tectonics/03V_121_DIVERGENCE_STAGES.csv)
- [81/121 preliminary convergence CSV](results/03_tectonics/03V_TIME_SPACE_CONVERGENCE_EARLY.csv)
- [Per-substep native-state hash CI](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38179009871)
- [Grid/time factorial experiments](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178558812)
- [Original 401-grid 15-Myr precision-endpoint comparison (PASS, precision sensitivity remains)](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178743124)
- [**FINAL 401/15Myr and 14-job precision-convergence findings**](notes/03v_FINAL_401_full15_results_and_14run_convergence.md)
- [**Final 14-condition numerical QC CSV**](results/03_tectonics/03V_FINAL_GRID_TIMESTEP_14_GROUPS.csv)

All planned **14/14** grid/time and 401 full-15 Myr paired benchmarks have now finished. **Scientific convergence is NOT established**: at 401/15 Myr, local-double `Sediment()` versus original `float` temporary produces 48.028m terrain RMS difference, 722.8m maximum local terrain difference, ~490m maximum local output sediment-thickness difference, and 82,656 different downstream links despite both corrected mass ledgers satisfying <0.001%. Prior to Junggar model calibration, isolate lake/outlet numerical discontinuities and verify same-scheme physical grid convergence.

## 03t — Solved: apparent 33–34% missing sediment caused by float32 accumulation

The author stores basinwide cumulative sediment `total_sed_mass` as a **32-bit float**. With millions of fine-grained open-lake deposits, many individual mass increments round to zero in that aggregate counter. The detailed 03q–03r node tracing and independently verified 03s `double` accounting demonstrate that the large reported loss was numerical bookkeeping, not missing material from those source/sink transactions.

**Measured 401×401** at time 1.0 Myr: native 32-bit reported loss **33.643619%**, independent 64-bit residual **0.000007660%**. At time 1.5 Myr: **33.842328%** native versus **0.000000513%** corrected. In N121 full 15 Myr, the largest original gap is 2.292665% versus 0.000012695% (double). **All 7 scientific output files** tested remain byte-for-byte identical with observer instrumentation at N121 full 15 Myr and N401 first 2 Myr, so the numerical model has not been tuned to force closure.

03t uses `scripts/profile_03s_double_ledger.py` and `scripts/patch_03t_correct_sediment_balance.py` to report scientifically meaningful double-precision `eros_nosd`, `sedim_inc`, `outp_seds`, and `sediment_balance`, preserving original native float structures and binary restart compatibility. N121 full corrected-output validation **PASS** (30 steps; all 7 fields SHA256-exact, maximum 0.000012695% balance error). Further N401 first2 and N401 full15 checks: [03t paired workflow](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38165200144), [03t full 401 workflow](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38165304319) — validate completion before claiming either passed.

[Detailed source and numerical audit](notes/03t_verified_float64_sediment_mass_accounting.md). This correction is distinct from the earlier 03k experimental negative-slope physical domain guard and from still-open 121→401 sediment-volume grid convergence.

## Current milestone — 03k, restored full 401-grid flexure and traced the sediment NaN

[03k scientific audit](notes/03k_nan_root_cause_and_401_flexure_results.md) | [full coupled 401 baseline GitHub run](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38157980373) | [independent experimental slope-corrected 401 run](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38158590091) | [experimental comparison](results/03_tectonics/03K_EXPERIMENTAL_GUARD_VALIDATION.csv)

Confirmed with instrumented original formula: the first `outp_seds=-nan` is caused by negative outlet slopes passed into `pow(slope,1.05)` for `erosed_model=6`. First observed faulty nodes are (19,120) on N121 and (400,151) on the original N401. A separate, explicitly labeled *physical correction* handles negative incision slopes with zero incision contribution; unlike 03g/03j, this changes a physical formula only for an invalid input domain. The corrected **121 grid 0–15 Myr** and **401 grid 0–0.5 Myr with original flexure enabled** both finished with zero sediment NaNs. Five published physical output files for both trials are byte-exact against the previous uncorrected 03j version. Mass-budget closure still needs full-precision validation. Full 401 **0–15 Myr runs have been started in separately retained original-formula and slope-corrected CI workflows**, but should not be called reproduced until their model exit, last T=15 timestamp, and outputs are verified.

## Current milestone — 03j, first complete 401×401 surface-routing timestep

[03j audited results](notes/03j_lake_discharge_optimization_results.md) | [81/121 eight-case validation](results/03_tectonics/03J_81_121_EQUIVALENCE.csv) | [401 benchmark](results/03_tectonics/03J_N401_FIRST_STEP.csv) | [GitHub Actions verified run](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38157360909)

After 03g merge optimization, 03j-A caches original-order lake evaporation sums with safe invalidation, and 03j-B skips expensive lake inflow scans only under a runtime-verified zero-evaporation/nonnegative-input invariant. **All eight small-grid original-vs-optimized output-file tests passed.** With original 401×401 input files, the optimized *surface-isolation* test (flexure temporarily disabled, -tf0.5) **finished all ten hydrology substeps and reached 0.5 Myr in 71.78 seconds, exit code 0**, skipping 1,605,950 unnecessary lake input scans. Two 81-grid nonzero-evaporation synthetic stress tests also matched physical output files exactly, including 51,388 lake-cache invalidations for the high-evaporation case.

**Not the full original author reproduction:** 401-grid original 0–15 Myr coupled flexure run still awaits verification. The upstream sediment-export `outp_seds=-nan` persists and needs separate analysis. The original baseline and prior mechanism experiments remain preserved.

# TISC Mechanism Lab

Independent, **public and reproducible** numerical experiments for learning the actual behavior of the [TISC](https://github.com/danigeos/tisc) program before applying it to tectonic–sedimentary evolution of the Junggar Basin or the North Tianshan.

## Current milestone — 03i, Calculate_Discharge O(N²) lake-input and evaporation bottleneck

**11 October 2026:** Official static flexure and Te experiments are validated. Four 81x81 tectonic control cases run to 15 Myr, but their sediment-export mass balance is not validated. The original coupled 401x401 case is still **NOT reproduced**.

**03i latest measured result:** [Read the discharge internal audit](notes/03i_discharge_internal_results.md). With 03g's validated lake-merge acceleration, the author demo's 401×401 water-flow calculation finishes two surface substeps in a bounded 210-second probe, but the first 0.5 Myr timestep remains unfinished (T=0 Myr). A completed discharge pass costs ~67.6 s; 98.7% lies in per-node lake evaporation/influx prechecks. The `Lake_Input_Discharge` helper alone visits ~26.05 billion lake nodes per pass. These are **measured engineering bottlenecks** in unchanged source physics, not yet a full official 401 reproduction. [121 measurements](results/03_tectonics/03I_N121_DISCHARGE_SUBSTEPS.csv) and [401 measurements](results/03_tectonics/03I_N401_DISCHARGE_SUBSTEPS.csv) are permanently stored on this branch. The original baseline on `main` is preserved.

**03f measured root cause:** [Lake-operation counts and per-function timings](notes/03f_lake_operation_results.md) show the 401-grid slowdown is overwhelmingly caused by linear duplicate searches in `Add_Node_To_Lake()` during massive node re-additions in `Unify_Lakes()`. Two independent 401 performance probes reached 144,416 and 156,704 of 160,801 nodes before their 140-second cutoffs; both remain incomplete. Permanent [numeric comparison](results/03_tectonics/LAKE_03F_SUMMARY.csv) and [401 node-progress samples](results/03_tectonics/LAKE_401_PROGRESS_03F.csv) are archived. A patched fast implementation must be numerically validated against the pinned upstream baseline before any full original case is called reproduced.

**Measured bottleneck:** [03d stage timing](notes/03d_surface_profile_results.md) shows the first 401-grid surface step blocks in `Define_Drainage_Net()` rather than the post-discharge reorder or fluvial transport. [03e nested timing](notes/03e_drainage_internal_results.md) confirms the growing cost is inside the ascending lake/drainage node sweep (136,224 of 160,801 nodes reached by 113.8 s; 120-s diagnostic timeout). Potential repeated lake allocation, list searches and merges are source-level candidates, not yet proven by per-function timings. Permanent [node progress CSV](results/03_tectonics/DRAINAGE_401_PROGRESS_03E.csv) and audit-backed scripts/workflows are archived here.

This laboratory starts with **pinned upstream source code, with an explicitly audited two-character compile-only whitespace normalization** and the author's published demo inputs. It does **not** copy the custom TISC patches or Junggar-specific geometry from `junggar-tisc-model`.

- **Upstream source**: `danigeos/tisc` at `d18b7d270f4d671b80223e10dede329ad35cafdd`.
- **Author's first quantitative test**: `tisc -Q2nd_example_load.xyp -N11/-N51 ... -qmode_interp=4`. The upstream demo README reports approximately **675.1 m (11×11)** and **711.0 m (51×51)** at the central node. These are author-supplied references, not measurements.
- **Author's project-input example**: `tisc/demo/3_flexure/` with its original `flex.PRM`, `flex1.UNIT`, `flex2.UNIT` and `flex3.UNIT` files. These are run without changing physical parameters.
- **Reproduction output**: standard logs, raw TISC output, numerical acceptance JSON, and a diagnostic cross-section inside GitHub Actions artifacts.

[Run or inspect the official flexure benchmark](https://github.com/lcxstar/tisc-mechanism-lab/actions/workflows/01_official_flexure.yml)

## Research questions

1. Can the unmodified TISC solver reproduce a published simple flexure benchmark?
2. What changes when `Te`, elastic boundary conditions or applied load are altered **one at a time**?
3. How do `fault`, `ride`, `vel_x/y`, `time_stop`, `cut_all` affect displacement, block inventory and flexural subsidence?
4. How are bedrock erosion, fluvial transport, lake deposition and **actual** sediment export recorded in mass budgets?
5. Can the original Ebro foreland basin example be reproduced before replacing geometry with North Tianshan?

## Rules

- Preserve the original upstream example first; experiment variants go into separate cases.
- Pin code version, report the exact input hash and numerical output.
- Record an expected effect **before** an experiment and label a prediction separately from observed results.
- Check stage-by-stage mass balance, local flexure and actual block movements rather than relying only on successful process exit.
- Keep physical coefficients unchanged when testing another mechanism. No hand-tuned basin subsidence to 'fix' a validation example.
- Add **no Junggar data** to this teaching repository until the independent benchmark suite passes.

## Source credit and licensing

TISC is by Daniel García-Castellanos and contributors. The original upstream license file states GNU GPL v3 for code and CC BY-SA 3.0 for non-code works. Upstream sources and example files are checked out at workflow runtime rather than re-licensed or copied into this repository. Any later redistribution of modified upstream code must follow its actual license and retain attribution.

Suggested scientific references: García-Castellanos (2002), *Basin Research* 14, 89–104, DOI [10.1046/j.1365-2117.2002.00174.x](https://doi.org/10.1046/j.1365-2117.2002.00174.x); García-Castellanos & Jiménez-Munt (2015), *PLOS ONE*, DOI [10.1371/journal.pone.0132252](https://doi.org/10.1371/journal.pone.0132252).

See [experiment notes](docs/01_flexure_reproduction.md) and [source code verification](scripts/qc_official_flexure.py).

**Lab portability findings:** pinned upstream `surf_proc.c` contains two nonbreaking spaces requiring compile-only normalization; the unmodified upstream program also dereferences a null file pointer on its first-run notification path. We avoid that path by creating `$HOME/.tiscdefaults` on the temporary CI runner. Both are reported in the experiment notes, and neither changes flexural physics.

## Experiment 02 — sensitivity of static flexure to effective elastic thickness

**Status: PASS**, [successful run](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38139533984). The official 675.1 m and 711.0 m references reproduce exactly. With only Te varied (5/20/40 km), the 51x51 center displacements are **634.4/695.4/480.2 m**, respectively, illustrating a non-monotonic response at a chosen point for this square load. [Read the numerical analysis](docs/02_te_sensitivity_results.md) and [raw permanent summary CSV](results/02_te_sensitivity/TE_SWEEP_NUMERICS.csv). Both 51x51 and 101x101 grid results passed identical pressure-field QC.

### 401x401 full coupled demo — runtime diagnostic (2026-10-11)

The **literal original 401x401, 0–15 Myr** case did **not** complete on GitHub's runner. Three attempts each reached only `T=0.0000 Myr` before the explicit 1800-second limit (exit 124). It is not a validated reproduction. The four completed 81x81 controls remain reproducible, and are now the default matrix in workflow 03; automatic 30-minute original runs were removed. An independent, explicitly modified-process diagnostic workflow 03b tests the actual bottleneck and a 121x121 intermediate-resolution full-physics case. [Investigation and caveats](notes/03b_401_timeout_investigation.md).
