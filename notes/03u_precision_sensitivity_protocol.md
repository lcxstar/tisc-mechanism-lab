# 03u — Selective floating-point precision sensitivity protocol

**Started 2026-10-12. Status: experimental, independent of accepted 03t reference.**

## Confirmed starting point and why this experiment is needed

- Immutable original source: `danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd`, official `6_tectonics` demonstration.
- Accepted executable family: 03g fast lake grouping + 03j lake-discharge algorithm optimizations + explicitly labeled 03k negative fractional-slope domain guard + 03s independent 64-bit ledger + 03t corrected `sediment_balance` reporting.
- [03t corrected mass QC N121 full15 and N401 first2](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38165200144) both passed, threshold abs residual <0.001% and scientific outputs checked byte-identical to the matching uninstrumented baseline.
- [03t full 401 × 401, 0–15 Myr](https://github.com/lcxstar/tisc-mechanism-lab/actions/runs/38165304319) **completed successfully with 30 reported time steps**, max high-precision sediment mass residual **0.0001675273334%**. That is the new fixed-input numerical baseline. It does not establish numerical convergence of sediment thickness.
- Original 401 mass discrepancy at 1.5 Myr was 33.8423% with the float accumulator, vs ~0.000000513% with the double ledger. This *alone* is not evidence that float32 physics arrays are defective.
- 121-to-401 sediment-volume variation was approximately 15.5% in the prior 03l geological acceptance. Need distinguish resolution dependence, solver errors and rounding.
- Never replace every `float` in a C struct in-place: native `ModelContext`, `GRIDNODE`, drainage, `Blocks`, external solver libraries and binary restart serialization use different contracts.

## Experiments

### 03u-0 — read-only precision observability (**start now**)

Instrument the accepted 03t solver only at existing physical update sites without changing *any* state or array type, and report paired float/double mathematical updates to the same stored value.

- `Sediment`: count increments of nonzero `dh_sed` that do not change stored `Blocks[top].thick[row][col]`, `ctx->topo[row][col]` or load `Dq[row][col]`. Measure double-evaluated ideal increment, float rounding deficit and worst relative loss; retain a meaningful aggregate and count.
- `Erode`: measure such lost small `dh_eros_Block` in stored `Blocks`, and for total topography decrement. Do not use a virtual double geological model as if this alone described an alternate time-history.
- `Fluvial_Transport`: examine slope-to-float rounding from *already stored float elevations* using double arithmetic and track relative/absolute change. Avoid ascribing all numerical error to subtraction since operands are themselves rounded.
- `drainage.masstr`: separately count flow additions that round away compared with corresponding double addition. This is **rate transfer**, not global mass accounting.

Because hooks are read-only, require exact SHA256 equality for `demo.xyw`, `demo.st`, `demo.hrz`, `demo.lak`, `demo.bas`, `demo.pfl`, `demo.xyzt` versus accepted 03t with identical parameter files. Recompute dry-running N81/N121 tests first, then N401 first0.5. Keep log, sidecar CSV, original C source diff, compiler and upstream SHA.

### 03u-A — controlled local arithmetic promotions (**isolate per operator**)

If measurements reveal significant, relevant loss, separately promote an **intermediate only** (`dh_sed` in `Sediment`, for example) to double while leaving `float **Blocks[].thick` and `float **topo` unchanged; same input and model settings. Unlike observer 03u-0, this intentionally changes numerics and must not be called a byte-equivalence check. Compare fraction of changed cells, maximal |Δtopography|, Δsediment volume, routing basin boundaries, maximum thickness and total exported sediments to 03t baseline. Build each change in a separate patch; do not combine blindly.

A truly double state-storage experiment requires a new ABI/serialization-safe design and may have very different behavior due to drainage ordering; not authorized to mislabel a simple local change as “all double”.

### 03u-B — spatial topography and thickness precision

Only if targeted observation/experiments warrant: preserve double state for sediment thickness and/or local topo increment across repeated updates, with explicit conversion at existing output and interop boundaries, separate data types, and explicit restart versioning. Measure evolution trajectory for both 121 and 401 grids and compare 0.5/6/10/12/15 Myr. No tuning of Te, tectonic velocities or source/transport coefficients.

### 03u-C — flexure solver precision inventory

Inspect actual C/Fortran solver interfaces (including FFT/DCT if linked). Distinguish native double library operations from float interface arrays and outputs before designing a double solver experiment. Compare controlled isostasy-only outputs, downward deflection and final sediment fields. Do not assume pure double arithmetic is always preferable: consider precision-sensitive threshold decisions and time integration stability.

## Acceptance gates and possible interpretations

1. All original geological input files identical between variants; 03t baseline saved, source patches and SHA256 auditable. Pin author SHA.
2. 03u-0 observational variant must finish requested simulated horizon with **byte-identical** physical products. Fail rather than claim a credible diagnostic if physics outputs change.
3. No nonfinite height, stratigraphy, flux or sediment budget values; 64-bit corrected sediment error **<0.001%**.
4. For intentionally changed-physics 03u-A/B, quantify both differences and numerical convergence across **81, 121, 401** where practical. A nonzero physical difference is not automatically an improvement.
5. No automatic claim that 121/401 sediment-volume difference comes from single precision: separate grid-spacing from precision with a paired factorial design.
6. Detailed outcome table: measured counts and lost increments by process, runtime, max/topographic RMS difference (m), sediment thickness RMS/max difference (m), volume difference (%), flexure RMS/max (m), drainage changed-cell fraction, total mass residual (%).

**Decision not preordained:** retain 03t and do not promote physical arrays if rounding is geologically negligible; if measured losses are material, design and run localized source/state changes with independent validation. The 03k nonnegative-slope guard remains an earlier independent experimental physical change.
