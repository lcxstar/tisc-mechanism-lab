# Performance diagnosis — 401×401 original tectonic demo

**Outcome (11 October 2026): the first-step high-resolution slowdown is primarily in the surface-process path.** The full original 401×401 0–15 Myr project is NOT reproduced, but the high-cost component has been isolated with controlled command-line overrides.

## Verified logs

- Original 401×401 (fully coupled with author's byte-exact input): [Actions 38140725340](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38140725340). Three original attempts separately ended after 1800 seconds with exit **124**. Last printed model time **0.0000 Myr**.
- Independent cost isolation: [Actions 38144468865](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38144468865).
- 401×401, **flexure disabled only** with `-qisost_model=0`, but hydrology and erosion enabled: still exited **124**, wall time **240.00 s**, time remained 0.0000 Myr. [Raw log](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38144468865/artifacts/11703679474).
- 401×401, **both hydrology and erosion disabled**: exit **0**, 0.21 s to 0.5 Myr. Elastic solver remained configured but no significant fault-motion load was realized in this short time window, so this is NOT a full elastic-solver benchmark. [Raw log](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38144468865/artifacts/11704127854).
- 401×401, **flexure AND surface disabled**: exit **0**, 0.21 s to 0.5 Myr. [Raw log](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38144468865/artifacts/11704365689).
- 121×121, model physics retained, plotting only disabled: exit **0**, full 0–15 Myr reached in **39.13 s**, 31 logged times and finite endpoint arrays. [Raw log](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38144468865/artifacts/11704236536).

## What follows, and what does not

**Strongly supported:** the first 401 time step becomes prohibitively slow when surface processes are active; turning off the elastic solver alone does not resolve the bottleneck.

**Not yet established:** which specific surface subroutine (lake routing, drainage calculation, erosion, sediment transport, sorting) dominates; nor the speed of the 401-grid elastic solver once the first actual tectonic load has been applied. The author's 401-grid initial topography is uniformly 100 m, which raises a plausible concern about expensive flat drainage/lake calculations, but this causal hypothesis has not been independently verified.

**Independent scientific warning:** the 121×121 run writes `outp_seds: -nan N` in the late-stage mass-balance log. Its **numerical completion was successful**, but a **finite, closed sediment-mass budget has NOT been demonstrated**. Do not use that run as a calibrated depositional history without a mass-budget audit.

## Source reproducibility and next validation

The 401-grid short tests copied `demo.PRM`, both UNIT files, and PRFL **byte for byte** from pinned official TISC `d18b7d270f4d671b80223e10dede329ad35cafdd`. Physics modifications were explicitly declared in the `-q` **runtime arguments**, not silently inserted in the physical parameter files. The `121×121` case only changed two grid dimensions in the author PRM; a nonphysical plotting override was used.

Four 81×81 first-order kinematic controls from [run 38140725340](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38140725340) remain **successful** and permanently documented in [03 results](03_official_tectonics_results.md).

For scientific analysis, prioritize separate 401-grid **hydrology-only and erosion-only short-step toggles** and detailed timing around the lake/drainage subroutines before attempting another literal 401×401 15-Myr coupled run. The automated 30-minute 401 trial has been removed from the routine experiment-03 matrix. Do not solve performance by changing Te, faults, or inventing accommodation; and do not treat an uncalibrated finite grid as proof that erosion physics is correct.

## Known automated-QC issue fixed

GNU `/usr/bin/time` writes a descriptive line before `240.00` on nonzero exits. The diagnostic QC originally attempted to parse the entire text as a float and failed during the 401 flexure-off timeout case. The QC script now selects only the numeric duration line; this is an independent reporting bug, not a physics or TISC failure. Existing timestamp, return code, and raw log are fully preserved in the artifact.

### Numerical measurements permanently preserved

See [performance measurements](../results/03_tectonics/PERFORMANCE_401_DIAGNOSTICS.csv), which explicitly identifies cases differing from author's source and distinguishes process exit from physical mass-balance acceptance.
