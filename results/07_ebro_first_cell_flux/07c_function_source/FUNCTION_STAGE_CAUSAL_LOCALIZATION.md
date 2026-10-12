# Ebro 208×110: exact routine boundary of first anomalous grid elevation

Cells are TISC local Cartesian x/y coordinates, NOT geographic lon/lat.

| Stage | Max z (m) | Cells z>2000 m | Max positive jump from previous stage (m) |
|---|---:|---:|---:|
| after_increment | 1201.859 | 0 | 0 |
| after_sort_topography | 1201.859 | 0 | 0.0 |
| after_define_drainage | 1201.859 | 0 | 0.0 |
| after_rain_evap | 1201.859 | 0 | 0.0 |
| after_ice_water | 1201.859 | 0 | 0.0 |
| after_custom_node_defs | 1201.859 | 0 | 0.0 |
| after_routing | 7555.547 | 1 | 7401.099 |
| after_transport | 7518.477 | 1 | 1563.431 |

**First supra-1500 m appears at after_routing**. Top 60 actual grid cells and incremental mass/load/discharge diagnostics in CSV.

This is a routine-level cause localization. A positive terrain change during hydro network processing does not by itself imply physical sediment deposition; compare per-routine mass edits and follow up at line/function granularity.
