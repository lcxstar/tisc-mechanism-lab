#!/usr/bin/env python3
"""03t safe, narrowly scoped fix for TISC reported sediment-mass balance.

The 03s independent double (float64) observer is already verified against the
original source fields and does not feed back to physical simulation.
03t switches ONLY the displayed erosion/deposition/export summary and the
sediment_balance warning to the float64 ledger. Original float32 context
fields, C struct ABI, on-disk restart serialization and all physics remain
untouched. Also emits an unrounded exact 64-bit mass audit at each step.

Not a mass-correction factor and not a rewrite of lake sediment transport.
"""
import hashlib,json,difflib,sys
from pathlib import Path
def main(source,out):
 p=Path(source);out=Path(out);b=p.read_bytes();s=b.decode()
 if "tisc03s_bed_kg" not in s:raise RuntimeError("03t requires 03s independent double ledger")
 if "TISC_03T_CORRECTED_BALANCE" in s:raise RuntimeError("03t already patched")
 i=s.index("int Surface_Transport (ModelConfig *cfg")
 j=s.index("int Calculate_Discharge (struct GRIDNODE *sortcell",i)
 f=s[i:j]
 start=f.index('\tPRINT_SUMLINE("eros_nosd:')
 end=f.index("\n\n\t/* Update lake elevations",start)
 old=f[start:end]
 if "mass_error = ctx->total_bedrock_eros_mass" not in old:raise RuntimeError("unexpected original budget source")
 new=r'''
    /* 03t: show the numerically conservative double-ledger mass budget.
     * Native ModelContext float32 is retained for upstream ABI compatibility,
     * but is unfit for a sum of millions of sub-ULP lake deposits. */
    PRINT_SUMLINE("eros_nosd: %+8.2e N\t sedim_inc: %+8.2e N   outp_seds:   %+8.2e N  ",
        tisc03s_bed_kg*g, tisc03s_sed_kg*g, tisc03s_export_kg*g);
    {
        double error = 0;
        const double mass_error = tisc03s_bed_kg - tisc03s_sed_kg - tisc03s_export_kg;
        double ref_mass = tisc03s_bed_kg;
        if (ref_mass == 0) ref_mass = tisc03s_export_kg;
        if (ref_mass == 0) ref_mass = fabs(tisc03s_sed_kg);
        if (ref_mass > 0) error = -mass_error / ref_mass * 100;
        fprintf(stderr,
            "\nTISC_03T_CORRECTED_BALANCE timeMyr=%.6f "
            "erosion_kg=%.17g net_deposition_kg=%.17g export_kg=%.17g "
            "balance_gap_kg=%.17g balance_pct=%.17g\n",
            (double)(ctx->Time/Matosec),tisc03s_bed_kg,tisc03s_sed_kg,
            tisc03s_export_kg,mass_error,error);
        fflush(stderr);
        if (fabs(error)>=.5 || (fabs(error)>=.1 && verbose_level>=3))
            PRINT_WARNING("sediment_balance: %.1f%% (>0 => sed>eros)", error);
    }
'''
 f=f[:start]+new+f[end:]
 s=s[:i]+f+s[j:];p.write_text(s);out.mkdir(parents=True,exist_ok=True)
 (out/"03T_CORRECTED_BUDGET_AUDIT.json").write_text(json.dumps({
    "scientific_scope":"Correct sediment mass accounting and warnings; retain physical simulation untouched",
    "before_sha256":hashlib.sha256(b).hexdigest(),
    "after_sha256":hashlib.sha256(s.encode()).hexdigest(),
    "author":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd",
    "depends_on":"03g+03j hydro speed and explicit 03k negative-slope physical correction plus independent 03s double ledger",
    "changes_source_equations":False,"changes_transport":False,
    "changes_native_float32_fields":False,"changes_serialization":False,
    "changes_user_prm":False,"uses_double_only_for":"printed eros_nosd/sedim_inc/outp_seds and sediment_balance diagnostics",
    "remaining_limitations":"numerical block thickening and 121-to-401 grid convergence not proved by a balanced ledger"
 },indent=2))
 (out/"03T_CORRECTED_BUDGET.diff").write_text("".join(difflib.unified_diff(b.decode().splitlines(True),s.splitlines(True),fromfile="03s/surf_proc.c",tofile="03t/surf_proc.c")))
 print("03t conservative sediment budget reporting replacement applied")
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("patch_03t_correct_sediment_balance.py SRC_C AUDIT_DIR")
 main(sys.argv[1],sys.argv[2])
