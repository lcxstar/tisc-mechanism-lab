# V08 scientific addendum — corrected TISC native .xyw column mapping

**Supersedes the numeric column interpretation in V08 08d/08e.** TISC documents original .xyw file fields as:

| Column (1-based) | Actual physical quantity |
|---|---|
| 1 | Native x (km) |
| 2 | Native y (km) |
| 3 | River/water discharge (m³/s) |
| 4 | Sediment transported mass flux (kg/s) |
| 5 | Routing/node type (non-numeric string) |
| **6** | **Terrain topography (m)** |

Older 08d and 08e compared the first three numeric columns and called the third "topography", which is wrong. The full Ebro .screen maxima, actual C salt-gate bug and on-mode bytewise .xyw equality remain valid. The status below re-evaluates all required scientific physical columns from preserved native outputs.

## Actual terrain comparisons

| Case | Grid cells | Max abs Δ topography (m) | RMS Δ topography (m) | Max abs Δ discharge (m³/s) |
|---|---:|---:|---:|---:|
| Ebro fixed default vs fixed explicit off | 22880 | 0.0 | 0.0 | 0.0 |
| Ebro original ON vs fixed ON | 22880 | 0.0 | 0.0 | 0.0 |
| Lake 1 original ON vs fixed ON | 2601 | 0.0 | 0.0 | 0.0 |
| Lake 2 original ON vs fixed ON | 6561 | 0.0 | 0.0 | 0.0 |
| Ebro corrected salt OFF vs original zero dissolved ions | 22880 | 0.0 | 0.0 | 0.0 |
| Ebro original unguarded OFF vs corrected OFF | 22880 | 5593.5 | 105.704593 | 581.06 |
| Lake1 original unguarded OFF vs corrected OFF | 2601 | 357.0 | 20.181485 | 200.27 |
| Lake2 original unguarded OFF vs corrected OFF | 6561 | 4683.8 | 339.144992 | 2899.04 |

**NEW SCIENTIFIC ACCEPTANCE = CORRECTED_NATIVE_PARITY_PASS**

## Boundary of claims

The source-localized improper salt deposition under salt_model=0 and 14 completed original-input native model runs are not undone by this post-processing error. However, old 08d/08e assertions about 22880 elevation columns should not be cited. Use this corrected addendum. The original 2016 historical peak chronology still does not match repaired 2026 source.