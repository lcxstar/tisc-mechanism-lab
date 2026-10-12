# V08 salt-module repair — actual original-input C solver regression

The two binaries differ only in the newly explicit salt_mode calculation guard and compiler NBSP normalization. All scientific TISC demo model input files remain bytewise identical.

| Native run | Maximum Ebro topography at -59.5 Ma (m) | Actual grid nodes | Exit |
|---|---:|---:|---:|
| ebro_orig_off | 9071.6 | 22880 | 0 |
| ebro_fixed_off | 1521.6 | 22880 | 0 |
| ebro_fixed_off_explicit | 1521.6 | 22880 | 0 |
| ebro_orig_on | 9071.6 | 22880 | 0 |
| ebro_fixed_on | 9071.6 | 22880 | 0 |
| ebro_orig_zero_ions | 1521.6 | 22880 | 0 |
| lake1_orig_off | None | 2601 | 0 |
| lake1_fixed_off | None | 2601 | 0 |
| lake1_orig_on | None | 2601 | 0 |
| lake1_fixed_on | None | 2601 | 0 |
| lake2_orig_off | None | 6561 | 0 |
| lake2_fixed_off | None | 6561 | 0 |
| lake2_orig_on | None | 6561 | 0 |
| lake2_fixed_on | None | 6561 | 0 |

## Strict original-on binary parity and salt-off invariants

- **patch_off_matches_explicit_off**: PASS, native SHA256 84619433a5d20161 / 84619433a5d20161
- **patch_on_identical_to_original_on_Ebro**: PASS, native SHA256 913c988f8eafd727 / 913c988f8eafd727
- **patch_on_identical_to_original_on_Lake1**: PASS, native SHA256 cbec4985d81aa4ae / cbec4985d81aa4ae
- **patch_on_identical_to_original_on_Lake2**: PASS, native SHA256 4f0dc29722a90f13 / 4f0dc29722a90f13
- **original_zero_ions_identical_to_fixed_off_Ebro**: FAIL, native SHA256 2b5422b4074dfeb1 / 84619433a5d20161

**REGRESSION PASS = False**. Failed assertions: ['original_zero_ions_identical_to_fixed_off_Ebro']

This test is NOT 2016 full-Ebro equivalence and does not certify the patched entire 60-Myr model.
