# V08 scientific salt-module fix final acceptance

**FINAL PASS**  14/14 checked invariants.

## Regression evidence
- PASS  14_original_input_runs_exit0_finite_native_grid
- PASS  salt_on_Ebro_bytewise_native_equal
- PASS  salt_on_Lake1_bytewise_native_equal
- PASS  salt_on_Lake2_bytewise_native_equal
- PASS  fixed_off_default_equals_explicit_bytewise
- PASS  corrected_off_equals_original_zero_ions_all_22880_native_xyz
- PASS  fixed_off_removes_initial_9km_spike
- PASS  full_60Myr_patched_Ebro_valid_execution
- PASS  full_60Myr_native_22880_grid
- PASS  full_60Myr_121_printed_age_labels
- PASS  full_60Myr_no_author_input_edits
- PASS  full_original_inputs_sha256_match_pinned_upstream
- PASS  full_2016_comparison_120_numeric_printed_age_labels
- PASS  historical_2016_is_still_not_numerically_reproduced

## Original Ebro early 0.5 Myr

| Source mode | Max elevation at -59.5 Ma |
|---|---:|
| 2026 original, salt_model=0 but unguarded deposition | 9071.6 m |
| V08 salt-mode repaired, salt_model=0 | 1521.6 m |
| V08 patched source, salt_model=1 | 9071.6 m |
| 2016 historical output | 1200.8 m |

## Complete Ebro 60 Myr, original input, audited 03t + V08 source

| Ma | Author 2016 (m) | Original V04 uncorrected (m) | V08 fixed (m) |
|---|---:|---:|---:|
| -59.5 | 1200.8 | 9071.6 | 1521.6 |
| -30 | 8505.0 | 7554.1 | 7483.6 |
| -0.5 | 7537.1 | 3081.7 | 3311.6 |

RMS across 120 stages vs 2016 was 2341.0 m before salt correction and 2122.17 m after correction.

The 14 original-physics native models all completed (including 1lake and 2lakes).
Enabled salt-model output from corrected and original binaries is bytewise identical for Ebro, 1lake and 2lakes.
Both disabled mode variants are bytewise identical.
The failed cross-input strict file-hash comparison is NOT a physical failure: the independently checked original zero-ion run and corrected salt-off run are exactly equal on all 22880 native coordinate/elevation columns (zero RMS).

## Scope and limitations

- The fix isolates physical sediment salt deposition and chemical mass counters; dissolved-ion tracer arithmetic can still run without physical effect when the switch is off.
- Full 60 Myr uses the already separately audited 03t optimized variant plus this fix, not a pristine 2026 binary.
- Input SHA256 was compared independently between full repaired Ebro and short pinned original-source experiment.
- The repaired Ebro does NOT reproduce all 2016 history (at -0.5 Ma elevation remains widely different).
- Neither upstream author repository nor Junggar evolution code was changed.

## Artifacts

- Source-only patch diff and manifest: ../08b_native14/MINIMAL_SALT_MODULE_FIX.diff
- Actual fourteen forward model runs and logs: ../08b_native14
- Independent numerical native grid differences: ../08d_native_numeric_comparison/NUMERIC_NATIVE_GRID_COMPARISON.md
- Complete Ebro 60 Myr QC and raw outputs: ../08c_full_ebro_60Myr
