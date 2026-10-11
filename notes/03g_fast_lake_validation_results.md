# 03g — Fast lake merge optimization with pinned-author numerical validation

Date: 2026-10-11. Source provenance: `danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd`.

## Isolation, method, and safeguards

This is a dedicated **performance-only derivative** of the author's original source. The `main` branch is unchanged. All testing uses the original author's `demo/6_tectonics` inputs, with only Nx/Ny modified in the 81 and 121 grid tests.

In `Unify_Lakes()`, a generation-stamped grid-cell membership table is constructed for the destination lake once per merge. The otherwise O(existing-lake-size) duplicate search in `Add_Node_To_Lake()` is replaced only while that merge is active by O(1) membership lookup. The duplicate detection still runs; nodes appended to the lake are also stamped. Outside a merge, the original loop is left intact. The active stamp is cleared before `Deallocate_Lake()` renumbers lakes. Allocation failure falls back to the exact original scan. A 32-bit generation overflow is handled by clearing the stamp table. Lake insert ordering, physics calculations, and erosion/tectonics parameters are not altered.

The reference executable is built first from pinned upstream with only the explicitly audited two-U+00A0 compilation-only normalization. The optimized binary is compiled separately; SHA256 and the entire source diff are captured in CI artifacts.

## Paired physical-output validation

[Second CI run #38152768335](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38152768335) **PASS for all four original/optimized pairs**, including both complete 0–15 Myr coupled histories.

| Pair | Author original wall time | Optimized wall time | Speed ratio | Exported physics byte exact |
|---|---:|---:|---:|---|
| 81², first 0–0.5 Myr with flexure disabled | 2.75 s | 2.42 s | 1.136× | PASS 6/6 deterministic field files |
| 121², first 0–0.5 Myr with flexure disabled | 11.79 s | 9.56 s | 1.233× | PASS 6/6 deterministic field files |
| 81², fully coupled 0–15 Myr | 9.29 s | 8.80 s | 1.056× | PASS 7/7 deterministic field files |
| 121², fully coupled 0–15 Myr | 21.34 s | 19.02 s | 1.122× | PASS 7/7 deterministic field files |

These wall times are noisy across independent hosted CI runners; they are not a rigorous machine-normalized benchmark. The first CI run #38152541091 also observed 1.198×, 1.224×, 1.042×, 1.111× respectively, but its initial QC logic overconstrained the raw binary restart file.

### Raw binary restart-file caveat

Original `tisc/src/tiscio.c` serializes raw C structures `Blocks` and `Lake` using `fwrite(struct, sizeof(struct))`. These structures include process-specific pointers and potentially padding bytes, so `demo.all` is not necessarily bit-for-bit deterministic across two scientifically equivalent executions. In the first 81 and 121 first-step paired artifacts, the two binary files had precisely 76 differing bytes in a few narrow clusters; other deterministic physical outputs were byte-identical. The validated QC records `raw_restart_binary_byte_equal=false` instead of silently counting `demo.all` as identical. **Fully equivalent binary restart semantics have NOT been separately proven**.

### Persistent scientific caveat

Both the author and optimized *fully coupled* 15-Myr histories print `outp_seds: -nan`; this is pre-existing in reference and remains unresolved. A successful TISC exit and equivalent physical fields do **not** prove finite sediment-export mass conservation. Do not label this a complete scientific reproduction of all author processes.

## 401-grid escalation

**Actual 401 outcome (03g / 03h):** The optimized 401² 0–0.5 Myr diagnostic still timed out (exit 124 after 480 s, model remained at 0.0 Myr). Independent 03h timing found the original lake-node scan is now completed in 4.452 s, but `Calculate_Discharge()` costs 77.831 s on its first substep and still blocks on its second substep at a 150-s cutoff. **No complete author 401 reproduction.** Full evidence and next profiling design are saved in [03h results](03h_optimized_401_profile_results.md).

## Links

- [Optimization source patcher](../scripts/patch_fast_lake_membership.py)
- [Pair input audit](../scripts/prepare_03g_validation.py)
- [Exact deterministic field QC](../scripts/validate_03g_outputs.py)
- [CI workflow](../.github/workflows/03g_fast_lake_validation.yml)
- [GitHub Actions run #38152768335](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38152768335)
