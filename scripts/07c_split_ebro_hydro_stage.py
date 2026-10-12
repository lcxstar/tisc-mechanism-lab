#!/usr/bin/env python3
"""Refine V07 grid snapshots INSIDE drainage stage; no change to physics."""
from pathlib import Path
import sys,json,hashlib
f=Path(sys.argv[1]);audit=Path(sys.argv[2])
src=f.read_text();old=src
def once(a,b):
    global src
    assert src.count(a)==1,(a,src.count(a))
    src=src.replace(a,b,1)
once('static void ebdiag_snapshot(ModelConfig *cfg, ModelContext *ctx, const char *phase) {\n    if (!ebdiag_active) return;',
     'static void ebdiag_snapshot(ModelConfig *cfg, ModelContext *ctx, const char *phase) {\n    if (!ebdiag_active || ebdiag_step > 1) return;')
for needle,label in [
  ('\t\tReSort_Matrix (ctx->topo, sortcell, cfg->Nx, cfg->Ny);','after_sort_topography'),
  ('\t\tDefine_Drainage_Net(sortcell, cfg, ctx);','after_define_drainage'),
  ('\t\tCalculate_Precipitation_Evaporation(cfg, ctx);','after_rain_evap'),
  ('\t\tIce_Flow(cfg, ctx, ice_velx_sl, ice_vely_sl, ice_velx_df, ice_vely_df, dt_st, &total_ice_melt, &total_ice_precip, &total_lost_water, &total_evap_water);','after_ice_water'),
  ('\t\tread_file_node_defs(cfg, ctx, dt_st);','after_custom_node_defs')]:
    once(needle,needle+'\n        ebdiag_snapshot(cfg,ctx,"'+label+'");')
f.write_text(src)
audit.parent.mkdir(exist_ok=True,parents=True)
d={'source':'pinned 2026 modern TISC original; NBSP compile normalization and V07a read-only instrumentation',
  'new_incremental_instrumentation':'Five stage boundaries inside each surface substep, saves only first substep complete native cell map',
  'stages':['after_increment','after_sort_topography','after_define_drainage','after_rain_evap','after_ice_water','after_custom_node_defs','after_routing','after_transport'],
  'underlying_physics_modified':False,'before_sha256':hashlib.sha256(old.encode()).hexdigest(),
  'after_sha256':hashlib.sha256(src.encode()).hexdigest()}
audit.write_text(json.dumps(d,indent=2));print(json.dumps(d))
