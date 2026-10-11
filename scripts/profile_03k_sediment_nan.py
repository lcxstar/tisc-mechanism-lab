#!/usr/bin/env python3
"""03k observational tracer: first nonfinite sediment mass and propagation.

Call after original-author NBSP normalization + 03g + 03j-A/B on ephemeral CI.
No physics inputs, formulas, control-flow branches or state values are changed.
Every trace branch ONLY emits diagnostic records and inspects isfinite().
"""
import difflib,hashlib,json,sys
from pathlib import Path

HELPER=r'''
/* 03k sediment first-NaN diagnostic-only tracing. */
static int tisc_03k_step = -1;
static int tisc_03k_nan_messages = 0;
static unsigned long long tisc_03k_nonfinite_observed = 0;
static void tisc_03k_sed_diag(const char *stage,int row,int col,
                    double mass,double masstr,double total_out,
                    double total_sed,double total_bed) {
    if (++tisc_03k_nan_messages<=32) {
       fprintf(stderr,
       "\nTISC_SED_DIAG stage=%s iter=%d row=%d col=%d mass=%.12g masstr=%.12g "
       "out_mass=%.12g sed_mass=%.12g bed_mass=%.12g\n",
       stage,tisc_03k_step,row,col,mass,masstr,total_out,total_sed,total_bed);
       fflush(stderr);
    }
    tisc_03k_nonfinite_observed++;
}
'''
def once(s,old,new,lab):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"03k tracer unsafe {lab}, exact anchor count {n}")
    return s.replace(old,new,1)
def section(s,begin,end,cb):
    i=s.index(begin);j=s.index(end,i+len(begin))
    return s[:i]+cb(s[i:j])+s[j:]

def patch_surface(part):
    part=once(part,
      "\t/*Distributes transport in 'n_iters' substeps:*/",
      "\t/*Distributes transport in 'n_iters' substeps:*/\n"
      "\tfprintf(stderr,\"\\nTISC_SED_DIAG phase=surface_start dt=%.12g dt_eros=%.12g iters=%d top_rain=%.12g\\n\",(double)ctx->dt,(double)ctx->dt_eros,n_iters,(double)rain);",
      "initial phase")
    part=once(part,
      "\tfor (int iter=0; iter<n_iters; iter++) {\t  \t  ",
      "\tfor (int iter=0; iter<n_iters; iter++) {\t  \t  \n"
      "\t\ttisc_03k_step=iter;",
      "substep tracker")
    part=once(part,
      "\t\tFluvial_Transport(sortcell, cfg, ctx, dt_st, &total_lost_sed_mass, lake_instant_fill);",
      '\t\tfprintf(stderr,"\\nTISC_SED_DIAG phase=before_fluvial iter=%d lost_sed=%.12g total_sed=%.12g total_bed=%.12g dt_st=%.12g\\n",iter,(double)total_lost_sed_mass,(double)ctx->total_sed_mass,(double)ctx->total_bedrock_eros_mass,(double)dt_st);\n'
      "\t\tFluvial_Transport(sortcell, cfg, ctx, dt_st, &total_lost_sed_mass, lake_instant_fill);\n"
      '\t\tfprintf(stderr,"\\nTISC_SED_DIAG phase=after_fluvial iter=%d lost_sed=%.12g total_sed=%.12g total_bed=%.12g nan_events=%llu\\n",iter,(double)total_lost_sed_mass,(double)ctx->total_sed_mass,(double)ctx->total_bedrock_eros_mass,tisc_03k_nonfinite_observed);\n'
      "\t\tfflush(stderr);",
      "fluvial-entry-exit")
    return part

def patch_fluvial(part):
    part=once(part,
      "\t\tfloat transfer_mass = drainage[row][col].masstr;",
      "\t\tif (!isfinite((double)d_mass) || !isfinite((double)drainage[row][col].masstr))\n"
      '\t\t\ttisc_03k_sed_diag("before_transfer",row,col,d_mass,drainage[row][col].masstr,*total_lost_sed_mass,ctx->total_sed_mass,ctx->total_bedrock_eros_mass);\n'
      "\t\tfloat transfer_mass = drainage[row][col].masstr;",
      "mass-before-transfer")
    # This is the first lake-outlet export aggregation.
    part=once(part,
      "\t\t\t\t\t*total_lost_sed_mass += drainage[drow][dcol].masstr * dt_st;",
      "\t\t\t\t\tif (!isfinite((double)drainage[drow][dcol].masstr) || !isfinite((double)*total_lost_sed_mass))\n"
      '\t\t\t\t\t\ttisc_03k_sed_diag("lake_outlet_export",drow,dcol,drainage[drow][dcol].masstr*dt_st,drainage[drow][dcol].masstr,*total_lost_sed_mass,ctx->total_sed_mass,ctx->total_bedrock_eros_mass);\n'
      "\t\t\t\t\t*total_lost_sed_mass += drainage[drow][dcol].masstr * dt_st;",
      "lake-outlet-export")
    part=once(part,
      "\t\t\t\t*total_lost_sed_mass += transfer_mass * dt_st;",
      "\t\t\t\tif (!isfinite((double)transfer_mass) || !isfinite((double)*total_lost_sed_mass))\n"
      '\t\t\t\t\ttisc_03k_sed_diag("boundary_export",row,col,transfer_mass*dt_st,transfer_mass,*total_lost_sed_mass,ctx->total_sed_mass,ctx->total_bedrock_eros_mass);\n'
      "\t\t\t\t*total_lost_sed_mass += transfer_mass * dt_st;",
      "boundary-export")
    return part

def patch_sediment(part):
    part=once(part,
      "\tfloat dh_sed;",
      "\tif (!isfinite(d_mass))\n"
      '\t\ttisc_03k_sed_diag("Sediment_nonfinite_input",row,col,d_mass,drainage[row][col].masstr,0,ctx->total_sed_mass,ctx->total_bedrock_eros_mass);\n'
      "\tfloat dh_sed;",
      "sediment-first-mass")
    part=once(part,
      "\tctx->total_sed_mass += d_mass;",
      "\tctx->total_sed_mass += d_mass;\n"
      "\tif (!isfinite((double)ctx->total_sed_mass))\n"
      '\t\ttisc_03k_sed_diag("Sediment_nonfinite_accumulator",row,col,d_mass,drainage[row][col].masstr,0,ctx->total_sed_mass,ctx->total_bedrock_eros_mass);',
      "sediment-final-accumulator")
    return part

def patch_erode(part):
    part=once(part,
      "\tfloat dh_eros=0, dh_eros_Block, mass_per_m2=d_mass/cfg->dx/cfg->dy;",
      "\tif (!isfinite(d_mass))\n"
      '\t\ttisc_03k_sed_diag("Erode_nonfinite_input",row,col,d_mass,drainage[row][col].masstr,0,ctx->total_sed_mass,ctx->total_bedrock_eros_mass);\n'
      "\tfloat dh_eros=0, dh_eros_Block, mass_per_m2=d_mass/cfg->dx/cfg->dy;",
      "erode-first-mass")
    part=once(part,
      "\tctx->topo[row][col] -= dh_eros;",
      "\tctx->topo[row][col] -= dh_eros;\n"
      "\tif (!isfinite((double)ctx->total_bedrock_eros_mass) || !isfinite((double)ctx->total_sed_mass))\n"
      '\t\ttisc_03k_sed_diag("Erode_nonfinite_accumulator",row,col,d_mass,drainage[row][col].masstr,0,ctx->total_sed_mass,ctx->total_bedrock_eros_mass);',
      "erode-accumulator")
    return part

def patch_lake_fill(part):
    part=once(part,
      "\tif (!drainage[row][col].masstr) return(0);",
      "\tif (!isfinite((double)drainage[row][col].masstr))\n"
      '\t\ttisc_03k_sed_diag("Lake_Fill_nonfinite_input",row,col,0,drainage[row][col].masstr,0,ctx->total_sed_mass,ctx->total_bedrock_eros_mass);\n'
      "\tif (!drainage[row][col].masstr) return(0);",
      "lake-fill-masstr")
    part=once(part,
      "\t\td_mass_now /= total_weight_distr;",
      "\t\tif (!isfinite((double)total_weight_distr) || total_weight_distr==0)\n"
      '\t\t\ttisc_03k_sed_diag("Lake_Fill_bad_weights",row,col,d_mass_now,drainage[row][col].masstr,0,ctx->total_sed_mass,ctx->total_bedrock_eros_mass);\n'
      "\t\td_mass_now /= total_weight_distr;",
      "lake-fill-denom")
    return part

def main(src,out):
    src=Path(src);out=Path(out);old=src.read_bytes();s=old.decode()
    if "tisc_03ja_lake_evap" not in s:raise RuntimeError("03k tracer requires 03j optimized source")
    if "TISC_SED_DIAG" in s:raise RuntimeError("Already traced")
    s=once(s,"int Surface_Transport (ModelConfig *cfg",HELPER+"\nint Surface_Transport (ModelConfig *cfg","helper entry")
    s=section(s,"int Surface_Transport (ModelConfig *cfg","int Calculate_Discharge (struct GRIDNODE *sortcell, ModelConfig *cfg, ModelContext *ctx, float *total_lost_water",patch_surface)
    s=section(s,"int Fluvial_Transport(struct GRIDNODE *sortcell","int Ice_Flow(ModelConfig *cfg",patch_fluvial)
    s=section(s,"int Lake_Fill (\n\tstruct LAKE_INFO *Lake","int Landslide_Transport (ModelConfig *cfg",patch_lake_fill)
    s=section(s,"int Sediment (ModelConfig *cfg","int Erode (ModelConfig *cfg",patch_sediment)
    s=section(s,"int Erode (ModelConfig *cfg","int Damn_River_Node (",patch_erode)
    src.write_text(s)
    out.mkdir(parents=True,exist_ok=True)
    (out/"03K_SEDIMENT_TRACE_AUDIT.json").write_text(json.dumps({
      "pinned_author_sha":"d18b7d270f4d671b80223e10dede329ad35cafdd",
      "before_sha256":hashlib.sha256(old).hexdigest(),
      "after_sha256":hashlib.sha256(s.encode()).hexdigest(),
      "physics_parameters_changed":False,
      "hydro_or_sediment_formulas_changed":False,
      "algorithm_changed":False,
      "extra_work":"diagnostic isfinite checks and stderr print only",
      "instrumented_functions":["Surface_Transport","Fluvial_Transport","Sediment","Erode","Lake_Fill"]
    },indent=2))
    (out/"03K_SEDIMENT_INSTRUMENTATION.diff").write_text("".join(difflib.unified_diff(
      old.decode().splitlines(True),s.splitlines(True),
      fromfile="03j-optimized/surf_proc.c",tofile="03k-sed-traced/surf_proc.c")))
    print("03k sediment diagnostics inserted with exact source anchors.")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("profile_03k_sediment_nan.py C_SOURCE AUDIT_DIR")
    main(sys.argv[1],sys.argv[2])
