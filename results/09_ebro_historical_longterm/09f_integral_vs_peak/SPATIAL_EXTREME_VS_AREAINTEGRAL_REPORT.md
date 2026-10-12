# Ebro 2016 historical screen versus earliest 2017 solver — integrated topology diagnosis

The full 60Myr author 2016 historical output and the first Git-upload 2017 solution differ dramatically in **maximum topography**, but the **signed area integral of modeled topography** remains relatively close at several time steps.
 Do not mistake the maximum-magnitude mismatch for spatially uniform basin error.

| Age | 2016 peak (m) | first upload 2017 peak (m) | 2016 topo-area (m³) | first upload 2017 topo-area (m³) |
|---|---:|---:|---:|---:|
| -59.5 | 1200.8 | 1190.9 | 123000000000000.0 | 123000000000000.0 |
| -50 | 3284.2 | 2027.9 | 133000000000000.0 | 137000000000000.0 |
| -35 | 6581.5 | 3246.7 | 201000000000000.0 | 211000000000000.0 |
| -30 | 8505.0 | 3157.2 | 244000000000000.0 | 251000000000000.0 |
| -20 | 5734.9 | 3945.1 | 230000000000000.0 | 241000000000000.0 |
| -10 | 7002.9 | 2222.5 | 118000000000000.0 | 129000000000000.0 |
| -0.5 | 7537.1 | 1872.9 | 126000000000000.0 | 127000000000000.0 |

The locations of the highest points cannot be checked against the archived 2016 **spatial** output, which was not preserved. Therefore the source of the individual high peak is not fully identified. Comparable elastic flexure and signed topology integral narrow, but do not prove, a nonlinear surface routing/erosion/peak-retention hypothesis.

## Saved PDF graphics

- TOP_HEIGHT.pdf — topography max time series
- INTEGRATED_HEIGHT.pdf — signed topology height-area integral
- MAX_FLEXURE.pdf — maximum elastic deflection
- MAX_RAINFALL.pdf — maximum precipitation
- SEDIMENT_DIAGNOSTIC.pdf — printed modeled sediment volume

## Critical numerical caveat

2016 and 2017 printed physical quantities may share names but not all implementation semantics. Use consistent dimensions, avoid treating the terrain-integral as observed basin net subsidence or mass balance.
