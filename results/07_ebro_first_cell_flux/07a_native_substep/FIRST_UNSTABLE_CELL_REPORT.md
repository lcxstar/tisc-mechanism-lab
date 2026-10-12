# Original Ebro 208x110 surface transport: first unstable native cell

This diagnostic instrumented the **original current-source** TISC fluvial loop without changing its physics expressions; original PRM/UNIT/ZINI inputs remain byte-identical. The first 0.5 Myr tectonic step consists of 10 × 0.05 Myr surface substeps. Snapshots are from after Dtopo increment, after runoff routing, and after fluvial erosion/deposition.

**Earliest maximum exceeding 1500m:** substep **1**, time -60.0 to -59.95 Ma.

| Substep | Max pre transport (m) | Max post transport (m) | Max gain (m) | Cells above 2000m | Total deposition (kg) | Max flux (kg/s) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 1201.86 | 7518.48 | 7364.03 | 1 | 285987125212994.94 | 0.0 |
| 2 | 7518.48 | 7178.36 | 5685.87 | 3 | 289561490992451.0 | 0.0 |
| 3 | 7178.36 | 9501.92 | 9346.04 | 4 | 299367037975700.25 | 0.0 |
| 4 | 9501.92 | 8969.79 | 3730.94 | 6 | 316027676053601.06 | 0.0 |
| 5 | 8969.79 | 8501.66 | 4183.31 | 7 | 315341215382616.5 | 0.0 |
| 6 | 8501.66 | 8082.3 | 4365.91 | 8 | 322875558566757.1 | 0.0 |
| 7 | 8082.3 | 7705.23 | 7360.79 | 12 | 324513309511273.7 | 0.0 |
| 8 | 7705.23 | 10073.85 | 9913.38 | 13 | 330175372493755.44 | 0.0 |
| 9 | 10073.85 | 9478.6 | 1908.86 | 19 | 339462952108038.3 | 0.0 |
| 10 | 9478.6 | 9107.57 | 8944.15 | 20 | 339921211914983.4 | 0.0 |

## First peak cell (model Cartesian coordinates)

\`\`\`json
{
  "row": 83,
  "col": 130,
  "x_km": 396.938,
  "y_km": 119.266063,
  "after_increment_topo_m": 154.448227,
  "after_routing_topo_m": 7555.54688,
  "after_transport_topo_m": 7518.47705,
  "within_substep_topography_gain_m": 7364.028823000001,
  "receiver_row": 82,
  "receiver_col": 130,
  "runoff_discharge_m3_s": 0.114980407,
  "transported_sediment_kg_s": 0.0,
  "eroded_mass_kg": 1073581260800.0,
  "deposited_mass_kg": 0.0,
  "Dq_Pa": 160103408.0,
  "lake_id": 0,
  "type": 82
}
\`\`\`

The top 30 growth cells per step and precise 7x7 neighborhood, with receiver graph, lake identity, discharge, sediment mass and native load, are saved as CSV and GeoJSON. **Do not infer real-world longitude/latitude** from model x/y. Mass flux and accumulated mass must not be interchanged, and this diagnosis does not establish full 60 Myr scientific agreement.
