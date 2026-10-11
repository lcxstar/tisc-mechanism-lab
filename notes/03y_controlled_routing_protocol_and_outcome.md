# 03y — Controlled route-gradient tie sensitivity, before any 801-grid run

**Status at creation: launched, NOT scientifically accepted.** Execution tracking [four-arm GitHub Action](https://github.com/lcxstar/tisc-mechanism-lab/actions/workflows/03y_local_routing_tie_factorial.yml). This branch is **experimental** and does NOT replace the accepted 03t and 03x reference.

## Previous robust findings

- Official synthetic 401×401 `6_tectonics` original geometry and kinetics on pinned author revision `danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd` successfully ran to 15Myr using documented 03g/03j computational optimizations, 03k separate negative-slope physical guard and 03t corrected double sediment event ledger.
- [03x exact native float output 401 3Myr CI](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38183004799) **PASS**. With only local `Sediment() dh_sed` promoted float to double, there are **18** unique changed outlet/river link nodes (15 changed directed downstream edges and 5 changed types). **Only 4/18 have identical exactly recoverable stored local float32 elevation**, vs **15/18** with matching *rounded 0.1m output* from older tests. The distinction is important: 4/18 is NOT proof that lake logic is incorrect; equal focal-node height can still produce different route choice because neighbouring heights, lake membership and priorities have changed.
- Reproduction check `03x` confirms output-format-only nine-digit float elevation print leaves **all six other scientific products byte-for-byte identical** to accepted `03v` runs. [03x read-only source and interpretation](../notes/03x_publications_mesh_convergence_and_outlet_mechanism.md).
- [03x read-only 81/121/201/401 original float+same time-step 15Myr](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38183080587) PASS. Approx compacted sediment volume 86,616/69,106/61,107/59,834 km³ respectively. 201 vs 401 has **48.74m** sediment-thickness RMS, **50.12m** true plate-deflection-w RMS, **122.63m** surface topography RMS despite basin volume being only **2.13%** different. These are comparisons to 401, not proof 401 is converged.
- Original `surf_proc.c Define_Drainage_Net` selects among eight neighbours, with strict `deriv<0`, downhill maximum comparison and separately strict `deriv==0`, same-elevation outlet/lake topology conditions. This code fact motivates a controlled *tie-breaking sensitivity* check, not automatic bug declaration.

## A preregistered *single physical intervention* (first pilot)

We modify ONLY **two** comparisons that *replace an already-selected downhill neighbour* in `Define_Drainage_Net`: when a downhill candidate is found, the first downhill route is still always selected, while later candidates must beat the current steepest slope by **more than `epsilon = 1e-8 m/m`** to replace it. At original N401 dx=1.25km this is a **0.0000125m = 0.0125mm** elevation difference over one horizontal cell. This does not set a universal minimum slope; the first negative candidate remains valid even when very shallow. It is a **numerical tie-selection experiment**, not a known physically or mathematically validated stabilization.

- NO changes to lake identification `deriv==0`, `topo==topo`, saddle defining or lake filling; no modifications to tectonic loads, plate modulus, `Te`, precipitation, erosion coefficients, sediment porosity, stratigraphy or original initial state.
- Four independently built executables per grid/horizon using identical author physical input and source except the explicitly preregistered numerical perturbations.
  - `F0` accepted 03t local float sediment increment, original exact steepest descent.
  - `D0` same except local `Sediment() dh_sed` double (03u1), original exact steepest descent.
  - `F1` same as F0 except `1e-8` descent replacement tie margin.
  - `D1` same as D0 plus that tie margin.
- Experimental matrix: N121 3Myr and full 15Myr for rapid bifurcation/external mass validation, N401 3Myr and 6Myr for direct native mesh first-lake & hydrology change check; extend N401 to 15Myr **only after** early-stage QC and enough computing budget to justify full run. Zero-epsilon source remains accepted baseline.
- An absolute requirement is *byte-for-byte equality* for `F0` and `D0` vs the accepted 03v reference for all 7 original geophysical outputs, and every run must complete with corrected mass-event balance <0.001%. If baseline mismatch, do NOT interpret eps-trial geological changes.
- Compare **same-scheme F0-vs-F1 and D0-vs-D1**, and controlled precision **F0-vs-D0 and F1-vs-D1**; do not confuse reduction of model difference between precision variants with proof of physical convergence.
- Outputs to compare: true `w` from `demo.xyzt`, sediment thickness from layer boundaries in `demo.hrz` (compaction-adjusted), absolute maxima, RMS spatial difference, 500×500km integrated sediment volume via trapezoidal area weights, sediment volumetric centroid and max-thickness position, downstream edges, different lake types, sediment mass QC. Named lake component memberships need independent checking, not inferred from lake count alone.
- Interpretation gates:
  1. No change in geology for F0/D0, exact author inputs;
  2. Short-stage sensitivity of 121/401 river/lake outlet selection verified;
  3. Is the perturbation *materially* changing finite volume, thickness and deflection? Quantify; compare physical fields.
  4. Is F1-D1 convergence consistently *better* across elapsed times and meshes? Improvement at one horizon is not enough; if nonmonotonic, reject as blanket fix.
  5. Preserve rejected branches, commit actual results; do not silently promote patched code to production and do not use it for Junggar calibration.
 
### Further required mechanism experiments

If the tie-margin experiment does not stabilize the pathways, the next hypothesis is **lake saddle and exact plateau identification** (strict equality and order effects in `Define_Drainage_Net`). This requires independent isolated lake-outlet cases on a small deliberately constructed DEM and a second, separate source branch. Do not combine a large change to lake-fill, exact lake equalities and routing in the first trial. Follow with same-scheme 201/401 long-horizon basin-scale thickness/deflection checks prior to deciding on 801.
