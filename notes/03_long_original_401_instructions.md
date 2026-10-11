# Manual extended-runtime test for the original 401 × 401 TISC demonstration

GitHub-hosted runner limit is **6 hours per job**, even for public repositories where standard runner compute minutes are free. There are **two** possible time limits: the job's `timeout-minutes` and any explicit `timeout` command used to launch the TISC process.

The three unsuccessful official attempts ended because our own command used `timeout 1800` (**30 minutes**) before reaching the 0.5 Myr step. All three returned **124**, not a demonstrated TISC crash.

The manual workflow [03-long | Exact 401×401 official TISC extended runtime](../.github/workflows/03_long_original_401.yml) now offers runtime 60, 120 (default), 240 or 330 minutes. Its job limit is 350 minutes, allowing time for compilation, archival and validation. These are **upper limits, not predicted runtimes**.

## How to launch

1. Open [the 401 long workflow](https://github.com/lcxstar/tisc-mechanism-lab/actions/workflows/03_long_original_401.yml).
2. Click **Run workflow**, choose branch `main`.
3. Choose `runtime_minutes`. Start with **120**, only consider **240** or **330** if logs show the numerical time steps are advancing.
4. Run it. Progress heartbeats print the most recent model time every 120 seconds.
5. At the end, download the `TISC03_401_ORIGINAL_LONG_...` artifact even if the run is marked failed. It includes raw `RUN.log`, full or partial model output, original SHA256 audit, `RUNTIME_STATS.txt`, `EXIT_CODE.txt`, and `ORIGINAL_401_QC.json`.

## Interpretation and scientific gate

- A run can time out with code 124 despite correctly compiling and starting. This **does not count** as reproduction.
- A normal process exit after 15 Myr counts as **completion**, not by itself as scientifically valid mass conservation.
- NaN in logged `outp_seds` means sediment-flux QC has failed; do not use the run as a validated basin filling model.
- Even all-finite `outp_seds` must still be checked for conservation residual and physically plausible routing before claiming meaningful sediment preservation.

## Efficiency caution

Previous experiments established that a 401-grid run remains stalled even with flexure disabled when the hydrology/surface path is still enabled. With hydrology disabled, a 0–0.5 Myr test finished in well under a second, whereas keeping hydrology enabled still timed out after 120 seconds.

The unmodified author's initial topography is **uniformly 100 m**; the upstream `surf_proc.c` contains nested processing of equal-height nodes. These facts support investigation of a pathological flat-terrain routing algorithm, but we have **not** timed the individual routines yet.

Extending the timeout is reasonable as a bounded test, **not** an alternative to the active water-routing performance diagnosis. No tectonic, lithospheric or geological parameter is changed by this manual workflow.

References: [GitHub Actions execution limits](https://docs.github.com/en/actions/reference/limits), [GitHub Actions billing for public repositories](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
