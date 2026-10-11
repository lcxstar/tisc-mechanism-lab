# Experiment 03 | TISC official 6_tectonics: replication + kinematics

## Scope and provenance

- Pinned author's code: danigeos/tisc @ d18b7d270f4d671b80223e10dede329ad35cafdd.
- Official inputs copied from upstream tisc/demo/6_tectonics: demo.PRM, demo.PRFL, demo1.UNIT, demo2.UNIT.
- Full original input geometry is 401 x 401 nodes (model domain: x=-150...350 km; y=-250...250 km).
- Author UNIT1: time 0 Myr, fault=1, vel_x=10 km/Myr, time_stop=10 Myr.
- Author UNIT2: time 6 Myr, fault=1, vel_x=10 km/Myr, time_stop=12 Myr, ride=1.
- The default PRM has Te=25 km, dt=0.5 Myr, hydrology 1, erosion/sedimentation model 6, final time 15 Myr.

## Controlled matrix

| Case | Input modification relative to author | Interpretation |
|---|---|---|
| original_401 | NONE, exact copies | Literal published demo baseline, full 401x401 |
| baseline_81 | Only Nx and Ny reduced to 81 | Mechanism comparator at fixed resolution |
| ride0_81 | baseline_81 plus second fault ride=0 | Influence of inherited block riding |
| slow2_81 | baseline_81 plus second fault vel_x=5 km/Myr | Influence of late displacement rate |
| no2_81 | baseline_81 with second UNIT excluded | Separate event exclusion control |

**Essential:** do not compare 401 and 81 outputs to infer changes caused by ride or slip. The controls must all share 81 x 81 nodes.

## Files and interpreting outputs

- scripts/prepare_official_tectonics.py: generates each model input and original-file SHA256 audit.
- scripts/qc_official_tectonics.py: parses program completion, stage history, final Blocks shifts and numeric grid outputs.
- scripts/compare_official_tectonics.py: collects same-grid comparisons and saves summary CSV/JSON plus deflection plots.
- .github/workflows/03_official_tectonics.yml: automatically compiles pinned TISC and runs the case matrix.
- Raw artifacts contain original PRM/UNIT inputs, outputs such as demo.xyzt/demo.hrz/demo.xyw, RUN.log, STEP_DIAGNOSTICS.csv, FINAL_BLOCKS.csv and CASE_QC.json.

## Numerical limitations and rules

- Block motion occurs in discrete node increments; 81-grid step is 6.25 km, while 401-grid step is 1.25 km.
- The code uses an audited, compile-only normalization of two Unicode no-break spaces. No physics, density, Te, or tectonics equations are changed.
- The pinned C implementation contains a legacy first-use notification cleanup crash; the workflow suppresses the first-use path via HOME/.tiscdefaults.
- This example does NOT model geologically calibrated North Tianshan fault traces or Junggar depositional history.
- Interpret observed final block displacements and flexure, never assume imposed velocities guarantee a given topographic uplift.

## Archive

Running workflow: https://github.com/lcxstar/tisc-mechanism-lab/actions/workflows/03_official_tectonics.yml
Raw GitHub Actions artifacts have a 30-day retention setting. The permanent numerical summary and lessons will be checked in here after validation.
