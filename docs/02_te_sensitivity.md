# Experiment 02: Reproduce author's flexure, then vary Te only

**Goal.** Understand what effective elastic thickness controls in TISC before applying it to North Tianshan.

## Step 1: Reproduce the author's exact static deflection benchmarks

Official author demo: https://github.com/danigeos/tisc/tree/main/tisc/demo

Pinned source: d18b7d270f4d671b80223e10dede329ad35cafdd

Input file: tisc/demo/2nd_example_load.xyp. Direct solver mode = -Q.
The author documents 675.1 m of downward deflection at the central node with an 11x11 grid and 711.0 m with a 51x51 grid.

In both cases use the original load and identical domain from -250 to +250 km.
Reproduce reference values **without any -T override** first, to establish that this software revision and command are working.

## Step 2: One-factor Te sweep

Retain the exact same official load, coordinates, source version, elastic solver and boundary configuration. In each fixed-resolution set vary only -T, which accepts **metres**.

| Te setting | Command argument | Grids | Status |
|---|---|---|---|
| 5 km | -T5000 | 51x51 and 101x101 | Diagnostic trial |
| 20 km | -T20000 | 51x51 and 101x101 | Diagnostic trial |
| 40 km | -T40000 | 51x51 and 101x101 | Diagnostic trial |

For every trial run the command in this pattern:

    tisc -Q2nd_example_load.xyp -N51 -D-2.5e5/2.5e5/-2.5e5/2.5e5 -qmode_interp=4 -T20000

The 101x101 repeats are numerical resolution checks. **Do not compare 51 versus 101 as a Te experiment**; the valid Te comparisons always use the same resolution.

## What is checked and preserved?

Every TISC output has x (km), y (km), w (m), pressure (Pa).
The numerical QC checks that the pressure grid is exactly unchanged when Te changes, coordinates and grid counts are correct, no values are non-finite, and the known author reference is reproduced.

Saved material in the GitHub Actions artifact:

- Raw standard-output logs for both official references and all six Te trials.
- TE_SWEEP_QC.json, with explicit author-reference error, pressure identity and numerical results.
- TE_SWEEP_NUMERICS.csv, plus TE_SWEEP_PROFILE_X_51.csv for reproducibility.
- FIG01_Te_profiles.png/.svg and FIG02_Te_maps.png.

**Interpretation:** The test isolates elastic plate stiffness. A thinner Te is expected to allow a more localized, higher peak deflection beneath the same load. This is a physical hypothesis, not a numerical result until verified. It cannot tell us North Tianshan shortening rate or Junggar sediment thickness.

## Exact source integrity

The workflow checks out the pinned original upstream commit. As in Experiment 01, it normalizes exactly two illegal Unicode U+00A0 whitespace characters in upstream surf_proc.c solely to enable compilation with current GCC. It does not modify formulas, load files, time stepping, or physical parameters. The temporary HOME/.tiscdefaults suppresses the original first-run notification bug without touching source physics.
