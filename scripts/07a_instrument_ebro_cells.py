#!/usr/bin/env python3
"""Attach read-only per-substep TISC cell, routing and mass diagnostics.

Patch ONLY pinned upstream's surf_proc.c in a disposable Actions checkout.
The added snapshots do not mutate Dq, topo, water, sediment or routing.
Require exact anchors to fail closed when upstream C changes.
"""
from pathlib import Path
import argparse,hashlib,json
ap=argparse.ArgumentParser()
ap.add_argument("source",type=Path)
ap.add_argument("audit",type=Path)
args=ap.parse_args()
f=args.source
before=f.read_text()
def once(old,new):
    global source
    assert source.count(old)==1,(old[:80],source.count(old))
    source=source.replace(old,new,1)
source=before
head=r'''
/* BEGIN EBRO V07 INSTRUMENTATION -- READ ONLY -- GENERATED */
static FILE *ebdiag_fp = NULL;
static double *ebdiag_eroded = NULL, *ebdiag_deposited = NULL;
static int ebdiag_cols = 0, ebdiag_rows = 0, ebdiag_step=0;
static int ebdiag_active=0, ebdiag_completed=0;
static void ebdiag_mass(int deposit, double mass, int r, int c) {
    if (!ebdiag_active || !isfinite(mass) || mass < 0 ||
        r < 0 || c < 0 || r >= ebdiag_rows || c >= ebdiag_cols) return;
    const int k=r*ebdiag_cols+c;
    if (deposit) ebdiag_deposited[k]+=mass;
    else ebdiag_eroded[k]+=mass;
}
static void ebdiag_open(ModelConfig *cfg) {
    if (ebdiag_completed || ebdiag_active) return;
    const char *p=getenv("EBRO_V07_DIAGNOSTIC_PATH");
    if (!p || !*p) return;
    ebdiag_fp=fopen(p,"w");
    if (!ebdiag_fp) {fprintf(stderr,"V07 failed to open %s\n",p);exit(73);}
    ebdiag_cols=cfg->Nx;ebdiag_rows=cfg->Ny;
    size_t n=(size_t)ebdiag_cols*ebdiag_rows;
    ebdiag_eroded=calloc(n,sizeof(double));
    ebdiag_deposited=calloc(n,sizeof(double));
    if (!ebdiag_eroded || !ebdiag_deposited) exit(74);
    fprintf(ebdiag_fp,"step,phase,row,col,x_km,y_km,topo_m,dr_row,dr_col,discharge_m3s,masstr_kg_s,eroded_kg,deposited_kg,Dq_Pa,lake_id,node_type\n");
    ebdiag_active=1;
}
static void ebdiag_snapshot(ModelConfig *cfg, ModelContext *ctx, const char *phase) {
    if (!ebdiag_active) return;
    double zmax=-1e100,zmin=1e100;int rmax=-1,cmax=-1;
    for (int i=0;i<cfg->Ny;i++) for (int j=0;j<cfg->Nx;j++) {
        int k=i*cfg->Nx+j;
        double z=ctx->topo[i][j];
        if (z > zmax) {zmax=z;rmax=i;cmax=j;} if(z < zmin) zmin=z;
        fprintf(ebdiag_fp,
          "%d,%s,%d,%d,%.9g,%.9g,%.9g,%d,%d,%.9g,%.9g,%.13g,%.13g,%.9g,%d,%d\n",
          ebdiag_step,phase,i,j,(cfg->xmin+j*cfg->dx)/1000.,
          (cfg->ymax-i*cfg->dy)/1000.,z,
          drainage[i][j].dr_row,drainage[i][j].dr_col,
          drainage[i][j].discharge,drainage[i][j].masstr,
          ebdiag_eroded[k],ebdiag_deposited[k],Dq[i][j],
          drainage[i][j].lake,(int)drainage[i][j].type);
    }
    fprintf(stderr,"V07STEP step=%d phase=%s zmax_m=%.9g at row=%d col=%d zmin_m=%.9g\n",
          ebdiag_step,phase,zmax,rmax,cmax,zmin);
    fflush(ebdiag_fp);
}
static void ebdiag_reset(ModelConfig *cfg, int step) {
    if (!ebdiag_active) return;
    ebdiag_step=step;
    size_t n=(size_t)cfg->Nx*cfg->Ny;
    memset(ebdiag_eroded,0,n*sizeof(double));
    memset(ebdiag_deposited,0,n*sizeof(double));
}
static void ebdiag_close(void) {
    if (ebdiag_active) {
       fflush(ebdiag_fp);fclose(ebdiag_fp);
       free(ebdiag_eroded);free(ebdiag_deposited);
       ebdiag_fp=NULL;ebdiag_eroded=NULL;ebdiag_deposited=NULL;
       ebdiag_active=0;ebdiag_completed=1;
    }
}
/* END EBRO V07 INSTRUMENTATION */
'''
once('int Surface_Transport (ModelConfig *cfg, ModelContext *ctx, float **topo_ant, int lake_instant_fill) ',head+'\nint Surface_Transport (ModelConfig *cfg, ModelContext *ctx, float **topo_ant, int lake_instant_fill) ')
once('\t/*Distributes transport in \'n_iters\' substeps:*/','\tebdiag_open(cfg);\n\t/*Distributes transport in \'n_iters\' substeps:*/')
once('\tfor (int iter=0; iter<n_iters; iter++) {\t  ','\tfor (int iter=0; iter<n_iters; iter++) {\t  \n        ebdiag_reset(cfg,iter+1);')
once('\t\t/*Resorts the matrix of topography.*/','\t\tebdiag_snapshot(cfg,ctx,"after_increment");\n\t\t/*Resorts the matrix of topography.*/')
once('\t\tCalculate_Discharge(sortcell, cfg, ctx, &total_lost_water, &total_evap_water, &total_underground_water);',
     '\t\tCalculate_Discharge(sortcell, cfg, ctx, &total_lost_water, &total_evap_water, &total_underground_water);\n        ebdiag_snapshot(cfg,ctx,"after_routing");')
once('\t\tFluvial_Transport(sortcell, cfg, ctx, dt_st, &total_lost_sed_mass, lake_instant_fill);',
     '\t\tFluvial_Transport(sortcell, cfg, ctx, dt_st, &total_lost_sed_mass, lake_instant_fill);\n        ebdiag_snapshot(cfg,ctx,"after_transport");')
once('\t\tIce_EroSed(cfg, ctx, ice_velx_sl, ice_vely_sl, dt_st, &total_ice_eros, &total_ice_sedim);\n\t}',
     '\t\tIce_EroSed(cfg, ctx, ice_velx_sl, ice_vely_sl, dt_st, &total_ice_eros, &total_ice_sedim);\n\t}\n    ebdiag_close();')
once('\tdh_sed = MASS2SEDTHICK(cfg, d_mass);','\tebdiag_mass(1,d_mass,row,col);\n\tdh_sed = MASS2SEDTHICK(cfg, d_mass);')
once('\tfloat dh_eros=0, dh_eros_Block, mass_per_m2=d_mass/cfg->dx/cfg->dy;',
     '\tfloat dh_eros=0, dh_eros_Block, mass_per_m2=d_mass/cfg->dx/cfg->dy;\n\tebdiag_mass(0,d_mass,row,col);')
f.write_text(source)
args.audit.parent.mkdir(parents=True,exist_ok=True)
q={'instrument_type':'READ_ONLY diagnostics except allocating memory and writing diagnostic CSV','source':'surf_proc.c',
'original_sha256':hashlib.sha256(before.encode()).hexdigest(),'patched_sha256':hashlib.sha256(source.encode()).hexdigest(),
'original_anchor_requirements':8,'snapshot_phases':['after_increment','after_routing','after_transport'],
'capture':'first main tectonic 0.5 Myr only; 3 maps each erosion transport substep; all 22880 cells',
'per_cell_columns':['elevation','drainage receiver','water discharge','sediment transported mass flux',
'eroded and deposited material mass during substep','sediment/isostatic load increment Dq','lake/type']}
args.audit.write_text(json.dumps(q,indent=2))
print(json.dumps(q,indent=2))
