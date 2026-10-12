#!/usr/bin/env python3
"""More first-step controls using reusable 06b pristine source runner."""
import sys,runpy
from pathlib import Path
base=runpy.run_path(str(Path(__file__).with_name('06b_ebro_firststep_interventions.py')))
f=base['main']
f.__globals__['CASES']={
 "10_hydro_off_erosion_on":{"opts":["-qhydro_model=0"]},
 "11_hydro_on_erosion_off":{"opts":["-qerosed_model=0"]},
 "12_dt_eros_0025":{"opts":["-te0.025"]},
 "13_dt_eros_0005":{"opts":["-te0.005"]},
 "14_dt_005_eros0005":{"opts":["-td0.05","-te0.005"]},
 "15_no_initial_random_topo":{"opts":["-qrandom_topo=0"]},
 "16_no_fluvial_capacity":{"opts":["-qK_river_cap=0"]},
 "17_no_topographic_diffusion":{"opts":["-qKerosdif=0"]},
 "18_old_2017_N104_N55_eros0025":{"opts":[],"prm_overrides":{"Nx":"104","Ny":"55","dt_eros":".025"}},
 "19_old_grid_N104_N55_eros005":{"opts":[],"prm_overrides":{"Nx":"104","Ny":"55"}},
 "20_current_grid_eros0025":{"opts":[],"prm_overrides":{"dt_eros":".025"}},
}
if __name__=='__main__':
    f()
