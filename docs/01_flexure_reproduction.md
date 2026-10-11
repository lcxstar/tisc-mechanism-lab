# Experiment 01 — Reproduce the official TISC flexure demonstration

## Scientific objective

First demonstrate numerical repeatability of a **known upstream author's benchmark**, before interpreting Junggar tectonic forcing or sedimentation.

### The author's documented standalone load benchmark

Upstream: `tisc/demo/README` and `tisc/demo/2nd_example_load.xyp`.

Exact author's input, interpolation mode 4, fixed rectangular domain from -250 to +250 km in both dimensions:

```bash
tisc -Q2nd_example_load.xyp -N11 -D-2.5e5/2.5e5/-2.5e5/2.5e5 -qmode_interp=4
tisc -Q2nd_example_load.xyp -N51 -D-2.5e5/2.5e5/-2.5e5/2.5e5 -qmode_interp=4
```

The author reports the following center-node values (positive magnitude, downward deflection):

| Grid | Author's reported center deflection |
|---|---:|
| 11×11 | 675.1 m |
| 51×51 | 711.0 m |
| 101×101 | 712.2 m (later resolution check) |

The first run accepts ±10 m for software-version and output precision differences, and *will not silently coerce* missing/out-of-range values to PASS. When the original benchmark is independently reproduced, subsequent experiments can tighten the tolerance.

The **11 versus 51** comparison isolates only grid resolution. `-Q` performs one static load/elastic-deflection calculation, not a 300 Ma time-evolution experiment.

### The author's full project example

Copy the source directory `tisc/demo/3_flexure` into a temporary GitHub runner working folder without changing any file contents. Run:

```bash
tisc flex -V2
```

Record source file hashes and TISC output arrays. This `flex.PRM` declares its own grid, default `Te`, time interval, no hydrology, and three numbered UNIT loads; importantly, this is **not** the same input as the single `-Q` load.

A successful run demonstrates input parsing, time scheduling and outputs, but does **not** constitute a geological calibration. A numerical QC report and images are saved only when source arrays parse correctly.

### Source isolation

- Pinned upstream TISC: `d18b7d270f4d671b80223e10dede329ad35cafdd`.
- No algorithmic source patches. The pinned upstream `surf_proc.c` has exactly two U+00A0 spaces in boolean operators, which GCC refuses to compile. Workflow normalizes only these characters to ordinary spaces in its temporary checkout and saves `UPSTREAM_WHITESPACE_FIX.json` containing the original and resulting file hashes. No legacy Junggar `surf_proc.c` modifications or boundary schedules.
- Native compile via `make -C upstream/tisc/src tisc`.
- Official inputs are not edited; screenshots and comparative interpretations are our own.

### Next after a validated baseline

Run Te=5, 20 and 40 km for **one identical prescribed load** with a known-fixed grid and produce the three deflection profiles. Only then progress to the author's `6_tectonics` example to investigate `ride=1`, discrete block motion and structural loading.

### Discovered upstream first-run cleanup fault (October 11, 2026)

First full demo run completed all numerical times and produced `flex.xyzt` and `flex.hrz`, but returned exit code 139 **after** `Time end`. Inspection of pinned `tisc/src/tisc.c` showed the cause. When `$HOME/.tiscdefaults` does not exist, the code creates it and tries to send an old first-use notification via `mail`, then calls `fclose(file)` on the `NULL` pointer from the unsuccessful `fopen`. This is a cleanup error, not failure of the flexure calculation.

To avoid both the segfault and unintended attempt to contact the upstream author, the workflow pre-creates `$HOME/.tiscdefaults` in the ephemeral runner. No physics source line is changed. Importantly, the code still contains the original bug, which should be reported upstream rather than silently edited for a teaching baseline.

The direct `-Q` outputs contain **four**, not three, numeric columns (x, y, displacement and pressure), so the numerical QC was corrected to recognize the author's actual format. The first successful observed center displacements, extracted from the failed-full-demo run's saved logs, were **675.1 m and 711.0 m**, exactly matching the author's reference.
