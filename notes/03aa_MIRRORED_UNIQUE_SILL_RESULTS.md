# 03aa — Mirror invariance with a uniquely lower controlling lake throat (2026-10-12)

**Scientific status:** independent original-physics 41×41 forward comparison. The first seven-case run [38212010449](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38212010449) passed every physical forward case and mass-budget QC. A follow-up re-execution checks and reports the precise locations of two reflected pointer mismatches. This test is not a Junggar palaeogeographic model.

## Prior evidence retained

- [03y controlled epsilon experiment](notes/03y_controlled_routing_protocol_and_outcome.md) rejected its globally applied 1e-8 downhill winner tie rule at long time/native mesh, despite an apparent N121 3-Myr short-time gain.
- [03z isolated lake saddle and Junggar science synthesis](03z_LOCAL_LAKE_OUTLET_SADDLE_TESTS.md) showed that lowering ONE genuinely controlling west lake entry throat by one 7.62939453125e-6m float32 ULP flips the deliberately exact-equality two-outlet 41×41 lake east→west, changing 229 downstream links; changing its outer notch does not.
- The question remaining for algorithm validation is distinct: if a lake has a RESOLVED unique low outlet, does the original lake algorithm select it and respect E/W mirror geometry without artificial slope epsilon?

## Pre-registered 03aa input and QC

- Original author commit d18b7d270f4d671b80223e10dede329ad35cafdd with the already independently benchmarked 03g/03j performance repairs, the separate 03k physically nonnegative incision-slope guard, corrected 03t sediment-event ledger, and output-only nine-digit native float topography print. Lake/river predicates are unchanged from accepted 03t.
- 41×41 points at dx=1 km across a 40×40-km deliberately synthetic radially confined lake, same PRM and zero fault UNIT files, 0–0.1 Myr with 0.05-Myr main steps.
- Exactly mirrored pairs at three unique inner-throat height differences (one float32 ULP, 0.1 m, 1.0 m): W_LOW_ULP1 vs E_LOW_ULP1; W_LOW_0p1m vs E_LOW_0p1m; W_LOW_1m vs E_LOW_1m. Plus identical exact-tie TIE baseline. All six nonbaseline cases modify exactly ONE initial inner throat cell, and every pair satisfies bitwise float32 E/W mirror equality.
- All 7 separate original TISC processes must complete and each full independent corrected mass-budget error must remain <0.001%.
- Compare actual largest lake outlet and membership from .lak, directed downstream edges and classes from .xyw, sediment thickness from .hrz, actual deflection w from .xyzt, plus integrated 41² sediment volume. Reflect one physical result across x=20km before comparing its counterpart. Report residual per-node pointer differences rather than assuming all are equal.

## First observed full-original-physics output (run 38212010449)

| Controlled inner-throat difference | Dominant outlet when WEST lowered | Dominant outlet when EAST lowered | Are reflected largest lake outlets and member sets identical? | Sediment thickness RMS after reflection | True flexural w RMS after reflection | Changed reflected downstream pointers |
|---|---|---|---|---:|---:|---:|
| 1 native float32 ULP (~0.000007629m) | (11,20)km WEST | (29,20)km EAST | YES / YES | 0m | 0m | 2 / 1681 |
| 0.1m | (11,20)km WEST | (29,20)km EAST | YES / YES | 0m | 0m | 2 / 1681 |
| 1.0m | (11,20)km WEST | (29,20)km EAST | YES / YES | 0m | 0m | 2 / 1681 |

All reported ZINI inputs reflect bitwise exactly; all seven original TISC physics runs reach 0.1 Myr with corrected mass balance errors under 0.001%. Mirror-paired integrated compacted deposited-sediment volume proxies respectively match at 0.0104, 0.0089 and 0.0090 km³; the 41² topography RMS discrepancies are only ~0.0000002–0.0000008 m as printed. There are 3 native lake objects per experiment.

The exactly tied symmetric baseline deterministically chooses EAST, but such a tie is intentionally underdetermined, and does not define a preferred geological eastward outlet. With a unique lower throat, the dominant lake outlet responds consistently and symmetrically at all three tested separations.

**Limit:** two *downstream pointer* entries after reflection differ although the dominant lake outlet location, lake member sets, sediment thickness and flexural response do not. Their exact cells and interpretation should be recorded separately, not concealed by a near-zero basin-integrated RMS. This may reflect benign non-discharging pointer conventions or ordering, but that mechanism is NOT yet established.

## Implication for Junggar and what this test does not prove

The 03aa result supports original TISC being geometrically responsive in this idealized controlled two-outlet lake, **not** a claim that its full real palaeotopography is correct, that it is globally numerically converged or that the 300-Myr Junggar fill deficit was cured. The very high Junggar V10.2B full-domain export/erosion proportion (~98.75%) and the low final basin-intersection fraction of outside nodes (28.82%, NOT sediment flux) remain separate [geological source-to-sink attribution tasks](https://github.com/lcxstar/junggar-tisc-model/blob/diagnostics/v102b-routing-export-grid-audit-20261012/docs/V102B_DOMAIN_EXPORT_AND_GRID_RELIABILITY_AUDIT_20261012.md).

The next Junggar mechanism priorities are to recover stage-specific source-zone drainage and provenance-weighted entry, test palaeosill/rim closure from independent stratigraphy, assess thermal/flexural accommodation on a separate axis and only then compare 10km vs 5km meshes. Do not promote 03y epsilon, alter the original hydrology source, or close all boundaries just to trap more material.
