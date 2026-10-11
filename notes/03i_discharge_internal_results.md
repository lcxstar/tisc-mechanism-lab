# 03i — Internal timing of Calculate_Discharge

**11 October 2026. Status: profiling completed (both GitHub Actions jobs green). The 401×401 author demonstration is STILL NOT reproduced.** Workflow success means that the bounded profiling jobs collected evidence, not that the forward model completed.

### Fully traceable run

- [GitHub Actions run 38155859997](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38155859997).
- [121 diagnostic artifact](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38155859997/artifacts/11708532595), with full `RUN.log`, two progress CSVs, QC JSON, exact source SHA256 and diffs.
- [401 diagnostic artifact](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38155859997/artifacts/11707959854), with the equivalent 119 diagnostic checkpoints.
- [Permanent 121 data, all ten 0.5-Myr hydrology substeps](../results/03_tectonics/03I_N121_DISCHARGE_SUBSTEPS.csv).
- [Permanent 401 data, two completed and one interrupted hydrology substeps](../results/03_tectonics/03I_N401_DISCHARGE_SUBSTEPS.csv).

Upstream pinned at `danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd`. Physical inputs are from the author's `tisc/demo/6_tectonics`: the 401 grid files are byte-for-byte identical; the 121 grid changes Nx and Ny only. Both benchmarks use `tisc demo -V1 -tf0.5 -qisost_model=0 -qplotting_mode=0`. Flexure and plotting are disabled for **diagnostic isolation**; hydrology and erosion remain from the author. Source in CI is the separate 03g merge-only optimized derivative, plus 03d/03e/03i profiling; the original author code is not directly edited on main. Full source diffs are in each artifact.

### 401×401 observations

A 210-second bounded 401-grid test finished **2 of the required 10 surface-process substeps** for the first 0.5 Myr. The **3rd substep** was interrupted after **122,880 of 160,801 nodes**, so the model still reported **T=0 Myr** and has not advanced to the end of the first timestep.

| Measurement | First complete discharge substep | Second complete discharge substep | Third, last checkpoint |
|---|---:|---:|---:|
| Discharge elapsed | 67.577355 s | 67.762329 s | 50.982202 s |
| Evaporation + lake-inflow **precheck**, inclusive | 66.670392 s | 66.848958 s | 50.943985 s |
| Of precheck: `Lake_Input_Discharge`, nested | 45.861940 s | 46.024397 s | 34.724753 s |
| Lake input queries | 162,194 | 162,194 | 122,674 |
| Lake nodes visited by lake input helper | 26,047,545,430 | 26,047,545,430 | 19,700,831,030 |
| Outlet rain scan | 0.197528 s | 0.201882 s | 0.003314 s |
| Outlet evaporation | 0.665395 s | 0.667308 s | 0.003341 s |
| Attempted lake deletions | 0 | 0 | 0 |

**Measured diagnosis:** in the first complete substep, **98.66%** of the elapsed discharge time was spent in per-node lake prechecks (66.670/67.577 s), and **67.86%** of the total was directly timed inside `Lake_Input_Discharge` (45.862/67.577 s). The remainder of the precheck, ~20.81 s, largely corresponds to the author's direct summation of lake evaporation over every lake node. The helper sum itself visits a **160,595-node lake approximately 162,000 times per substep**. This is a demonstrated O(number-of-processed-nodes × lake-size) pattern, not a stalled worker.

These numbers are **inclusive** timings: do NOT add the `Lake_Input_Discharge` 45.86 s to the precheck 66.67 s. The helper's count includes one call from the final lake check beyond the completed node scan (162,194 vs 162,193 in the scan).

### Independent 121×121 confirmation

The smaller 121 grid completed all **10 hydrology substeps** and exited zero. Across all ten substeps, the discharge routine spent **6.237038 s** in total, including **5.951876 s** inside lake precheck, of which **4.325134 s** was separately timed in `Lake_Input_Discharge`. The helper was invoked **150,830 times** and traversed **2,202,570,490 total lake nodes**, even though the grid contains only 14,641 cells. No lake-node deletion attempts were observed. The last substep breakdown was 0.631015 s total, 0.602076 s precheck, 0.437181 s lake input helper.

### What is NOT diagnosed / validated here

1. Neither original 401-grid 0–15 Myr nor optimized first 0.5 Myr is fully finished. The cutoff is a controlled test, not a successful physical simulation.
2. Instrumentation increases measured wall time modestly; comparisons of runner wall times must not be treated as deterministic speedup factors.
3. Raw restart `demo.all` is not byte-equivalent across separately compiled runs because TISC serializes pointer-bearing structs; 03g validated the publicly exported forward physics fields, not complete restart semantic equivalence.
4. The pre-existing sediment export `-nan` in some full-history 81/121 runs remains a **separate** numerical/physical issue. Do not infer it is solved from successful profiling.
5. Lake influx is a **time-varying aggregate during node-by-node water routing**. Caching a single scalar for the whole substep would generally be physically wrong.

### Recommended 03j, not part of 03i

Test two isolated optimizations separately. **A** cache per-lake evaporation sums with invalidation whenever lake membership or evaporation changes. **B** explore an incremental lake-inflow accumulator that is updated consistently on every upstream transfer, rather than summing a lake of 160k nodes each time. For both, compare against the existing 03g validated solver on 81/121 in short-step and full-history configurations, require output-field equivalence and no new non-finite values, then test first 401 step and finally the full coupled official demo. Never skip a numerical equivalence gate solely to reduce runtime.
