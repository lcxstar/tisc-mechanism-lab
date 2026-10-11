# 03v initial results — precise benchmark reproduction and emergence of numerical bifurcation

**Source:** author's TISC official `6_tectonics` at fixed upstream commit `d18b7d270f4d671b80223e10dede329ad35cafdd`. Both paired variants use all same geological/tectonic inputs per experiment, coupled plate flexure on, 03g/03j runtime accelerations, 03k labeled slope-domain guard, 03t 64-bit transaction bookkeeping. 03u1 changes **only** the local `Sediment() dh_sed` temporary from float to double, NOT persistent Block thickness, terrain, river storage or flexure arrays. Never call this a fully double TISC implementation.

## Status of reproduction

**PASS, functional/mechanistic reproducibility:** original author N401 0–15 Myr benchmark is executable to completion with prescribed uplift/flexure/river/lake transport and source/sink sediment budget properly audited. This uses a **modified derivative** of author code. It is *not* a claim of strict unmodified-source bitwise reproduction or validated agreement with an independently available author cell-by-cell benchmark.

[Original 401×401 15Myr scientific baseline](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38165304319) had 30 normal main time steps with corrected sediment budget max error 0.00016753%, while unchanged original author `demo.PRM` and `demo*.UNIT` are audited. Prior ~34% native sediment bookkeeping loss is accounted for by float32 global accumulation and was not a 34% physical mass loss.

## First observable numerical divergence and lake/river threshold (N121, original time steps)

[Paired-stage workflow](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178515988); [2.5 Myr discriminating follow-up](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178607601). Both original author time controls `dt=.5 Myr, dt_eros=.05 Myr`, except Nx,Ny=121; source loads and all other geology unchanged.

| Elapsed Myr | Max abs terrain difference (m) | Terrain RMS difference (m) | Changed downstream edges | Lake counts float/double |
|---:|---:|---:|---:|---:|
| 0.5 | 0 | 0 | 0 | 1 / 1 |
| 1.0 | 0 | 0 | 0 | 40 / 40 |
| 1.5 | 0 | 0 | 0 | 16 / 16 |
| 2.0 | 0 | 0 | 0 | 10 / 10 |
| **2.5** | **0.1** | **0.00165** | **0** | **29 / 29** |
| **3.0** | **2.1** | **0.02688** | **4** | **27 / 26** |
| 4.0 | 2.7 | 0.03794 | 2 | 30 / 30 |
| 6.0 | 325.6 | 11.126 | 2,976 | 69 / 65 |
| 10.0 | 674.2 | 31.683 | 5,421 | 79 / 86 |
| 12.0 | 802.4 | 46.653 | 6,413 | 93 / 78 |
| 15.0 | 586.7 | 48.055 | 7,291 | 20 / 10 |

**Exact limits:** the first *printed* terrain difference occurs between last identical tested t=2.0 and t=2.5. The first observed drainage and lake-membership graph difference occurs between t=2.5 and t=3.0; this does not prove the first microscopic floating-point difference started in those windows because author outputs retain only 0.1m precision. Stage t3 lake member union symmetric difference is 3 nodes, outlet coordinate symmetric difference 2, lake components 27 vs 26; this is an actual topology difference, not merely text changes in `demo.lak`. At t6 lake union difference reaches 1265 nodes with 2976 changed downstream edges.

At t3 first reported changed lake/drainage category nodes are near the model southeast boundary at synthetic (350,−241.67), (345.83,−245.83), and (345.83,−250) km, showing the potential involvement of shoreline/outlet boundary thresholds; other changed drainage links also occur near the western edge. Do not attribute causality exclusively to boundary erosion without a controlled mechanism test.

The first differences are not monotonic in every metric at each horizon (e.g., 3-to-4 Myr changed edges 4→2), consistent with discontinuous lake routing and interaction. Correlation is not mechanistic proof; to test causality, inspect first changed outlet and its high-resolution local water level/slope, or hold routing fixed in a separate model branch.

[Permanent stage control CSV](../results/03_tectonics/03V_121_DIVERGENCE_STAGES.csv).

## Time-step convergence — initial 81 and 121 full 15Myr

[Paired 81/121/201/401 factorial run 38178558812](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178558812) is separately testing grid and time step. First two resolutions' independent completed jobs:

| grid | dt (Myr) | dt_eros (Myr) | float vs local-double terrain RMS (m) | changed downstream edges |
|---:|---:|---:|---:|---:|
| 81 | .5 | .05 | 43.737 | 3,045 |
| 81 | .5 | .025 | 21.526 | 2,053 |
| 81 | .25 | .025 | **19.386** | **1,955** |
| 121 | .5 | .05 | 48.055 | 7,291 |
| 121 | .5 | .025 | 26.459 | 5,524 |
| 121 | .25 | .025 | **24.943** | **5,566** |

**Interpretation:** halving `dt_eros` reduces precision-variant elevation differences; further halving `dt` also reduces RMS height differences in both grids, but N121 changed edges **increase** slightly from 5524 to 5566 in that last step, so not every hydrologic measure improves monotonically. It is too early to claim numerical convergence. Also, integrated sediment volume for the float baseline changes materially when time steps are refined; convergence of *absolute physical predictions* remains separate from convergence of two precision variants.

[Permanent factorial early results CSV](../results/03_tectonics/03V_TIME_SPACE_CONVERGENCE_EARLY.csv).

## New N401 2Myr precision evidence

Earlier [N401 0–2 Myr full model pair 38167459994](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38167459994) completed with only 3 of 160801 printed elevation cells changed (max 0.1m), **zero** drainage type changes, **zero** downstream link changes, and **29 lakes** in each run. Different raw `demo.lak` files did **not** demonstrate changing membership/outlet topology at this stage. New N401 0.5–6 Myr matched-time outputs are being tested and must be checked before declaring 401 stability.

## Convergence testing in progress

- [03v staged 121/401 first-divergence workflow](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178515988).
- [03v 2.5 Myr threshold probe 121/401](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178607601).
- [03v grid/time factorial N81/N121/N201/N401](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38178558812).
- [03v 401 full 15 Myr paired endpoint](https://github.com/lcxstar/tisc-mechanism-lab/actions) (new workflow `03v_401_full15_precision.yml`). Do not call an in-progress run complete.

**Scientific decision:** (1) main official reference process chain functional reproduction passed with documented source corrections; (2) the nontrivial long-time divergence across arithmetic precision is real, not mass ledger error; (3) a lake/river-network bifurcation appears by t3 in N121, with large divergence by t6; (4) some convergence under smaller dt is observed for variant difference, but spatial and fully physical convergence not yet established. No geological parameter fitting to Junggar until these are characterized.

## 03w read-only bitwise state chronology — decisive new result

[03w per-hydrological-substep tracer](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38179009871) instruments the same raw native float-state FNV hashes into BOTH source variants and retains `ctx->topo`, last Block thickness, cumulative flexure `w` and drainage node type/lake/downstream edge independently. **No input, output, or physical arithmetic change** is introduced by this hash. N121 paired trial ran all **60 erosion substeps through 3 Myr**, exit0 and mass gates PASS.

| Internal state being compared, first mismatch | Elapsed simulated time |
|---|---:|
| Raw stored float topography `ctx->topo` | **0.55 Myr** (substep zero of main interval 0.5–1.0) |
| Last Block thickness raw float storage | **0.55 Myr** |
| Plate deflection grid `w` raw float storage | **2.05 Myr** |
| Drainage type, lake ID or downstream destination raw state hash | **2.55 Myr** |
| First rounded 0.1m terrain difference in exported N121 stage maps | 2.5 Myr |
| First *stage output* observable river and lake topology difference | 3.0 Myr |

**Interpretation:** the earliest detectably changed native numerical state is sediment/terrain by about 0.55 Myr, i.e. **much earlier** than the first visually noticeable 0.1m difference. Downstream flexural and hydrological trajectories diverge later, consistent with nonlinearly amplified feedbacks. The `hydro_crc` hash signals any difference among raw drainage type, lake IDs and downstream edges; the 03v `xyw`/`lak` member-set analyses are needed to distinguish a mere internal lake-index change from actual graph topology. This is not proof of a mathematical instability theorem or of which trajectory is physically correct. Timing is quantized by 0.05 Myr erosion substeps, and the model may diverge within a substep before the snapshot.

N401 has independently shown the first **rounded printed** height difference at 1.5 Myr (one 0.1m changed cell), no changed drainage type/edge or lake member components through at least the first 1.5 Myr. N401 internal-state checksum trial has been launched but requires its own completed log before stating its exact first mismatch.
