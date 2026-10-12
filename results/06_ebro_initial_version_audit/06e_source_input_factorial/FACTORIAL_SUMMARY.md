# Source-version × input-version factorial first-step audit

Historic Ebro reference is Nov 2016 TISC screen output. Our archived earliest available runnable solver is April 2017, not identical 2016 binary.
2017 original input is 104×55, dt_eros=0.025 Myr; 2026 input is 208×110, dt_eros=0.05 Myr.

| Case | -59.5 Ma max topo (m) | max load (MPa) | max deflection (m) | Exit |
|---|---:|---:|---:|---:|
| OLD2017_SOURCE__OLD2017_INPUT | 1190.9 | 4.21 | 11.7 | 0 |
| OLD2017_SOURCE__NEW2026_INPUT | 1376.2 | 25.8 | 10.6 | 0 |
| NEW2026_SOURCE__OLD2017_INPUT | 1197.9 | 9.44 | 17.1 | 0 |
| NEW2026_SOURCE__NEW2026_INPUT | 9071.6 | 195.0 | 60.3 | 0 |
| NEW2026_SOURCE__OLD2017_INPUT_AS_DEN3250 | 1197.9 | 9.44 | 17.0 | 0 |

## Controlled contrasts

- version_change_fixed_old_input_m: 7.0 m
- version_change_fixed_new_input_m: 7695.400000000001 m
- input_change_fixed_old_solver_m: 185.29999999999995 m
- input_change_fixed_new_solver_m: 7873.700000000001 m
- asthenosphere_density_default_fixed_2026_source_old_input_m: 0.0 m

No experimental model was calibrated to the historical 2016 log. Every native first-window model output and original input is archived under its own case.
