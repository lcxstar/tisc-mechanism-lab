#!/usr/bin/env python3
"""03q paired stock and sediment ledger checkpoints, purely observational.

Two known first mass-discrepant ordinary river cells, stage PRE, POST_SED,
POST_ROUTE. Includes physical Erode/Sediment totals, current+downstream
masstr, global stock and routing processed[dst] flag. No formulas change.
"""
from pathlib import Path
import hashlib,difflib,json,sys
def one(s,o,n,name):
  c=s.count(o)
  if c!=1:raise ValueError(f"{name}: expected unique anchor got {c}")
  return s.replace(o,n,1)
def main(src,out):
  src=Path(src);out=Path(out);b=src.read_bytes();s=b.decode()
  if "tisc03p_focus" not in s or "tisc_03n_stock" not in s:raise ValueError("apply to 03p+03o+03n branch")
  a=s.index("int Fluvial_Transport(struct GRIDNODE *sortcell"); z=s.index("\n\nint Ice_Flow(ModelConfig",a)
  f=s[a:z]
  f=one(f,
    "\t\t/*Adds results to the topo and the next load Dq and removes/adds material to the Blocks*/",
    "\t\tdouble tisc03q_before=0;\n"
    "\t\tif (tisc03p_focus) {\n"
    "\t\t\ttisc03q_before=(double)ctx->total_bedrock_eros_mass-(double)ctx->total_sed_mass-\n"
    "\t\t\t\t(double)*total_lost_sed_mass-tisc_03n_stock(cfg,(double)dt_st);\n"
    '\t\t\tfprintf(stderr,"\\nTISC_03Q stage=PRE call=%d node=%d row=%d col=%d dmass=%.17g "\n'
    '\t\t\t\t"bed=%.17g sed=%.17g out=%.17g stock=%.17g "\n'
    '\t\t\t\t"here_rate=%.17g dest_rate=%.17g dst_processed=%d\\n",\n'
    "\t\t\t\ttisc03o_call,isort,row,col,(double)d_mass,(double)ctx->total_bedrock_eros_mass,\n"
    "\t\t\t\t(double)ctx->total_sed_mass,(double)*total_lost_sed_mass,tisc_03n_stock(cfg,(double)dt_st),\n"
    "\t\t\t\t(double)drainage[row][col].masstr,\n"
    "\t\t\t\tIN_DOMAIN(drow,dcol)?(double)drainage[drow][dcol].masstr:0.0,\n"
    "\t\t\t\tIN_DOMAIN(drow,dcol)?(int)processed[drow*cfg->Nx+dcol]:-1);\n"
    "\t\t}\n"
    "\t\t/*Adds results to the topo and the next load Dq and removes/adds material to the Blocks*/",
    "pre")
  f=one(f,
    "\t\tdrainage[row][col].masstr += d_mass/dt_st;",
    "\t\tdrainage[row][col].masstr += d_mass/dt_st;\n"
    "\t\tif (tisc03p_focus) {\n"
    "\t\t\tdouble stock=tisc_03n_stock(cfg,(double)dt_st);\n"
    "\t\t\tdouble r=(double)ctx->total_bedrock_eros_mass-(double)ctx->total_sed_mass-\n"
    "\t\t\t\t(double)*total_lost_sed_mass-stock;\n"
    '\t\t\tfprintf(stderr,"\\nTISC_03Q stage=POST_SED call=%d node=%d row=%d col=%d dmass=%.17g "\n'
    '\t\t\t\t"resdelta=%.17g bed=%.17g sed=%.17g out=%.17g stock=%.17g "\n'
    '\t\t\t\t"here_rate=%.17g dest_rate=%.17g dst_processed=%d\\n",\n'
    "\t\t\t\ttisc03o_call,isort,row,col,(double)d_mass,r-tisc03q_before,\n"
    "\t\t\t\t(double)ctx->total_bedrock_eros_mass,(double)ctx->total_sed_mass,\n"
    "\t\t\t\t(double)*total_lost_sed_mass,stock,(double)drainage[row][col].masstr,\n"
    "\t\t\t\tIN_DOMAIN(drow,dcol)?(double)drainage[drow][dcol].masstr:0.0,\n"
    "\t\t\t\tIN_DOMAIN(drow,dcol)?(int)processed[drow*cfg->Nx+dcol]:-1);\n"
    "\t\t}\n",
    "post sediment")
  f=one(f,
    "\t\t/* Periodically recompute every cell's in-flight sediment at read-only intervals. */",
    "\t\tif (tisc03p_focus) {\n"
    "\t\t\tdouble stock=tisc_03n_stock(cfg,(double)dt_st);\n"
    "\t\t\tdouble r=(double)ctx->total_bedrock_eros_mass-(double)ctx->total_sed_mass-\n"
    "\t\t\t\t(double)*total_lost_sed_mass-stock;\n"
    '\t\t\tfprintf(stderr,"\\nTISC_03Q stage=POST_ROUTE call=%d node=%d row=%d col=%d "\n'
    '\t\t\t\t"resdelta=%.17g bed=%.17g sed=%.17g out=%.17g stock=%.17g "\n'
    '\t\t\t\t"here_rate=%.17g dest_rate=%.17g dst_processed=%d\\n",\n'
    "\t\t\t\ttisc03o_call,isort,row,col,r-tisc03q_before,\n"
    "\t\t\t\t(double)ctx->total_bedrock_eros_mass,(double)ctx->total_sed_mass,\n"
    "\t\t\t\t(double)*total_lost_sed_mass,stock,(double)drainage[row][col].masstr,\n"
    "\t\t\t\tIN_DOMAIN(drow,dcol)?(double)drainage[drow][dcol].masstr:0.0,\n"
    "\t\t\t\tIN_DOMAIN(drow,dcol)?(int)processed[drow*cfg->Nx+dcol]:-1);\n"
    "\t\t}\n"
    "\t\t/* Periodically recompute every cell's in-flight sediment at read-only intervals. */",
    "post route")
  s=s[:a]+f+s[z:];src.write_text(s);out.mkdir(parents=True,exist_ok=True)
  (out/"03Q_AUDIT.json").write_text(json.dumps({"physics_modified":False,"pinned_author":"d18b7d270f4d671b80223e10dede329ad35cafdd","before_sha256":hashlib.sha256(b).hexdigest(),"after_sha256":hashlib.sha256(s.encode()).hexdigest(),"sample_calls":[20,24],"stages":["PRE","POST_SED","POST_ROUTE"]},indent=2))
  (out/"03Q.diff").write_text("".join(difflib.unified_diff(b.decode().splitlines(True),s.splitlines(True),fromfile="03p/surf_proc.c",tofile="03q/surf_proc.c")))
  print("03q tripartite source stock diagnostics inserted")
if __name__=="__main__":
  if len(sys.argv)!=3:raise SystemExit("profile_03q_mass_stages.py SRC_C DIAG_DIR")
  main(sys.argv[1],sys.argv[2])
