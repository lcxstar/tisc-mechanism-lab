# Synthetic TISC fault sign test: verified native result (2026-10-19)

**Passing GitHub Actions run:** https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/39205727463

**Experiment branch:** experiment/synthetic-fault-sign-test-20261019

- The published TISC source is locked to danigeos/tisc commit d18b7d270f4d671b80223e10dede329ad35cafdd.
- Every spatial input is **synthetic**, with no present or palaeo-Junggar coordinates, field data, material distribution, or mapped fault.
- Grid 61 x 11, 5 km dx and 10 km dy; flat initial surface +100 m; 2 Myr model duration.
- One geometrically identical, assumed dipping fault was tested with ±5 km/Myr and stop at 1.5 Myr; both native final shifts were ±5 km.
- Surface processing, hydrology and water loading were disabled, so **sediment accommodation, growth strata, and basin sedimentation have not been tested**.
- True surface elevation is read from the **last column of the native demo.pfl section**, at Y=-50 km. Elastic vertical deflection is read separately from native demo.xyzt column 3, on the same line.
- All cases exit 0, reach 2.0 Myr and produce finite records; no surface mass-conservation inference is made.

## Quantitative result

| Case | Actual block X shift | Surface min/max (m) | Elastic w min/max (m, positive down) | Min surface minus control (m) |
|---|---:|---:|---:|---:|
| Control | 0 km | 100 / 100 | 0 / 0 | 0 |
| Positive | +5 km | -32.9 / +614.0 | +15.8 / +145.1 | -132.9 |
| Negative | -5 km | -416.7 / +234.3 | -145.7 / -11.5 | -516.7 |

The negative case's deepest local low occurs at X=-39.8 km and maximum
high at X=-45.4 km: a ~651 m step over only ~5.6 km. The positive
case shows similarly concentrated relief near X=-40 to -35 km.
These are **mesh-sensitive fault-kinematic steps**, not validated
regional half-graben profiles.

**Physical conclusion: Not passed.** Merely reversing the horizontal
velocity can create a sharp local surface depression, but the negative
case shows upward rather than downward plate deflection. It is not a
demonstration of crustal thinning, hangingwall normal slip, tectonic
subsidence, or a spatially realistic early Permian rift.

**Next method gate before real basin modeling:** Build a two-block
cross-section that separately tracks the fault surface and vertical
hangingwall/footwall displacements; validate a normal-fault kinematic
solution before applying it to a 2-D planform. If TISC lacks physical
crustal-thinning/normal-sense kinematics, use independently prescribed
tectonic subsidence in a clearly named scenario instead of relabeling
negative thrust-style slip as extension.

Native inputs/outputs and figure are downloadable from the passing
workflow's artifact (7-day retention). Key tabular results are
permanently committed beside this note.
