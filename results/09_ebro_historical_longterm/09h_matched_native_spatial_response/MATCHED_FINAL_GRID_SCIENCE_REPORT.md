# Ebro modern versus 2017 original, matching exact geological grid and 60-Myr integration

**All 5720 native coordinate pairs matched; geological PRM/UNIT/ZINI/SVL files have identical SHA256.**

| Diagnostic at final native 0 Ma | Value |
|---|---:|
| Grid pairs | 5720 |
| RMS terrain change (m) | 676.7536585934208 |
| Max positive delta (m) | 1967.1 |
| Max negative delta (m) | -4868.2 |
| Cells changed more than 100m | 3762 |
| Cells changed more than 1000m | 438 |

This is **not** a location-by-location comparison to the archived 2016 author screen. The 2016 native spatial grid was not preserved. These experiments identify the spatial signature of changing the 2017 source to 2026 salt-fixed C source on exactly the same archived 2017 geological input. Runtime inherited defaults may also differ.

## Plots

- MATCHED_104x55_TERRAIN_SOURCE_DIFFERENCE.pdf — exact spatial difference (not interpolated)
- MATCHED_104x55_ELEVATION_DIFFERENCE_HISTOGRAM.pdf — magnitude/distribution
- MATCHED_104x55_FINAL_DELTATOPO_XYZ.csv — every matched native x/y/old height/new height/difference row
