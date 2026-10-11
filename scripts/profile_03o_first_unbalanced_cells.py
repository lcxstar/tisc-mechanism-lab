#!/usr/bin/env python3
"""03o: tightly focus 03n local mass changes around largest unexplained chunks.

Assumes 10 fluvial substeps per 0.5 Myr in fixed author's example.
Focus: fluvial call 20 (last substep 0.5 Myr), nodes 148480-149504;
       fluvial call 24 (substep 3 of 1.0 Myr), nodes 136192-137216.
Perform read-only whole-grid suspended-mass scan before/after each node
within the window; exact physics and order unchanged.
"""
from pathlib import Path
import difflib,hashlib,json,sys
def once(s,o,n,label):
    count=s.count(o)
    if count!=1:raise RuntimeError(f"{label}: found {count} expected source anchors")
    return s.replace(o,n,1)
def main(src,out):
    p=Path(src);out=Path(out);b=p.read_bytes();s=b.decode()
    if "tisc_03n_stock" not in s:raise RuntimeError("requires 03n patch")
    a=s.index("int Fluvial_Transport(struct GRIDNODE *sortcell");z=s.index("\n\nint Ice_Flow(ModelConfig",a);f=s[a:z]
    f=once(f,
       "\tdouble tisc03n_drop_closed_kg=0.0;",
       "\tdouble tisc03n_drop_closed_kg=0.0;\n"
       "\tstatic int tisc03o_fluv_call_count=0;\n"
       "\tint tisc03o_call=++tisc03o_fluv_call_count;\n"
       "\tint tisc03o_hit_count=0;",
       "call counter")
    f=once(f,
       "\t\trow = sortcell[isort].row;  col = sortcell[isort].col;",
       "\t\trow = sortcell[isort].row;  col = sortcell[isort].col;\n"
       "\t\tint tisc03o_focus=((tisc03o_call==20 && isort>=148480 && isort<=149504) ||\n"
       "\t\t                   (tisc03o_call==24 && isort>=136192 && isort<=137216));\n"
       "\t\tdouble tisc03o_begin_balance=0;\n"
       "\t\tif (tisc03o_focus) tisc03o_begin_balance=(double)ctx->total_bedrock_eros_mass-\n"
       "\t\t\t(double)ctx->total_sed_mass-(double)*total_lost_sed_mass-\n"
       "\t\t\ttisc_03n_stock(cfg,(double)dt_st);",
       "before node")
    f=once(f,
      "\t\t/* Periodically recompute every cell's in-flight sediment at read-only intervals. */",
      "\t\tif (tisc03o_focus) {\n"
      "\t\t\tdouble after_balance=(double)ctx->total_bedrock_eros_mass-\n"
      "\t\t\t\t(double)ctx->total_sed_mass-(double)*total_lost_sed_mass-\n"
      "\t\t\t\ttisc_03n_stock(cfg,(double)dt_st);\n"
      "\t\t\tdouble delta=after_balance-tisc03o_begin_balance;\n"
      "\t\t\tif (fabs(delta)>1e10 && tisc03o_hit_count++<45) {\n"
      '\t\t\t\tfprintf(stderr,"\\nTISC_03O_CELL t=%.6f call=%d node=%d row=%d col=%d "\n'
      '\t\t\t\t"dest_row=%d dest_col=%d type=%c lake=%d delta_kg=%.17g "\n'
      '\t\t\t\t"masstr_after_kgps=%.17g closed_reset_kg=%.17g\\n",\n'
      "\t\t\t\t(double)(ctx->Time/Matosec),tisc03o_call,isort,row,col,drow,dcol,\n"
      "\t\t\t\tdrainage[row][col].type,drainage[row][col].lake,delta,\n"
      "\t\t\t\t(double)drainage[row][col].masstr,tisc03n_drop_closed_kg);\n"
      "\t\t\t\tfflush(stderr);\n"
      "\t\t\t}\n"
      "\t\t}\n"
      "\t\t/* Periodically recompute every cell's in-flight sediment at read-only intervals. */",
      "after node")
    s=s[:a]+f+s[z:]
    p.write_text(s);out.mkdir(parents=True,exist_ok=True)
    (out/"03O_TARGETED_ROUTING_AUDIT.json").write_text(json.dumps({
        "before_sha256":hashlib.sha256(b).hexdigest(),
        "after_sha256":hashlib.sha256(s.encode()).hexdigest(),
        "physical_change":False,
        "source":"03n verified first large residual chunks",
        "calls":{"20":[148480,149504],"24":[136192,137216]},
        "mass_formula":"bedrock - net_deposited - exported - in_flight; difference after one route cell",
        "read_only":True,"notes":"possible floating-point differences due to diagnostic work; preserve forward-equivalence QC separately"
    },indent=2))
    (out/"03O_TARGETED_ROUTING.diff").write_text("".join(difflib.unified_diff(b.decode().splitlines(True),s.splitlines(True),fromfile="03n/surf_proc.c",tofile="03o/surf_proc.c")))
    print("03o target mass-audit window installed.")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("profile_03o_first_unbalanced_cells.py SOURCE_C AUDIT_DIR")
    main(sys.argv[1],sys.argv[2])
