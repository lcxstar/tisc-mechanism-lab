# First-step controlled intervention, original current TISC source only

This suite establishes what can directly change the first half-Myr Ebro response. Original demo inputs remain intact in the baseline. Every intervention receives its own copy; all edits and SHA256 changes are declared, without altering original repository examples.

| Intervention | Final -59.5 Ma max topo (m) | 2016 difference (m) | load max (MPa) | max flexure (m) | PASS |
|---|---:|---:|---:|---:|---|
| 10_hydro_off_erosion_on | 1201.8 | 1.0 | 0.002 | 0.0 | True |
| 11_hydro_on_erosion_off | None | None | N/A | None | False |
| 12_dt_eros_0025 | 3782.0 | 2581.2 | 78.9 | 19.6 | True |
| 13_dt_eros_0005 | 1200.1 | -0.7000000000000455 | 17.7 | 11.7 | True |
| 14_dt_005_eros0005 | 1207.1 | 6.2999999999999545 | 0.296 | 10.5 | True |
| 15_no_initial_random_topo | 1198.3 | -2.5 | 1.26 | 3.9 | True |
| 16_no_fluvial_capacity | 8483.0 | 7282.2 | 182.0 | 32.2 | True |
| 17_no_topographic_diffusion | 9107.6 | 7906.8 | 195.0 | 60.3 | True |
| 18_old_2017_N104_N55_eros0025 | 1197.9 | -2.8999999999998636 | 9.44 | 17.1 | True |
| 19_old_grid_N104_N55_eros005 | 1197.9 | -2.8999999999998636 | 18.6 | 30.6 | True |
| 20_current_grid_eros0025 | 3782.0 | 2581.2 | 78.9 | 19.6 | True |

The recorded native log output is authoritative. Completion does NOT prove historical 2016 numerical equality.
Controlling an input only identifies a sensitivity; matching 2016 needs its actual executable/source or matching diagnosed algorithmic path.
Original source physics has NOT been modified beyond non-breaking space compiler normalization; not the 03t optimized baseline.
