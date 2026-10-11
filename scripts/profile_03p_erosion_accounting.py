#!/usr/bin/env python3
"""03p focused, NONMUTATING forensic line-by-line river erosion audit.

In two already proven R-type cells with unexplained mass:
  t=0.5, call20 isort149193 row63 col83
  t=1.0, call24 isort136214 row146 col130
Log d_mass, original initial rate, delta total bedrock and sediment mass
strictly across Erode(), and flux before/after downstream transport.

Requires sequential 03g+03j+03k+03n+03o. No physics adjustments.
"""
from pathlib import Path
import hashlib,difflib,json,sys
def once(s,o,n,name):
 c=s.count(o)
 if c!=1:raise RuntimeError(f"03p anchor {name} expected once got {c}")
 return s.replace(o,n,1)
def main(source,out):
 source=Path(source);out=Path(out);b=source.read_bytes();s=b.decode()
 if "tisc03o_fluv_call_count" not in s:raise RuntimeError("Apply after 03o patch")
 a=s.index("int Fluvial_Transport(struct GRIDNODE *sortcell");z=s.index("\n\nint Ice_Flow(ModelConfig",a);f=s[a:z]
 f=once(f,
   "\t\tint tisc03o_focus=((tisc03o_call==20 && isort>=148480 && isort<=149504) ||",
   "\t\tint tisc03p_focus=((tisc03o_call==20 && isort==149193) ||\n"
   "\t\t                    (tisc03o_call==24 && isort==136214));\n"
   "\t\tint tisc03o_focus=((tisc03o_call==20 && isort>=148480 && isort<=149504) ||",
   "target-cell-selector")
 f=once(f,
   "\t\t/*Adds results to the topo and the next load Dq and removes/adds material to the Blocks*/",
   "\t\tif (tisc03p_focus) {\n"
   '\t\t\tfprintf(stderr,"\\nTISC_03P_PRE cellrow=%d col=%d call=%d isort=%d dmass=%.17g masstr_in=%.17g discharge=%.17g slope_top=%.17g sourceBed=%.17g sourceSed=%.17g destrow=%d destcol=%d\\n",\n'
   "\t\t\t\trow,col,tisc03o_call,isort,(double)d_mass,(double)drainage[row][col].masstr,\n"
   "\t\t\t\t(double)drainage[row][col].discharge,(double)ctx->topo[row][col],\n"
   "\t\t\t\t(double)ctx->total_bedrock_eros_mass,(double)ctx->total_sed_mass,drow,dcol);\n"
   "\t\t\tfflush(stderr);\n"
   "\t\t}\n"
   "\t\t/*Adds results to the topo and the next load Dq and removes/adds material to the Blocks*/",
   "pre-cell-accounting")
 f=once(f,
   "\t\t\t\tErode\t(cfg, ctx, d_mass, row, col);",
   "\t\t\t\tdouble tisc03p_bed_pre=(double)ctx->total_bedrock_eros_mass;\n"
   "\t\t\t\tdouble tisc03p_sed_pre=(double)ctx->total_sed_mass;\n"
   "\t\t\t\tErode\t(cfg, ctx, d_mass, row, col);\n"
   "\t\t\t\tif (tisc03p_focus) {\n"
   '\t\t\t\t\tfprintf(stderr,"\\nTISC_03P_ERODE call=%d node=%d row=%d col=%d "\n'
   '\t\t\t\t\t"requested_dmass=%.17g delta_bed_kg=%.17g delta_sed_kg=%.17g accounted_net_kg=%.17g ero_minus_accounted_kg=%.17g\\n",\n'
   "\t\t\t\t\t tisc03o_call,isort,row,col,(double)d_mass,\n"
   "\t\t\t\t\t (double)ctx->total_bedrock_eros_mass-tisc03p_bed_pre,\n"
   "\t\t\t\t\t (double)ctx->total_sed_mass-tisc03p_sed_pre,\n"
   "\t\t\t\t\t (double)ctx->total_bedrock_eros_mass-tisc03p_bed_pre-tisc03p_sed_pre+(double)ctx->total_sed_mass,\n"
   "\t\t\t\t\t (double)ctx->total_bedrock_eros_mass-tisc03p_bed_pre-tisc03p_sed_pre+(double)ctx->total_sed_mass-(double)d_mass);\n"
   "\t\t\t\t\tfflush(stderr);\n"
   "\t\t\t\t}\n",
   "Erode source mass")
 f=once(f,
   "\t\tfloat transfer_mass = drainage[row][col].masstr;",
   "\t\tif (tisc03p_focus) {\n"
   '\t\t\tfprintf(stderr,"\\nTISC_03P_BEFORE_ROUTE call=%d node=%d row=%d col=%d "\n'
   '\t\t\t\t"masstr_rate=%.17g dmass=%.17g dtst=%.17g downstock_rate=%.17g\\n",\n'
   "\t\t\t\ttisc03o_call,isort,row,col,(double)drainage[row][col].masstr,(double)d_mass,(double)dt_st,\n"
   "\t\t\t\tIN_DOMAIN(drow,dcol)?(double)drainage[drow][dcol].masstr:0.0);\n"
   "\t\t}\n"
   "\t\tfloat transfer_mass = drainage[row][col].masstr;",
   "rate before routing")
 # Target final per-node logs already included by 03o so no extra after.
 s=s[:a]+f+s[z:]
 source.write_text(s);out.mkdir(parents=True,exist_ok=True)
 (out/"03P_RIVER_ACCOUNTING_AUDIT.json").write_text(json.dumps({
 "source_before":hashlib.sha256(b).hexdigest(),"source_after":hashlib.sha256(s.encode()).hexdigest(),
 "edits_physics":False,"focus_cells":[[20,149193,63,83],[24,136214,146,130]],
 "tests":"d_mass vs Erode delta bedrock minus change in sediment stock; rate sent to downstream, mass residual from 03o",
 "upstream":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd"},indent=2))
 (out/"03P_RIVER_ACCOUNTING.diff").write_text("".join(difflib.unified_diff(b.decode().splitlines(True),s.splitlines(True),fromfile="03o/surf_proc.c",tofile="03p/surf_proc.c")))
 print("03p river source-vs-transport checks applied")
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("profile_03p_erosion_accounting.py SOURCE_C AUDIT_DIR")
 main(sys.argv[1],sys.argv[2])
