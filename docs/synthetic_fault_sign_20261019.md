# Fully synthetic TISC opposite-slip benchmark (2026-10-19)

This is a numerical **mechanism screening** task, not a normal-fault implementation,
not a geological model, and not any Junggar Basin data.

Source: official `danigeos/tisc`, pinned commit
`d18b7d270f4d671b80223e10dede329ad35cafdd`.
Input is based on the author's `6_tectonics` PRM with controlled numerical changes.

- Grid: 61 x 11, over synthetic 300 km x 100 km, no geographic reference.
- Initial relief: flat 100 m.
- Identical west-dipping hypothetical plane to 4 km depth, wholly synthetic.
- Three independent cases: no UNIT; single fault at +5 km/Myr; same fault at -5 km/Myr.
- Runtime: 0 to 2 Myr; faults stop at 1.5 Myr.
- Hydrology and surface erosion/sedimentation disabled to isolate kinematics/flexure.
- Numerical pass requires native exit code zero, finite `demo.xyzt`, and correct time.
- Native `Blocks:` output is preserved: sign of requested velocity does not, by itself,
  establish hangingwall/footwall vertical slip.
- Plot: centerline differences in topography and downward flexure relative to no-fault case.

**Do not classify the negative-velocity case as a normal fault unless the source
algorithm, direction/geometry and displacement discontinuity validate true
extension and hangingwall subsidence, as distinct from moving/loading the block.**

GitHub Actions workflow:
`.github/workflows/synthetic_fault_sign_20261019.yml`.
Only compact logs/inputs/CSV/PNG/QC, retention 7 days; no field or private data.
