#!/usr/bin/env python3
"""03k: prove/refute negative-slope fractional-power cause of NaN in mode 6.

Injected immediately before the official dh=...pow(slope,spl_n) formula,
without modifying slope, C math result, routing, model inputs or equations.
Requires profile_03k_sediment_nan.py first.
"""
from pathlib import Path
import hashlib,difflib,json,sys

def unique(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"{label} ambiguous source anchor {n}")
    return s.replace(old,new,1)
def main(src,out):
    src=Path(src);out=Path(out);b=src.read_bytes();s=b.decode()
    if "TISC_SED_DIAG" not in s:raise RuntimeError("03k NaN tracer must be applied first")
    if "TISC_03K_SLOPE" in s:raise RuntimeError("Already instrumented")
    s=unique(s,
        "static int tisc_03k_nan_messages = 0;",
        "static int tisc_03k_nan_messages = 0;\nstatic int tisc_03k_slope_messages = 0;",
        "add slope-limited counter")
    first=s.index("int Fluvial_Transport(struct GRIDNODE *sortcell")
    last=s.index("\n\nint Ice_Flow(ModelConfig",first)
    f=s[first:last]
    i=f.index("case 6:")
    j=f.index("case 7:",i)
    seg=f[i:j]
    target="\t\t\t\t\t\tfloat dh;\n\t\t\t\t\t\t\tdh = erodibility_aux/secsperyr * pow(1020*g, a)"
    replacement=(
      "\t\t\t\t\t\tfloat dh;\n"
      "\t\t\t\t\t\t/* 03k diagnostic only: upstream fractional power of potentially negative slope. */\n"
      "\t\t\t\t\t\tif ((slope < 0 || !isfinite((double)slope) || !isfinite((double)drainage[row][col].discharge)) &&\n"
      "\t\t\t\t\t\t    (tisc_03k_slope_messages++ < 40 || (Nx==401 && row==400 && col==151) ||\n"
      "\t\t\t\t\t\t     (Nx==121 && row==19 && col==120))) {\n"
      "\t\t\t\t\t\t\tfprintf(stderr,\n"
      '\t\t\t\t\t\t\t"\\nTISC_03K_SLOPE iter=%d row=%d col=%d boundary=%d type=%c drow=%d dcol=%d "\n'
      '\t\t\t\t\t\t\t"slope=%.12g spl_n=%.12g main_tribut_slope=%.12g "\n'
      '\t\t\t\t\t\t\t"discharge=%.12g masstr=%.12g transp_capacity_eq=%.12g "\n'
      '\t\t\t\t\t\t\t"erodibility=%.12g dist=%.12g topography=%.12g\\n",\n'
      "\t\t\t\t\t\t\ttisc_03k_step,row,col,AT_BORDER(row,col),drainage[row][col].type,drow,dcol,\n"
      "\t\t\t\t\t\t\t(double)slope,(double)spl_n,(double)main_tribut_slope,\n"
      "\t\t\t\t\t\t\t(double)drainage[row][col].discharge,(double)drainage[row][col].masstr,\n"
      "\t\t\t\t\t\t\t(double)transp_capacity_eq,(double)erodibility_aux,(double)dist,\n"
      "\t\t\t\t\t\t\t(double)ctx->topo[row][col]);\n"
      "\t\t\t\t\t\t\tfflush(stderr);\n"
      "\t\t\t\t\t\t}\n"
      "\t\t\t\t\t\t\tdh = erodibility_aux/secsperyr * pow(1020*g, a)"
    )
    seg=unique(seg,target,replacement,"inception point for fractional exponent")
    f=f[:i]+seg+f[j:]
    s=s[:first]+f+s[last:]
    src.write_text(s)
    out.mkdir(parents=True,exist_ok=True)
    (out/"03K_SLOPE_TRACE_AUDIT.json").write_text(json.dumps({
       "upstream_commit":"d18b7d270f4d671b80223e10dede329ad35cafdd",
       "before_sha":hashlib.sha256(b).hexdigest(),
       "after_sha":hashlib.sha256(s.encode()).hexdigest(),
       "location":"Fluvial_Transport, mode 6, immediately before pow(slope,spl_n)",
       "physical_parameter_change":False,"equation_change":False,
       "first_nonfinite_n121":"row19,col120",
       "first_nonfinite_n401":"row400,col151",
       "printed_when":"negative or nonfinite slope/discharge, first 40; always first known failing cells",
    },indent=2))
    (out/"03K_SLOPE_TRACE.diff").write_text("".join(difflib.unified_diff(
       b.decode().splitlines(True),s.splitlines(True),
       fromfile="03k-nan-tracer/surf_proc.c",
       tofile="03k-slope-tracer/surf_proc.c")))
    print("03k signed slope instrumentation added")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("profile_03k_slope_pow.py SOURCE_C AUDIT_DIR")
    main(sys.argv[1],sys.argv[2])
