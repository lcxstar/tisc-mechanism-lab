# 03k — First nonfinite sediment transfer, source-domain defect, and 401 coupled validation

## Reproduction status

The entire original-author **401×401 × 0–15 Myr** coupled model was genuinely *launched* with default flexure in [03k baseline workflow 38157980373](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38157980373). An independent [experimental domain-corrected 401 coupled run 38158590091](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38158590091) was also launched, gated by successful N121 full-history and N401 first-timestep tests. Both full-duration workflows have separate, automatic exit-time/elapsed-time QC and artifact archival. **Do not infer completion of 15 Myr merely from the job having started or from a green workflow wrapper.** Detailed run outcomes must be taken from `03K_COUPLED_RUN_QC.json` or `03K_EXPERIMENTAL_FIX_QC.json` in the artifacts.

The first **0.5 Myr** of the original 401 grid with its original `isost_model=1` and `Te=25 km` in `demo.PRM` **HAS completed, exit 0, 72.64 s**, without any runtime override switching flexure off. No geological input values were altered. The C hydro algorithm is separately optimized via validated 03g+03j patches. A nonfinite sediment-export statistic persisted.

## Actual first nonfinite source, independently confirmed twice

Instrumented source [first-NaN run 38158131141](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38158131141) and [fractional-slope proof 38158334902](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38158334902) examine the original author's `tisc/src/surf_proc.c` at immutable commit `d18b7d270f4d671b80223e10dede329ad35cafdd`. No physics source edits were made in those two diagnostic builds. Source diffs and SHA256 audits are retained.

| Observation | N121 first NaN, full coupled | N401 first NaN, isostasy isolated |
|---|---|---|
| Earliest surface-process substep | 0 | 0 |
| Grid coordinate (row, column) | (19, 120), east outlet | (400, 151), south outlet |
| Drainage type | E (lake outlet) | E |
| Downstream destination | (-9999,-9999), model edge | (-9999,-9999), model edge |
| Measured upstream slope | −1.83105475227 × 10⁻⁹ | −6.10351547081 × 10⁻⁹ |
| Fractional stream-power exponent `spl_n` | 1.04999995232 | 1.04999995232 |
| Water discharge | 211.852081299 m³/s | 4.27552843094 m³/s |
| Transferred sediment rate prior to bad calculation | 0 | 0 |
| Sediment output after event | NaN | NaN |

The relevant original code is `Fluvial_Transport`, `erosed_model = 6`, where `pow((double)slope, (double)spl_n)` uses an approximately **1.05 fractional exponent**. `slope` is assigned `main_tribut_slope` when the destination lies outside the domain, and the original main-tributary slope expression uses `topo[current] - topo[contributing_upstream_node]`, negative for physically higher contributing upstream cells. Negative-to-fractional-power creates a floating-point NaN. The bad `d_mass` becomes `drainage[row][col].masstr` and immediately contaminates the cumulative boundary export `total_lost_sed_mass` (`outp_seds=-nan`). Therefore **the final summary does not create the NaN; it reports an upstream undefined floating-point operation**.

[First-event measured CSV](https://github.com/lcxstar/tisc-mechanism-lab/blob/v03k-full401-sediment-audit/results/03_tectonics/03K_NAN_FIRST_NODES.csv).

## Candidate physical correction — kept separate from author's source

The branch `v03k-slope-guard-experiment` adds **one deliberate physics-domain correction** in its ephemeral compiled derivative. Inside model-6 incision and ONLY for `slope < 0`, replace the fractional-power slope input with zero. This avoids imaginary/non-real values, interpreted as no physical incision contribution from an uphill/non-downhill slope. The compiled source preserves the original operand for nonnegative finite slopes. NaN inputs are *not* silently treated as zero. Full source patch, audit and hit-counter are saved in each experimental artifact. This is **NOT byte-identical upstream physics** and is not automatically the final approved geoscientific choice.

## Controls already passed

1. Original author 401 grid, `isost_model=1`, `Te=25 km`, 0–0.5 Myr, optimized hydro but uncorrected erosion — exit0, time0.5, 72.64 s, 1 sediment-export NaN occurrence in final summary.
2. Candidate corrected model, 121 grid, *original 0–15 Myr coupled physics settings except source guard* — exit0, all 30 main steps, 300 hydro substeps, **0 nonfinite sediment-export statements**, 550 negative-slope guard events.
3. Candidate corrected model, 401 original inputs, 0–0.5 Myr *with isostasy enabled* — exit0, all ten hydro substeps, **0 nonfinite sediment-export statements**, ten guard events.
4. Direct binary comparison of `demo.xyw`, `demo.st`, `demo.hrz`, `demo.bas`, `demo.lak` against the corresponding previous 03j uncorrected outputs found **all five scientific published output files SHA256-exact at N121 0–15 Myr and at N401 0–0.5 Myr**. This establishes tested published forward fields were unchanged by the narrowly targeted domain guard, even though the mass-export accounting became finite. It does NOT prove internal restart state equivalence; `demo.all` serializes pointer-bearing C structures.
5. 121 corrected full simulation printed 30 finite mass-budget records. The largest absolute normalized budget residual calculated from the author's rounded console values was ~2.22%; full-precision conserved mass accounting has **not** been established and must not be claimed.

[Experimental corrected results table](../results/03_tectonics/03K_EXPERIMENTAL_GUARD_VALIDATION.csv).

## Recommended next scientific checks

- Inspect final 401 full-history coupled results **when explicitly observed**. Accept only exit0, last logged `T=15`, complete output arrays, and finite sediment export; treat a GitHub Actions job marked successful after `timeout` as NOT a completed model.
- Quantify precise mass conservation using internal full-precision accumulators rather than three-digit printed values. Verify 401 and 121 topography, tectonic deformation, sediment thickness, boundary export vs. time.
- Independently assess the scientifically correct treatment of `main_tribut_slope` at no-downstream model outlets. The current guard is a safe domain correction, not a blanket endorsement of the author's boundary erosion physics. Compare a sign-convention fix as a separate experiment if interpreting erosion near the domain boundary.
- After full 401 validation, begin the original `6_tectonics` geological-mechanism reproduction review and compare actual unconstrained processes rather than tuning Junggar input parameters prematurely.
