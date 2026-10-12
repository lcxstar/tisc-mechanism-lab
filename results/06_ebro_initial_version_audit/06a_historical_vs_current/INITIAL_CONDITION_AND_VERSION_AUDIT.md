# Ebro original author screen versus pinned 2026 code — forensic early-time audit

The full -60 to 0 Myr original-input experiment was already completed in v04. This independent read-only audit extracts the TISC native load, flexure, sediment and topography outputs rather than comparing only global maximum topography.

| TISC diagnostic | Author 2016 at -59.5 Ma | Pinned 2026 at -59.5 Ma |
| topography_max_m | 1200.8 | 9071.6 |
| load_now_max_pa | 3500000.0 | 195000000.0 |
| load_now_total_N | -4210000000000000.0 | 1.06e+17 |
| deflection_max_m | 10.7 | 60.3 |
| deflection_min_m | -12.0 | -14.1 |
| rain_integrated | 97500000000.0 | 3060.0 |
| sediment_volume_km3 | 2820.0 | 7780.0 |

## Inherited 2026 defaults and source flags

- Model PRM version header is TISC_2016-08-30; current template is TISC_2026-03-22_factorized_stable.
- The demo contains no Te line and no EET input. The current template defaults to 15000 m.
- densmantle=3250 is distinct from densasthen; current inherited densasthen=3200 kg/m³.
- The input parameter matrix distinguishes explicitly provided values from inherited current-template defaults. It is not a reconstruction of the original unavailable 2016 template.
- Because the 2016 binary and exact runtime default file are not archived, input versus solver version causation cannot be inferred without controlled interventions.

## Evidence

- FIRST_FIVE_TIMES_STEPWISE_2016_VS_2026.csv — 12 source-calculated physical diagnostics at first five ages.
- EFFECTIVE_INPUT_AND_DEFAULTS.csv — frozen PRM, 2026 template defaults, five original kinematic UNIT parameter heads.
- INITIAL_CONDITION_DIAGNOSTICS.json — specific observed first-step difference without any claim of proof of mechanism.
