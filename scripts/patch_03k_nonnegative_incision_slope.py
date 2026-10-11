#!/usr/bin/env python3
"""EXPERIMENTAL SCIENTIFIC correction: nonnegative incision slope in mode 6.

This is NOT merely faster, NOT byte-identical to author, and NOT automatically
an approved source repair. The original mode-6 expression
  pow((double)slope, (double)spl_n)
gives NaN for the observed tiny negative slopes on no-downstream boundary
outlets; do not pass them to fractional-power incision laws.

For slope >=0, evaluate exactly the original pow arguments/order. For a
strictly negative slope (non-descending geometry), use zero incision slope.
NaN slopes themselves remain NaN and are NOT silently masked.
"""
from pathlib import Path
import difflib,hashlib,json,sys

def exactly(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"03k slope guard {label}, anchor count {n}")
    return s.replace(old,new,1)
def main(src,out):
    src=Path(src);out=Path(out)
    old=src.read_bytes();s=old.decode()
    if "tisc_03ja_lake_evap" not in s:raise RuntimeError("Requires 03j optimized source")
    if "TISC_03K_GUARD" in s:raise RuntimeError("Guard already installed")
    first=s.index("int Fluvial_Transport(struct GRIDNODE *sortcell")
    last=s.index("\n\nint Ice_Flow(ModelConfig",first)
    part=s[first:last]
    part=exactly(part,
      '\tPRINT_DEBUG("Calculating fluvial_transport");',
      '\tPRINT_DEBUG("Calculating fluvial_transport");\n'
      '\tunsigned long long tisc_03k_guard_hits=0;',
      "local hit counter")
    i=part.index("case 6:");j=part.index("case 7:",i)
    clause=part[i:j]
    clause=exactly(clause,
      "\t\t\t\t\t\tfloat dh;\n\t\t\t\t\t\t\tdh = erodibility_aux/secsperyr * pow(1020*g, a)",
      "\t\t\t\t\t\tfloat dh;\n"
      "\t\t\t\t\t\t/* 03k EXPERIMENTAL domain guard: uphill/negative slope => zero incision. */\n"
      "\t\t\t\t\t\tdouble tisc_03k_incision_slope=(double)slope;\n"
      "\t\t\t\t\t\tif (slope<0.0f) {\n"
      "\t\t\t\t\t\t\ttisc_03k_incision_slope=0.0;\n"
      "\t\t\t\t\t\t\ttisc_03k_guard_hits++;\n"
      "\t\t\t\t\t\t}\n"
      "\t\t\t\t\t\t\tdh = erodibility_aux/secsperyr * pow(1020*g, a)",
      "guard immediately before fractional exponent")
    clause=exactly(clause,"* pow((double)slope,\t\t\t\t\t\t(double)spl_n)",
                   "* pow(tisc_03k_incision_slope,\t\t\t\t\t\t(double)spl_n)",
                   "fractional pow argument")
    part=part[:i]+clause+part[j:]
    part=exactly(part,
      "\tfree(processed);\n\treturn(1);",
      "\tfree(processed);\n"
      '\tfprintf(stderr,"\\nTISC_03K_GUARD negative_incision_slopes=%llu grid=%d substep=%d\\n",tisc_03k_guard_hits,Nx*Ny,tisc_03k_guard_hits>0?1:0);\n'
      "\tfflush(stderr);\n"
      "\treturn(1);",
      "report guard")
    s=s[:first]+part+s[last:]
    src.write_text(s);out.mkdir(parents=True,exist_ok=True)
    (out/"03K_EXPERIMENTAL_SLOPE_GUARD_AUDIT.json").write_text(json.dumps({
       "status":"EXPERIMENTAL SCIENTIFIC CHANGE, NOT PURE REPRODUCTION",
       "pinned_original_author":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd",
       "source_sha_before":hashlib.sha256(old).hexdigest(),
       "source_sha_after":hashlib.sha256(s.encode()).hexdigest(),
       "physics_change":True,
       "parameters_unchanged":True,
       "purpose":"NaN caused by negative slope raised to mode 6 noninteger exponent ~1.05",
       "semantics":"slope<0 => zero-incision slope, slope>=0 preserves original pow operand",
       "NaN_input_slope_masked":False,
       "requires_invariant_tests":True,
    },indent=2))
    (out/"03K_EXPERIMENTAL_SLOPE_GUARD.diff").write_text("".join(difflib.unified_diff(
        old.decode().splitlines(True),s.splitlines(True),
        fromfile="03j-optimized/surf_proc.c",
        tofile="03k-physical-correction/surf_proc.c")))
    print("03k experimental physics slope-guard applied; source diff and caveat saved")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("patch_03k_nonnegative_incision_slope.py SOURCE_C AUDIT_DIR")
    main(sys.argv[1],sys.argv[2])
