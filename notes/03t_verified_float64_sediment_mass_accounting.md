# 03t verified correction — apparent missing sediment mass caused by float32 accumulation

## Scientific verdict

The previously observed **33–34%** sediment-budget deficit in the original author's **401×401** `6_tectonics` example is demonstrably dominated by loss of significance in the *aggregate bookkeeping accumulator*, not disappearance of this amount from the fluvial sediment-transfer stream.

The author defines `float total_sed_mass`, `float total_bedrock_eros_mass` in `tisc/include/tisc.h`'s `ModelContext` and globally in `tisc/src/globals.c`. `Sediment()` adds every local deposit to `ctx->total_sed_mass`. On large lakes this executes millions of small additions into a total already at ~10¹⁴–10¹⁵ kg, below float32's half-ULP. An enormous number of valid local increments leave the counter unchanged, despite the same call updating the sediment block thickness and associated physical fields.

### Source and execution provenance

- Immutable pinned author: `danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd`.
- Original demo: `tisc/demo/6_tectonics`, true 401×401, 0–15 Myr, original `isost_model=1`.
- Previous controlled modifications: independently validated 03g+03j computational algorithm acceleration and the explicitly labeled 03k negative-slope fractional-power domain correction. No parameters tuned.
- [03q mass substep tests](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38164401388), [03r lake transfer receiver](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38164687015).
- [03s original float32 vs independent float64 ledger verification](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38164926540). Both 121 full-history and 401 first 2 Myr jobs PASS.
- [03t full history N121 and 401 first-2-Myr corrected print tests](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38165200144). N121 PASS; N401 0–2 Myr PASS (each 7 field outputs byte-exact), per GitHub workflow 38165200144.
- [03t complete 401×401 15-Myr coupled full test](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38165304319). Treat any in-progress run as NOT yet scientifically accepted. The workflow requires completion and a maximum corrected-budget error less than 0.001%.

### Direct source-level localization

At the row146 col130 river node (main timestep 1.0 Myr), before the local deposit the source has `masstr=0.18883417547 kg/s`. `d_mass=-15,543,129,088 kg` is deposited by `Sediment`; this local stage has only ~−2.61×10⁷ kg of 32-bit rounding error, within original float counter precision at the existing total. Immediately after transferring the remaining `0.17898327112 kg/s` to the downstream **open lake** `type='L', ilake=1, n_sd=43`, the native ledger diverges by +8.1288×10¹⁰ kg.

Inside `Lake_Fill`, the suspended inflow decreases from 0.17898327112 to 0.00099984137 kg/s. The ordinary 32-bit global total increases by only ~1.995×10¹¹ kg, even though the rate reduction represents ~2.809×10¹¹ kg. The discrepancy is explained by lake-wide repeated small sediment additions that fall below the native float32 accumulator resolution.

The earlier suspicion that simple closed-lake clearing caused the apparent loss was **disproved**: this destination is an OPEN lake (43 outlets), and the tracked closed-lake clearing term is zero. The ordinary-river node itself is locally conservative; the inaccurate **global accumulation** appears during distributed lake deposition.

### Controlled independently audited float64 ledger, 03s

03s adds static double observers in the temporary compiled source. They are reset at each `Surface_Transport` call and follow all existing native code sites in `Sediment`, sedimentary re-erosion in `Erode`, bedrock/basement erosion in `Erode` and the two open-lake/domain-boundary sediment export sites in `Fluvial_Transport`. Original numerical state and physics computations are not altered. Counters track each time a positive/negative sediment addition leaves the native float32 total unchanged.

| Grid and stage | Native float32 absolute balance error | Independent float64 absolute balance error |
|---|---:|---:|
| 401, first 0.5 Myr | 0.729404% | 0.000007056% |
| 401, 1.0 Myr | **33.643619%** | **0.000007660%** |
| 401, 1.5 Myr | **33.842328%** | **0.000000513%** |
| 121, full 15-Myr run, maximum over stages | **2.292665%** | **0.000012695%** |

At 401 1.5 Myr, **170,732,357** native `total_sed_mass` additions left the float32 accumulator unchanged; the sum of their individual signed masses is of order 1.064×10¹⁵ kg. This is a decisive numerical demonstration of the source.

### Strict forward-physics equivalence gate

Seven output products were compared byte-for-byte against their **03k scientific domain-corrected but otherwise uninstrumented** counterparts:

- N121 0–15 Myr: `demo.xyw`, `demo.st`, `demo.hrz`, `demo.lak`, `demo.bas`, `demo.pfl`, `demo.xyzt` — **all seven identical**.
- N401 0–2 Myr: the same seven output files compared against the independent 03m 401 first2 full-coupled source run — **all seven identical**.

Thus adding observers had NO effect on these physical outputs. This does not test binary `demo.all` restart equivalence: TISC currently serializes pointer-bearing C structs.

### 03t minimal corrective code and scope

`scripts/patch_03t_correct_sediment_balance.py` applies on top of 03s. It switches ONLY the printed `eros_nosd`, `sedim_inc`, `outp_seds` and `sediment_balance` warning calculation to the independently validated float64 ledger, and adds a high-precision `TISC_03T_CORRECTED_BALANCE` diagnostic line.

**The patched source does not change water routing, lake filling, erosion/deposition masses, model parameters, native float counters, serialized restart format, block geometry, or source equations.** This is a precise correction of apparent loss in the *reported budget*, not artificial addition of a source mass or tuning a physical law.

`tisc/include/tisc.h` is deliberately NOT modified to replace `float ModelContext` fields with `double`, since that would change the ABI and could corrupt existing binary restart compatibility. Users of the original float context fields outside this reporting path should use the audited float64 ledger if they need accurate sediment flux accounting.

### Acceptance and limitations

- 03t N121 full 0–15 Myr test **PASS**, max corrected sediment balance 0.000012695% (versus native 2.292665%).
- 03t N401 0–2 Myr **PASS**, max corrected sediment balance error 0.000007659607% (versus native 33.8423276195%), all seven compared forward physical output files byte-exact versus 03m unmodified scientific case. Full N401 0–15 Myr must still pass actual CI completion and 30 printed step records; do not claim full pass before that finishes.
- The float64 source ledger closes to ~1e−7 relative error in tested cases. This establishes conservation of the **code's sediment source/sink/export transactions** to numerical precision.
- A deeper physical audit should still compare total mass reconstructed from *stored sediment block thickness and densities* over the grid, because float32 block storage, compaction and rock-density conversions can introduce separate, smaller numerical discrepancies. Passing the ledger is not evidence that the full physical state has exact mass conservation in every reservoir.
- The 121/401 final sediment-volume difference (~15.5%) remains a separate **grid-convergence problem**, not fixed by the accounting correction.

**Decision:** The dominant 33–34% mass discrepancy is SOLVED as float32 bookkeeping loss. This is distinct from verifying geological sediment volumes or full 401 grid convergence, which remain separate scientific validation tasks.

### 03t conclusive regression gates

- [Official two-case corrected workflow 38165200144](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38165200144) both jobs green, zero process exit and sediment mass balance below the independently set **0.001%** threshold.
- 121 corrected full 15 Myr: 30 accepted records; peak |balance| = **0.00001269480098%**; all seven physical output files SHA256-exact to 03k baseline.
- 401 corrected first 2 Myr: four accepted records; peak |balance| = **0.00000765960705%**; all seven physical output files SHA256-exact to prior 03m fixed-physics benchmark.
- The correction remains **accounting only**. It does not modify stratigraphic production and does not improve the separate 121-vs-401 volume-resolution consistency.
