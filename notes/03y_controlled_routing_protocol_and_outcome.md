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

## First REAL 03y results, N121, 0–3Myr — completed with baseline equivalence gate PASS

[Four-arm workflow execution 38183870409](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38183870409), N121 3Myr job id 114601948431, completed with GitHub Actions **success**, `F0` and `D0` 7 original physical files **byte-identical** to earlier 03v accepted original, all four runs reached 3 Myr and high-precision independent sediment mass-event ledger errors were **below 0.001%**.

| Difference pair | Terrain RMS (m) | Max local terrain abs (m) | Sediment thickness RMS (m) | Max local thickness abs (m) | Changed river downstream | Basin compacted sediment volume percent |
|---|---:|---:|---:|---:|---:|---:|
| Accepted float vs local double `F0-D0` | 0.02688 | 2.1 | 0.02688 | 2.1 | 4 | -0.000049% |
| Tie-margin float vs local double `F1-D1` | 0.00320 | 0.1 | 0.00351 | 0.1 | 0 | -0.000025% |
| **Physical change** baseline float `F0` vs tie-margin float `F1` | **7.446** | **304.0** | **5.857** | **116.4** | **678** | **-0.1544%** |

Notable: at 3 Myr a tiny tie-margin **1e-8 gradient (m/m)** reduces the two precision-variant differences in `F1-D1`, including 0 mismatched current downstream links, but **changes the underlying physical trajectory substantially**: float baseline `F0-F1` local elevation max **304m**, sediment thickness max **116.4m**, **678** changed directed river links, **259** changed drainage classes. The position of the maximum sediment thickness moves ~**200.22 km**, even though the **integrated volume changes by only −0.1544%** and centroid moves by ~0.30km. Locations of maxima may be inherently unstable or tied and must not be interpreted in isolation.

**Science decision:** This is a successful sensitivity experiment, **not** verified numerical stabilization. A lower discrepancy between two arbitrarily selected finite precision variants can coexist with dramatic changes in hillslopes/sediment placement. Do NOT adopt tie-margin as a production fix. Await N121 15Myr, N401 3/6Myr; additional micro-DEM tests are still required to demonstrate physically faithful tie handling.


## N121 15 Myr full-history acceptance — tie tolerance FAILS long-time stability as a general fix

[GitHub Actions job 114601948263](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38183870409) SUCCESS and original F0/D0 7/7 science output exact identity checks PASS. All four runs completed 15 Myr, corrected mass error <0.001%.

| Pair | Elevation RMS (m) | Sediment thickness RMS (m) | True flexure-w RMS (m) | Changed directed links | Compacted sediment total volume difference |
|---|---:|---:|---:|---:|---:|
| F0 vs D0 original precision | 48.055 | 27.190 | 2.481 | 7291 | 0.1976% |
| F1 vs D1 tolerance precision | 50.901 | 26.908 | 2.382 | 7171 | -0.1031% |
| F0 vs F1 physical tie change | 52.020 | 30.068 | 3.800 | 7460 | 0.1401% |
| D0 vs D1 physical tie change | 51.644 | 29.384 | 2.744 | 7361 | -0.1604% |

**Decisive time dependence:** under N121, the F1–D1 precision-pair elevation RMS decreases from F0–D0 **0.02688→0.00320m** at t3, but at t15 it **increases from 48.0548→50.9012m**. Thus the chosen tie margin is NOT shown to stabilize geologic results over 15 Myr. The physical float case F0→F1 alone changes terrain up to 648.7m and sediment thickness up to 635.9m even with only 0.1401% change in integrated sediment output volume. **Reject promoting the tiny-tolerance patch as a global numerical fix.** We may keep it solely as a sensitivity perturbation for identifying discontinuous choices. The actual outlet type/plateau equality conditions and local lake membership deserve isolated tests rather than blind epsilon tuning.


## Cross-project interpretation for actual Junggar source-to-sink studies (2026-10-12)

Full documented diagnostic in [Junggar V10.2-B domain-export-and-grid review](https://github.com/lcxstar/junggar-tisc-model/blob/diagnostics/v102b-routing-export-grid-audit-20261012/docs/V102B_DOMAIN_EXPORT_AND_GRID_RELIABILITY_AUDIT_20261012.md).

**Do NOT transpose the synthetic demo's t=2.5–3.0Myr internal elapsed-time hydrology bifurcation into Junggar geological ages 2.5–3.0Ma.** These refer to entirely different input models and timescales.

Junggar's recent 300–0Ma version uses **121×113 grid at 10km** in 1,200×1,120km overall rectangle, not the demo's 401×401 at 1.25km. Its experimental V10.2-B retained in-basin sediment thickness is mean ~39.57m / max 510.2m, with proxy basin preserved volume ~5,416.97km³. Independent diagnostics from the real accepted 300–0Ma V10.2-B artifact show 327,208 direct-border sediment-loss records summing **4.303904308257639e18kg**, despite transport boundary labelled 0000; export shares E54.3%, N23.7%, W14.0%, S8.0%. Large external domain export does **not** mean the majority of sediment eroded inside or destined to Junggar was lost, as the computational rectangle encompasses other catchments.

To assess if this hydrologic numerical effect explains genuine missing Junggar basin fill, trace **which upstream source zones connect to the Junggar basin mask**, distinguish border-lost non-Junggar catchments, and compare basin accommodation and palaeodivide stage constraints. **No** small gradient EPS change or generic 801-grid refinement should be marketed as automatically recovering Junggar sediment. Need true source-to-sink provenance bookkeeping and 10km vs 5km stage-controlled grid tests once geology is anchored.

## N401 3 Myr acceptance — tiny epsilon *worsens* sensitivity at the native author's grid

[03y run 38183870409, job 114601948476](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38183870409) **PASS**, input and original baseline outputs byte-identical, 4/4 completed original-domain 401² t3Myr forward trajectories; corrected sediment budget QC passed. Original unmodified F0 vs local double D0 had **terrain RMS 0.016721m**, **15** different directed river links and **5** type differences. With the registered epsilon=1e-8, F1 vs D1 has **terrain RMS 1.453640m** and **597** different directed links; sediment thickness RMS from **0.009277m** to **1.497640m**, max local thickness difference from **0.9m** to **244.0m**. The intervention itself changes F0 vs F1 maximum local terrain by **295.2m**, maximum local sediment thickness by **335.1m** while global compacted volume changes **-0.0463%**.

**Decision hard gate:** At native 401², a superficially tiny gradient tie change makes precision-pair disagreement substantially worse at the first t3Myr hydrology split. Combined with 121² long-run t15 result (terrain RMS 48.05→50.90m), this falsifies any claim that this particular epsilon universally stabilizes the drainage network. Only a *geographically local* lake outlet diagnosis with case-specific saddle elevations and drainage graph comparison should be pursued. Keep original 03t baseline as the accepted code; do not amend source for Junggar from the epsilon test.
