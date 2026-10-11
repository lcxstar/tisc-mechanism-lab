#!/usr/bin/env python3
"""03r pure observational trace: isolate lake-entry vs Lake_Fill vs outlet mass.

Assumes 03q instrumentation already present. Capture source ledger plus all
suspended rates for two known problematic river->lake transfers. No formula
or physics input is changed.
"""
from pathlib import Path
import difflib,hashlib,json,sys
def one(s,o,n,label):
 c=s.count(o)
 if c!=1:raise RuntimeError(f"{label} expected one anchor, got {c}")
 return s.replace(o,n,1)
def main(src,out):
 src=Path(src);out=Path(out);b=src.read_bytes();s=b.decode()
 if "tisc03p_focus" not in s or "TISC_03Q" not in s:raise RuntimeError("03r after 03q")
 a=s.index("int Fluvial_Transport(struct GRIDNODE *sortcell");z=s.index("\n\nint Ice_Flow(ModelConfig",a);f=s[a:z]
 # Before downstream transfer, explicitly inspect incoming target type and lake.
 f=one(f,
  "\t\tint ild = drainage[drow][dcol].lake;\n\t\tfloat hl;",
  "\t\tint ild = drainage[drow][dcol].lake;\n"
  "\t\tif(tisc03p_focus) {\n"
  '\t\t\tfprintf(stderr,"\\nTISC_03R phase=DEST call=%d node=%d source_type=%c dest_type=%c "\n'
  '\t\t\t\t"source_rate=%.17g dest_rate=%.17g dest_lake=%d dest_lake_outlets=%d "\n'
  '\t\t\t\t"dest_drow=%d dest_dcol=%d dest_processed=%d\\n",\n'
  "\t\t\t\ttisc03o_call,isort,drainage[row][col].type,drainage[drow][dcol].type,\n"
  "\t\t\t\t(double)transfer_mass,(double)drainage[drow][dcol].masstr,\n"
  "\t\t\t\tild,ild?Lake[ild].n_sd:0,drainage[drow][dcol].dr_row,\n"
  "\t\t\t\tdrainage[drow][dcol].dr_col,(int)processed[drow*cfg->Nx+dcol]);\n"
  "\t\t}\n"
  "\t\tfloat hl;",
  "lake destination")
 # Before lake fill, only open-lake branch; identical call text twice original (open/closed), patch with unique surrounding.
 anchor="\t\t\t\thl = ctx->topo[row][col];  /*MIN_2 (Lake[ild].alt+1., ctx->topo[row][col]-1.);??*/\n\t\t\t\tLake_Fill (Lake, cfg, ctx, drow, dcol, hl, dt_st, lake_instant_fill);"
 replacement="\t\t\t\thl = ctx->topo[row][col];  /*MIN_2 (Lake[ild].alt+1., ctx->topo[row][col]-1.);??*/\n"
 replacement += (
  "\t\t\t\tif(tisc03p_focus) fprintf(stderr,\"\\nTISC_03R phase=BEFORE_LAKE_FILL call=%d node=%d lake=%d rate=%.17g source_sed_kg=%.17g stock_kg=%.17g\\n\",\n"
  "\t\t\t\t\ttisc03o_call,isort,ild,(double)drainage[drow][dcol].masstr,(double)ctx->total_sed_mass,tisc_03n_stock(cfg,(double)dt_st));\n"
  "\t\t\t\tLake_Fill (Lake, cfg, ctx, drow, dcol, hl, dt_st, lake_instant_fill);\n"
  "\t\t\t\tif(tisc03p_focus) fprintf(stderr,\"\\nTISC_03R phase=AFTER_LAKE_FILL call=%d node=%d lake=%d rate=%.17g source_sed_kg=%.17g stock_kg=%.17g\\n\",\n"
  "\t\t\t\t\ttisc03o_call,isort,ild,(double)drainage[drow][dcol].masstr,(double)ctx->total_sed_mass,tisc_03n_stock(cfg,(double)dt_st));")
 f=one(f,anchor,replacement,"open lake before-after")
 # After outlet reception and before clearing lake cell (happens whether open or closed).
 f=one(f,
  "\t\t\t/*Next line commented in tAo!!*/\n\t\t\tdrainage[drow][dcol].masstr = 0;",
  "\t\t\tif(tisc03p_focus) fprintf(stderr,\"\\nTISC_03R phase=BEFORE_LAKE_CLEAR call=%d node=%d lake=%d n_sd=%d rate=%.17g srcsed=%.17g export=%.17g stock=%.17g\\n\",\n"
  "\t\t\t\ttisc03o_call,isort,ild,Lake[ild].n_sd,(double)drainage[drow][dcol].masstr,\n"
  "\t\t\t\t(double)ctx->total_sed_mass,(double)*total_lost_sed_mass,tisc_03n_stock(cfg,(double)dt_st));\n"
  "\t\t\t/*Next line commented in tAo!!*/\n\t\t\tdrainage[drow][dcol].masstr = 0;",
  "lake-clear")
 s=s[:a]+f+s[z:];src.write_text(s);out.mkdir(parents=True,exist_ok=True)
 (out/"03R_AUDIT.json").write_text(json.dumps({"physics_modified":False,"source_before_sha256":hashlib.sha256(b).hexdigest(),"source_after_sha256":hashlib.sha256(s.encode()).hexdigest(),"questions":["destination type and lake outlet status","mass after Lake_Fill","before clearing recipient rate"],"author_sha":"d18b7d270f4d671b80223e10dede329ad35cafdd"},indent=2))
 (out/"03R.diff").write_text("".join(difflib.unified_diff(b.decode().splitlines(True),s.splitlines(True),fromfile="03q/surf_proc.c",tofile="03r/surf_proc.c")))
 print("03r lake reception trace inserted without changing physics")
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("profile_03r_lake_receiver.py SRC_C AUDIT_DIR")
 main(sys.argv[1],sys.argv[2])
