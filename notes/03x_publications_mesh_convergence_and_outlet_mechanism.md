# 03x — Original TISC scientific literature and our first same-scheme grid / first-outlet audit

**2026-10-12.**  This is a reproducible literature-and-numerics milestone for the official synthetic TISC `6_tectonics` example. Its author calls the method 3-D planform in early papers, but current source README calls the implementation a pseudo-3D model using a two-horizontal-dimensional finite-difference grid with multiple tracked stratigraphic Blocks; not a 3-D volumetric full-stress finite element solution.

## Papers that justify TISC and benchmark numerical choice

1. **García-Castellanos, D. (2002)**, *Interplay between lithospheric flexure and river transport in foreland basins*, *Basin Research* **14**, 89–104. [DOI](https://doi.org/10.1046/j.1365-2117.2002.00174.x). Foundational coupling of thrust kinematics, flexural subsidence and explicitly routed river/lake erosion/transport. This paper is the first methodological starting point, not evidence of pointwise numerical convergence in the current 2026 revision.
2. **García-Castellanos, D., Vergés, J., Gaspar-Escribano, J., Cloetingh, S. (2003)**, *Interplay between tectonics, climate, and fluvial transport during the Cenozoic evolution of the Ebro Basin (NE Iberia)*, *JGR: Solid Earth* **108(B7)**, 2347. [DOI and openly available full text](https://doi.org/10.1029/2002JB002073). **IMPORTANT actual validation precedent:** paper Table 1 explicitly lists **104×55 grid**, Table 2 **60–0 Ma** and **0.05 Myr time step**. Section 4 paragraph **[57]** explicitly says *double-resolution runs* produced broadly similar regional drainage evolution, while the timing of drainage closure/opening could shift by **a few Myr**; spatially integrated basin infill and postopening incision rates changed by **less than 10%**, so authors retained lower spatial resolution because finer modeling was computationally costly. The text also describes discrete thrust movement as requiring a minimum shift of one cell, creating numerical spacing effects. Section [41] cautions that capture transition timing is resolution sensitive, and [64] says their resolution cannot further constrain sub-Myr lags. Crucially, <10% is **a specific result of that case**, not an universal code reliability guarantee.
3. **García-Castellanos, D., Fernàndez, M., Torné, M. (2002)**, *Modeling the evolution of the Guadalquivir foreland basin (southern Spain)*, *Tectonics* **21(3)**. [DOI](https://doi.org/10.1029/2001TC001339). Documents flexural plate rheology, tectonic loads, sediment transport and basin-scale constraints, with planform + cross-section analysis. Mechanism and geological validation reference, not identical to 2026 bundled `6_tectonics`.
4. **García-Castellanos, D. & Jiménez-Munt, I. (2015)**, *Topographic Evolution and Climate Aridification during Continental Collision: Insights from Computer Simulations*, *PLOS ONE* **10(8)** e0132252. [DOI](https://doi.org/10.1371/journal.pone.0132252). Uses spatial thin-sheet tectonics and river/lake hydrology feedback; that implementation additionally incorporates 1D thermal columns, which should NOT be ascribed automatically to current `6_tectonics` example.
5. **García-Castellanos, D. & Cloetingh, S. (2011)**, *Modeling the Interaction between Lithospheric and Surface Processes in Foreland Basins*, *Tectonics of Sedimentary Basins* chapter 8. [DOI](https://doi.org/10.1002/9781444347166.ch8). Conceptual review of coupling between foreland lithosphere, surface mass transfer, sediment stratigraphy and drainage systems.
6. **Official author's TISC page**, [software and related scientific publications](https://sites.google.com/site/daniggcc/software/tisc), explicitly describes rectangular horizontal finite-difference mesh, following topographic maximum-gradient river network, explicit lake outlets and sediment horizons.

## First new *same numerical scheme* synthetic grid comparison, achieved before 801

All simulations used the accepted 03t-derived 32-bit physical solver (not the 03u1 candidate), `dt=.5 Myr`, `dt_eros=.05 Myr`, original kinematic blocks and synthetic 500km×500km footprint, completed t=15Myr. Science arrays re-read from archived `demo.hrz` and `demo.xyw`; compaction-adjusted sediment thickness reconstructed only from sedimentary units tagged at 2200kg/m³. Integrals use trapezoidal quadrature across **exact 500km square**. RMS fields are interpolated to the **coarse node coordinates** from the 401 grid using 2-D bilinear interpolation; the 401 result is only a **comparison reference**, not the exact solution.

| Nx×Ny | Grid km | Integrated compacted sediment approximate km³ | Relative volume vs 401 | Sediment thickness RMS difference vs bilinear 401 map | Surface elevation RMS difference vs 401 | Deepest .hrz basal-surface elevation RMS vs 401 |
|---|---:|---:|---:|---:|---:|---:|
| 81 | 6.250 | 86,615.86 | +44.76% | 174.58 m | 140.50 m | 131.00 m |
| 121 | 4.167 | 69,105.56 | +15.50% | 91.00 m | 133.80 m | 59.13 m |
| 201 | 2.500 | 61,107.43 | +2.13% | 48.74 m | 122.63 m | 51.12 m |
| 401 | 1.250 | 59,833.94 | reference | reference | reference | reference |

The **deepest .hrz layer is the basal interface elevation** and does not isolate deflection `w`. For an exact plate-flexure convergence test, additionally compare `w(x,y,t)` against consistent initial basements from exported solver state. Thickness reconstruction here yields **compacted output volume**, not time-integrated sediment mass from the high-precision process ledger.

**Finding:** aggregated sediment volume shows an apparent approach to the 401 value as grid is refined, but 201 vs 401 still has 48.74m RMS sediment thickness discrepancy and 122.63m RMS final topography discrepancy. No assertion of numerical convergence with only four grid settings, or that 401 is correct. Test 801 ONLY if further physical and outlet checks warrant and hardware permits.


## Explicit deflection convergence check (instead of using deepest .hrz elevation)

The independent `demo.xyzt` scientific export contains the plate deflection `w` as its third column. This was directly re-extracted from the paired accepted artifacts; same-scheme deflection RMS relative to bilinearly interpolated 401 benchmark:

| original benchmark Nx | RMS of true plate deflection `w` vs 401 |
|---:|---:|
| 81 | **119.74 m** |
| 121 | **54.89 m** |
| 201 | **50.12 m** |
| 401 | comparison reference |

The deepest `demo.hrz` surface is **not itself w**. Across 201→401, true flexure still differs spatially by ~50m RMS at 15 Myr. New reproducible `03x` CI now reads `demo.xyzt` separately and records both basal-horizon and true-flexure errors; output values should be verified from the completed current CI job.

## First changed river/lake routing node diagnostics

- Comparison of 401 exact same-dt 03u1 local-double vs 03t original (only temporary `Sediment() dh_sed` precision changed). Stage **t=2.5Myr** has **zero** changed raw `demo.xyw` downstream links or node types.
- At **t=3 Myr**, the full original 401×401 domain has **15 changed downstream links**, **5 changed node classes**, at **18 unique grid nodes**. In **15/18** changed nodes, the output height *as printed to 0.1m* is identical between two simulations. Many changed nodes lie on flats/outlet/synthetic boundary corridors.
- At 3Myr, differences cluster around **x≈37.5–38.75km, y≈−245 to −247.5km**, **x≈−148km, y≈−246km**, and other sills; these coordinates are synthetic benchmark (not Junggar geography).
- Author `surf_proc.c` `Define_Drainage_Net()` makes branch decisions on **exact float zero/equality**, e.g. `deriv==0`, `ctx->topo[i][j]==ctx->topo[other]`; negative-steepest slope `deriv<maxderneg`, lake-component sorting and outlet categorization. This provides a **plausible mechanism** for amplifying sub-output-resolution topographic differences, not yet a proof of unique causal origin.
- **Necessary next gate:** an **output-only** `tiscio.c` patch prints float32 elevations using `%.9g` instead of `%.1f`, while preserving all six other scientific output files byte-identical to the original runs. This probes near-zero/tied slopes using exactly recoverable stored float values. Run separately on N121 and N401 t3; DO NOT change lake-routing physical comparisons or declare source fixed based on this observer alone.
- Only after verifying the near-flat branch site with native float precision should controlled deterministic tie-breaking or threshold stabilization be tested in a separate branch, with explicit before/after basin-scale geography and mass accounting; otherwise changing lake code could hide or create a different problem.

## Source files and reproducible actions

- `scripts/analyze_03x_archived_grid_and_routing.py` replays fixed artifacts.
- [GitHub Actions read-only 03x mesh/outlet audit](../.github/workflows/03x_grid_route_reanalysis.yml).
- `scripts/patch_03x_raw_float_xyw.py` output-format-only source alteration.
- [GitHub Actions exact native float outlet probe](../.github/workflows/03x_highprecision_rawfloat_outlets.yml).
- The old benchmark artifacts are public Actions runs [38178558812](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178558812), [38178743124](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178743124), [38178515988](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178515988), [38178607601](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178607601).

**Decision:** Do not launch 801 yet. Finer 201 vs 401 sediment volume becomes closer but not spatially stable, while near-flat routing branches may substantially affect later sediment depocentres. In addition to numerical verification, future Junggar runs must be calibrated against independent tectonic shortening, basin subsidence, stratigraphic depocentre and thermochronologic constraints.
