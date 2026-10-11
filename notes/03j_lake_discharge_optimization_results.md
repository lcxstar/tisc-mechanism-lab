# 03j numerical-equivalence and first-401-timestep outcome

**Status 2026-10-11: 03j PASS for eight paired small-grid comparisons, PASS for 401×401 isolated first timestep, PASS for two nonzero-evaporation stress comparisons. Full original 401×401 0–15 Myr history is NOT yet reproduced. The upstream sediment export NaN persists.**

## Exact provenance

- Official source: `danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd`.
- Official benchmark: `tisc/demo/6_tectonics`. Input files `demo.PRM`, `demo.PRFL`, `demo1.UNIT`, and `demo2.UNIT`.
- Original `main` source baseline is never replaced. Experiments build temporary checked-out author C files with (1) compile-only U+00A0 normalization, (2) previously validated 03g lake-merge search acceleration, (3) 03j-A evaporation cache, and optionally (4) 03j-B zero-evaporation decision fastpath.
- GitHub Actions [03j primary run 38157360909](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38157360909); all nine jobs PASS. 401 [source diff, input audit, model outputs, run logs and QC artifact](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38157360909/artifacts/11709056288).
- Additional [nonzero evaporation stress tests 38157619040](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38157619040) two jobs PASS. **These are explicitly modified-author-input tests, not literal reproduction.**
- Permanent result tables are [eight paired jobs](../results/03_tectonics/03J_81_121_EQUIVALENCE.csv), [401 first timestep](../results/03_tectonics/03J_N401_FIRST_STEP.csv), and [nonzero evaporation](../results/03_tectonics/03J_NONZERO_EVAP_STRESS.csv).

## What each optimization actually does

**03j-A.** One `Calculate_Discharge` call spans a hydrology substep. Each lake evaporation sum is performed with the author's original floating-point loop and order **on cache misses only**, and saved within that substep. Whenever `Attempt_Delete_Node_From_Lake` runs, the cache's generation is advanced, so lakes changed, divided or renumbered cannot reuse stale entries. On failed allocation the exact author sum is used. Compiled source diff and SHA256 are archived.

**03j-B.** This is an intentionally narrower, proof-gated shortcut for the author's literal `evaporation=0` condition; **it is not yet a general-purpose incremental lake-inflow accumulator for arbitrary evaporation**. When an entire discharge pass begins with nonnegative finite precipitation/discharge, permeability is zero, and the nonnegative discharge invariant is verified after each routed update, a lake with exactly zero evaporation cannot satisfy `Lake_Input_Discharge < lake_evap`. In that provably false case, the expensive lake-inflow summation is skipped. If evaporation is nonzero, the code invokes `Lake_Input_Discharge` exactly as upstream; any negative/invalid discharge permanently disables the fastpath until the next substep. This preserves control flow and floating summation order for calculations actually needed.

## Eight paired 81×81 / 121×121 results

All eight passed exact output SHA256 comparisons for scientific text/raster outputs against the **03g validated executable** with byte-identical physical input files, and identical logged time histories. Independent `demo.all` raw binary SHA values are not a scientific identity gate because upstream serializes native pointer-bearing C structs, so full restart semantics remain unverified.

| Variant | Grid | Mode | Reference s | Optimized s | Speedup |
|---|---|---|---:|---:|---:|
| 03j-A | 81 | 0–0.5 Myr, flexure off | 2.42 | 1.97 | 1.23× |
| 03j-A+B | 81 | 0–0.5 Myr, flexure off | 2.42 | 0.91 | 2.66× |
| 03j-A | 121 | 0–0.5 Myr, flexure off | 11.37 | 9.20 | 1.24× |
| 03j-A+B | 121 | 0–0.5 Myr, flexure off | 9.63 | 3.57 | 2.70× |
| 03j-A | 81 | 0–15 Myr, all author physics | 8.82 | 8.26 | 1.07× |
| 03j-A+B | 81 | 0–15 Myr, all author physics | 8.79 | 6.21 | 1.42× |
| 03j-A | 121 | 0–15 Myr, all author physics | 35.93 | 32.73 | 1.10× |
| 03j-A+B | 121 | 0–15 Myr, all author physics | 35.74 | 22.98 | 1.56× |

Runtimes depend on GitHub runner load. Benchmarks are observed results, not deterministic performance guarantees.

## 401×401 breakthrough

Using *byte-for-byte original author PRM/UNIT/PRFL inputs*, the optimized solver on the isolated flags
`tisc demo -V1 -tf0.5 -qisost_model=0 -qplotting_mode=0`
ran to completion, **exit 0**, in **71.78 s**. All **ten of ten** hydrological 0.05 Myr substeps finished; the model advanced from 0 to **0.5 Myr**. The 03j-B guard skipped **1,605,950** demonstrably unnecessary full-lake inflow queries.

This is the FIRST full 401×401 0.5 Myr surface-routing timestep recorded in this lab after the earlier 03f/03g/03i timeouts. However, the original 401 model includes flexure (isost_model=1) and a 15 Myr history, and in this performance experiment flexure was disabled deliberately. **This is NOT full author-model reproduction.**

The original-style mass balance log reports `outp_seds: -nan` after the 401 pass, although the provided `demo.xyw`, `demo.st`, `demo.hrz`, `demo.lak`, `demo.bas` exported text files contain no literal NaN/Inf tokens. The export-level absence of NaN is insufficient to certify sediment conservation; it requires a separate audit. In the 81/121 full-history experiments the SAME NaN existed in baseline and optimized runs, therefore it was **not fixed** by 03j.

## Nonzero evaporation regression

To test fallback behavior rather than rely only on the author's zero-evaporation demo, synthetic N81 first-step variants set `evaporation` to 100 and 1000 mm/yr **in both reference and optimized inputs**. The rest of the author input remains unchanged. Both matched all compared forward physics output files byte-for-byte.

- 100 mm/yr: 65,360 original lake-inflow predicates executed; no 03j-B skips. 03j-A cache has 68,540 hits and no invalidations. The first step completed.
- 1000 mm/yr: 60,694 original predicates executed; 51,388 lake cache invalidations reflecting high lake mutation activity. Still the original and optimized outputs matched exactly; the baseline *and* optimized output logs reported a sediment NaN. No B shortcuts applied.
- Under high evaporation, 03j-A+B did **not** accelerate the first step (4.53 vs 4.59 s): this is expected because the expensive original live inflow calculation is retained when lake evaporation is nonzero.

## Gate for the next project phase

03j is a bounded optimization/validation milestone, not finished geological reproduction. Next, isolate sediment `outp_seds=-nan` through mass transfer tracing, then test the optimized 401 grid with original flexure enabled, then run the full original 401-grid 0–15 Myr demonstration. If fully general fast lake-inflow accumulation is desired for **nonzero** evaporation, build it as a separate, stricter algorithmic change with additional equivalence and balance tests, not by globally freezing a lake's inflow value.
