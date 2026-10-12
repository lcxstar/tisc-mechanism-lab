# Original author TISC demo commands — independent execution ledger

Date: 2026-10-12. Junggar forward model is paused. Benchmarks pinned to danigeos/tisc commit d18b7d270f4d671b80223e10dede329ad35cafdd. All supplied original input files remain unchanged.

## Confirmed commands

| Author instruction | Completion / scientific limits |
|---|---|
| -Q1st_example_load.xyp -N11 -qmode_interp=0 | PASS, 675.1 m centre, equals compact-load mode4 across native grid |
| -Q2nd_example_load.xyp -N11 -qmode_interp=4 | PASS, 675.1 m centre |
| -Q2nd_example_load.xyp -N51 / -N101 | PASS, 711.0 / 712.2 m centre |
| tisc flex | PASS, official project, already archived in experiment 01 |
| tisc flex -T5000 | PASS, 141 x 141 / 0–9 Myr, [variant](../results/05_readme_variants/flex_project_T5000/) |
| tisc conic_island -tf10 | PASS, 101 x 101 / 0–10 Myr, [variant](../results/05_readme_variants/conic_island_tf10/) |
| tisc 2lakes | PASS, author's unchanged 81 x 81 / 0–1 Myr, [original](../results/04_09_official_demo_suite/05_lakes_two/) |
| tisc demo | PASS, original 401 x 401 / 0–15 Myr with audited 03t source variant, [original](../results/04_09_official_demo_suite/06_tectonic/) |
| tisc sinusoidal | PASS, author 101 x 101 / 0–5 Myr [original](../results/04_09_official_demo_suite/07_climate/) |
| tisc Ebro_evol | EXECUTION PASS 208 x 110 / -60–0 Myr; NUMERICALLY DIFFERS FROM AUTHOR 2016, [historic difference](../results/04_09_official_demo_suite/08_ebro/reference_compare/EBRO_AUTHOR_SCREEN_COMPARISON.md) |
| tisc Ebro_evol -qerosed_model=0 -qhydro_model=0 | PASS, no-surface 60 Myr [variant](../results/05_readme_variants/ebro_without_surface/); [same-source history comparison](../results/05_readme_variants/ebro_surface_process_isolation/EBRO_SURFACE_OPTION_QC.md) |
| tisc Iberia_present | PASS, 159 x 141 / 0–0.1 Myr, [original](../results/04_09_official_demo_suite/09_iberia/) |
| The author -Pc image-generation instructions | Legacy GMT4/ImageMagick route not yet run; [all seven original native fields have modern SVG-free PNG and vector PDF](../results/05_readme_variants/author_native_figures/) without changing TISC input or state |

## Three original-author restart examples, not new forward starts

The original demo README instructs using a REAL serialized demo.all state and -F restart, then changing velocity or block ordering. This is NOT equivalent to running three independent fresh PRM files.

1. tisc demo -F -v-2850/3.14/31.4 -tf20
2. tisc demo -F -v3/2.17/21.7 -tf25
3. tisc demo -F -S1/1 -tf30

Status: [separately running original 401-grid, 15-Myr checkpoint + restart variants](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38229155504). The third README command contains duplicated, incomplete -tf token, removed in executed syntax and fully disclosed. Do not count the tests as accepted until original baseline, checkpoint SHA, correct resumed timeline and actual native 401-grid outputs are independently verified. [Read-only audit script](../scripts/audit_05_official_tectonic_restarts.py) is retained for results produced by this workflow.

## Critical historic Ebro mismatch

Author's bundled TISC_2016-08-30 history differs substantially from today's pinned executable and model input. At -59.5Ma the native author saved log reports 1200.8m maximum surface height, while modern pinned code yields 9071.6m. A compile-whitespace-normalized original current source (with no 03t acceleration) produces the same 9071.6m. **Numerical execution succeeds but author 2016 equivalence does not.** Cause between the historical executable, inputs and current repository code remains unverified.

## Important provenance distinction

Normalized upstream = author source with only compiler-incompatible NBSP whitespace normalized. Audited 03t = explicit performance patches, slope guard and corrected diagnostic mass accounting; geological and climate PRM/UNIT/ZINI inputs are identical to author examples. This suite validates command execution and input preservation, NOT real-world tectonic history or physical equivalence in every source revision.

All seven original project cases are permanently archived on the [completed v04 branch](https://github.com/lcxstar/tisc-mechanism-lab/tree/v04-official-demo-completion/results/04_09_official_demo_suite); v05 contains only supplementary author README commands, figures and checks.
