# Original author models: full 04–09 suite accepted on numeric-execution basis

All 7 original author-supplied project setups (including TWO 5_lakes cases) were run to their original time limits with original parameter files, saved SHA256 provenance, full original native output and independent QC.

**7/7 process and finite native-grid gates passed. This is NOT proof of geological / historical numeric equality.**

| Case | Native nodes | Original time interval (Myr) | Solver |
|---|---:|---|---|
| 04_river | 10201 | 0.0 to 20.0 | audited_03t_optimized |
| 05_lake_one | 2601 | 0.0 to 0.5 | normalized_upstream |
| 05_lakes_two | 6561 | 0.0 to 1.0 | normalized_upstream |
| 06_tectonic | 160801 | 0.0 to 15.0 | audited_03t_optimized |
| 07_climate | 10201 | 0.0 to 5.0 | audited_03t_optimized |
| 08_ebro | 22880 | -60.0 to -0.0 | audited_03t_optimized |
| 09_iberia | 22419 | 0.0 to 0.1 | normalized_upstream |

Normalized upstream = compile-only NBSP whitespace change. Audited 03t = declared performance, numerical guard and nonphysical accounting diagnostics added; no author geological/transport inputs changed.

**The supplied 2016 Ebro_evol.screen differs significantly from the 2026 pinned-source reproduction** (e.g., -59.5Ma max elevation 1200.8m vs 9071.6m). Pure normalized 2026 code reproduces the latter early value. Thus Ebro execution passed, historical numeric equivalence FAILED; do not conceal this.

See full scientific report ../../docs/04_OFFICIAL_AUTHOR_DEMO_COMPLETE_REPRODUCTION.md and 08_ebro/reference_compare/ for quantitative Ebro evidence. Earlier 03t/03v 401x401 full run remains an independent numerical baseline.
