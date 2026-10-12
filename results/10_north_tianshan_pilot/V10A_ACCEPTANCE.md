# North Tian Shan → South Junggar static flexural mechanism gate — PASS

**Scope:** idealised pinned-author TISC -Q, NOT Junggar late-Cenozoic forward reconstruction.
**Provenance:** source d18b7d270f4d671b80223e10dede329ad35cafdd, only two NBSP compile whitespace normalisations.

The x/y axes are **model-local km**, with the north direction +y and nominal
mountain front y=0 km. Input parameters are **test hypotheses**, not measured
topography, true thrust kinematics, basin age or lithospheric strength.

## Numerical and mechanism gates
- PASS all_cases_numerically_complete
- PASS author_N11_reference
- PASS author_N51_reference
- PASS zero_load_zero_deflection_under_0p2m
- PASS mountain_pressure_and_northern_basin_response
- PASS linear_load_response_0p5_under_1m_residual
- PASS linear_load_response_1p5_under_1m_residual
- PASS shifted_load_changes_basin_response
- PASS coarse_refined_rms_recorded

## Key numbers (not field-calibrated)
- Foreland maximum downward flexure in 0–150 km strip: **178.7 m**.
- Static half-pressure residual against linear half response: **0.05 m**.
- Static 1.5-pressure residual: **0.10 m**.
- Coarse-vs-refined center transect RMS: **17.11797772198348 m**.
- Grounded geological direction is from published N Tian Shan / southern Junggar structure only.
  The reported ~3.1 mm/yr 22–16 Ma forebulge migration is **not** assumed equal to load movement.
- No erosion, sediment, lakes, time integration, tectonic slip or thermal coupling is simulated.

## Preserved outputs
- V10A_CASE_METRICS.csv, V10A_CENTERLINE_TRANSECTS.csv
- V10A_NUMERIC_QC.json
- V10A_NORTH_SOUTH_TRANSECTS.pdf and V10A_FLEXURE_MAP.pdf when plotting succeeds
- per-case .xyp, exact CLI and gzip-compressed native -Q output.
