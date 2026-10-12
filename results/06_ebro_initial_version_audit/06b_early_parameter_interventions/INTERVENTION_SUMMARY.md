# First-step controlled intervention, original current TISC source only

This suite establishes what can directly change the first half-Myr Ebro response. Original demo inputs remain intact in the baseline. Every intervention receives its own copy; all edits and SHA256 changes are declared, without altering original repository examples.

| Intervention | Final -59.5 Ma max topo (m) | 2016 difference (m) | load max (MPa) | max flexure (m) | PASS |
|---|---:|---:|---:|---:|---|
| 00_clean_source_baseline | 9071.6 | 7870.8 | 195.0 | 60.3 | True |
| 01_Te_25km | 9071.6 | 7870.8 | 195.0 | 53.3 | True |
| 02_asthenosphere_3250 | 9071.6 | 7870.8 | 195.0 | 59.4 | True |
| 03_Te25_rho3250 | 9071.6 | 7870.8 | 195.0 | 52.6 | True |
| 04_hydrology_erosion_off | 1201.9 | 1.1000000000001364 | N/A | None | True |
| 05_unit1_initial_velocity_zero | 9071.6 | 7870.8 | 195.0 | 60.3 | True |
| 06_defer_unit1_load_to_minus58 | 8085.9 | 6885.099999999999 | 174.0 | 45.8 | True |
| 07_delay_all_tectonic_units | 8085.9 | 6885.099999999999 | 174.0 | 45.8 | True |
| 08_dt_005 | 5246.5 | 4045.7 | 3.48 | 38.0 | True |
| 09_unit1_initial_ramp_thickness_1000m | 8920.9 | 7720.099999999999 | 192.0 | 58.2 | True |

The recorded native log output is authoritative. Completion does NOT prove historical 2016 numerical equality.
Controlling an input only identifies a sensitivity; matching 2016 needs its actual executable/source or matching diagnosed algorithmic path.
Original source physics has NOT been modified beyond non-breaking space compiler normalization; not the 03t optimized baseline.
