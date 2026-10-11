#!/usr/bin/env python3
"""03n read-only mass-continuity checkpoints inside Fluvial_Transport.

At node intervals compute:
  R = bedrock_source - net_rock/sediment_deposit - exported_mass - in-flight_suspended_mass
  delta R = R_now - R_before_first_cell
The stock uses the exact existing drainage[i][j].masstr times dt_st.
No formulas, model parameters or control branches are changed.
"""
from pathlib import Path
import difflib,hashlib,json,sys
HELPER=r'''
/* 03n forensic mass-only observation; runs on separate research branch. */
static double tisc_03n_stock(ModelConfig *cfg, double dtst) {
    double rate=0.0;
    for (int i=0;i<cfg->Ny;i++)
        for (int j=0;j<cfg->Nx;j++)
            rate+=(double)drainage[i][j].masstr;
    return rate*dtst;
}
'''
def once(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"03n source anchor {label} found {n} times")
    return s.replace(old,new,1)
def main(source,out):
    source=Path(source);out=Path(out)
    b=source.read_bytes();s=b.decode()
    if "TISC_03K_GUARD" not in s or "tisc_03ja_lake_evap" not in s:raise RuntimeError("Requires candidate 03k slope guard + 03j baseline")
    h="int Fluvial_Transport(struct GRIDNODE *sortcell, ModelConfig *cfg, ModelContext *ctx, float dt_st, float *total_lost_sed_mass, int lake_instant_fill)"
    s=once(s,h,HELPER+"\n"+h,"before_flv")
    i=s.index(h);j=s.index("\n\nint Ice_Flow(ModelConfig",i);f=s[i:j]
    f=once(f,
      "\tbool *processed = calloc(cfg->Nx * cfg->Ny, sizeof(bool));",
      "\tbool *processed = calloc(cfg->Nx * cfg->Ny, sizeof(bool));\n"
      "\tdouble tisc03n_drop_closed_kg=0.0;\n"
      "\tdouble tisc03n_start_balance=(double)ctx->total_bedrock_eros_mass-(double)ctx->total_sed_mass-\n"
      "\t\t(double)*total_lost_sed_mass-tisc_03n_stock(cfg,(double)dt_st);\n"
      "\tdouble tisc03n_max_abs_delta=0.0;\n"
      "\tint tisc03n_max_row=-1,tisc03n_max_col=-1;\n",
      "loop-init")
    f=once(f,
      "\t\t\t/*Next line commented in tAo!!*/\n\t\t\tdrainage[drow][dcol].masstr = 0;",
      "\t\t\t/* 03n trace mass cleared after CLOSED lake handling, not forwarded lake outlets. */\n"
      "\t\t\tif (!Lake[ild].n_sd) tisc03n_drop_closed_kg += (double)drainage[drow][dcol].masstr * (double)dt_st;\n"
      "\t\t\t/*Next line commented in tAo!!*/\n\t\t\tdrainage[drow][dcol].masstr = 0;",
      "closed-lake-reset")
    f=once(f,
      "\t\t}\n\t}\n\tfree(processed);\n",
      "\t\t}\n"
      "\t\t/* Periodically recompute every cell's in-flight sediment at read-only intervals. */\n"
      "\t\tif ((isort%1024)==0 || isort==cfg->Nx*cfg->Ny-1) {\n"
      "\t\t\tdouble tisc03n_stock_kg=tisc_03n_stock(cfg,(double)dt_st);\n"
      "\t\t\tdouble tisc03n_budget=(double)ctx->total_bedrock_eros_mass-(double)ctx->total_sed_mass-\n"
      "\t\t\t\t(double)*total_lost_sed_mass-tisc03n_stock_kg;\n"
      "\t\t\tdouble tisc03n_delta=tisc03n_budget-tisc03n_start_balance;\n"
      "\t\t\tif (fabs(tisc03n_delta)>tisc03n_max_abs_delta) {\n"
      "\t\t\t\ttisc03n_max_abs_delta=fabs(tisc03n_delta);\n"
      "\t\t\t\ttisc03n_max_row=row;tisc03n_max_col=col;\n"
      "\t\t\t}\n"
      "\t\t\tfprintf(stderr,\n"
      '\t\t\t\t"\\nTISC_03N_CHUNK timeMyr=%.6f node=%d row=%d col=%d "\n'
      '\t\t\t\t"delta_budget_kg=%.17g stock_kg=%.17g source_kg=%.17g "\n'
      '\t\t\t\t"net_sed_kg=%.17g exported_kg=%.17g closed_lake_mass_reset_kg=%.17g\\n",\n'
      "\t\t\t\t(double)(ctx->Time/Matosec),isort,row,col,tisc03n_delta,tisc03n_stock_kg,\n"
      "\t\t\t\t(double)ctx->total_bedrock_eros_mass,(double)ctx->total_sed_mass,\n"
      "\t\t\t\t(double)*total_lost_sed_mass,tisc03n_drop_closed_kg);\n"
      "\t\t\tfflush(stderr);\n"
      "\t\t}\n"
      "\t}\n"
      '\tfprintf(stderr,"\\nTISC_03N_SUMMARY timeMyr=%.6f max_abs_delta_kg=%.17g row=%d col=%d closed_mass_reset_kg=%.17g\\n",\n'
      "\t\t(double)(ctx->Time/Matosec),tisc03n_max_abs_delta,tisc03n_max_row,tisc03n_max_col,tisc03n_drop_closed_kg);\n"
      "\tfree(processed);\n",
      "loop-interval-timing")
    s=s[:i]+f+s[j:]
    source.write_text(s)
    out.mkdir(parents=True,exist_ok=True)
    (out/"03N_MASS_ROUTING_TRACE_AUDIT.json").write_text(json.dumps({
        "what":"source-sediment-export minus suspended-stock ledger at isort intervals",
        "source_before":hashlib.sha256(b).hexdigest(),
        "source_after":hashlib.sha256(s.encode()).hexdigest(),
        "physical_formulas_changed":False,
        "note":"suspended mass calculated as drainage.masstr*dt; source - net_deposition - export - suspended; initial offset subtracted",
        "source_commit":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd",
        "frequency":"every 1024th river node in each hydrological substep"
    },indent=2))
    (out/"03N_MASS_ROUTING_TRACE.diff").write_text("".join(difflib.unified_diff(
       b.decode().splitlines(True),s.splitlines(True),
       fromfile="03k-candidate/surf_proc.c",tofile="03n-routing-trace/surf_proc.c")))
    print("03n streamwise mass-source-sink diagnostic applied")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("profile_03n_mass_routing.py SOURCE_C AUDIT_DIR")
    main(sys.argv[1],sys.argv[2])
