# Ebro exact first-substep salt precipitation branch evidence

The original 2026 Ebro template defaults to salt_model=0. The current Calculate_Discharge code computes salt precipitation without consulting that flag.
Only the original disposable C checkout and diagnostic probes are altered; original geological inputs are unchanged.

| Variant | Maximum z at -59.5 Ma (m) | Max load (MPa) | Source-proximate salt sink events | Exit |
|---|---:|---:|---:|---:|
| A_original_salt_default_0 | 9071.6 | 195.0 | 557 | 0 |
| B_explicit_salt_model_0 | 9071.6 | 195.0 | 557 | 0 |
| C_original_ions_forced_zero | 1521.6 | 28.9 | 0 | 0 |
| D_guarded_salt_model_0 | 1521.6 | 28.9 | 0 | 0 |
| E_guarded_salt_model_1 | 9071.6 | 195.0 | 557 | 0 |

## First extreme cell salt-flux and physically effective switches

**A_original_salt_default_0**
`V07SALTEVENT branch=direct salt_model=0 row=83 col=130 precip_gypsum_kg_s=67.6605072 precip_halite_kg_s=95.584877 rise_m=7401.09863 dt_sec=1.57783674e+12`
**B_explicit_salt_model_0**
`V07SALTEVENT branch=direct salt_model=0 row=83 col=130 precip_gypsum_kg_s=67.6605072 precip_halite_kg_s=95.584877 rise_m=7401.09863 dt_sec=1.57783674e+12`
**E_guarded_salt_model_1**
`V07SALTEVENT branch=direct salt_model=1 row=83 col=130 precip_gypsum_kg_s=67.6605072 precip_halite_kg_s=95.584877 rise_m=7401.09863 dt_sec=1.57783674e+12`

**Scope:** an experimental conditional is not a validated upstream fix; all 60-Myr original/source divergence and sediment history require independent full-model QA.
