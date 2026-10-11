#!/usr/bin/env python3
"""03j-B conservative zero-evaporation lake-inflow decision fastpath.

Apply strictly AFTER 03g + 03j-A. This is *not* a generic incremental water
accumulator. It skips the quadratic Lake_Input_Discharge() in the per-node
evaporation deletion predicate only if a runtime-verifiable lower bound
shows no lake deletion is possible:

  lake_evap == 0 and every source summand of Lake_Input_Discharge >= 0.

All grid precipitation and discharge values are checked at entry. Seepage
(permeability != 0) disables the shortcut. During normal routing, the
nonnegative discharge invariant is checked for the current node and every
potential updated downstream node. Any violation permanently disables the
shortcut and returns to original computation for all remaining nodes.

If nonzero lake evaporation, the original full water inflow function is called
without altering its summation or numerical order. Nonzero evaporation is NOT
accelerated in 03j-B beyond the verified 03j-A cache.
"""
import difflib,hashlib,json,sys
from pathlib import Path
DECL="int Calculate_Discharge (struct GRIDNODE *sortcell, ModelConfig *cfg, ModelContext *ctx, float *total_lost_water, float *total_evap_water, float *total_underground_water)"

def once(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"03j-B {label} anchor count {n}")
    return s.replace(old,new,1)

def main(path,out):
    b=path.read_bytes();s=b.decode()
    if "tisc_03ja_lake_evap" not in s or "tisc_fast_merge_target" not in s:
        raise RuntimeError("Requires 03g and 03j-A source patches")
    start=s.index(DECL+"\n{")
    end=s.index("\n\n\nint constant_rate_eros (",start)
    p=s[start:end]
    p=once(p,
        "\ttisc_03ja_cache_hits=tisc_03ja_cache_misses=tisc_03ja_cache_invalidations=0;",
        "\ttisc_03ja_cache_hits=tisc_03ja_cache_misses=tisc_03ja_cache_invalidations=0;\n"
        "\tunsigned long long tisc_03jb_predicate_skips=0, tisc_03jb_predicate_fallbacks=0;\n"
        "\tint tisc_03jb_safe=(permeability==0);\n"
        "\tif (tisc_03jb_safe) {\n"
        "\t\tfor (int rr=0; rr<cfg->Ny && tisc_03jb_safe; rr++)\n"
        "\t\t\tfor (int cc=0; cc<cfg->Nx; cc++) {\n"
        "\t\t\t\tif (!isfinite(precipitation[rr][cc]) || precipitation[rr][cc]<0 ||\n"
        "\t\t\t\t    !isfinite(drainage[rr][cc].discharge) || drainage[rr][cc].discharge<0) {\n"
        "\t\t\t\t\ttisc_03jb_safe=0; break;\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        "\t}",
        "initial-invariant-check")
    p=once(p,
        "\t\t\t\tif (Lake_Input_Discharge(cfg, il)<lake_evap && Lake[il].n>1) {",
        "\t\t\t\t/* 03j-B: every term in input-sum is nonnegative while invariant holds.\n"
        "\t\t\t\t * If evaporation is EXACTLY zero, deletion inequality is false.\n"
        "\t\t\t\t * For any other value, original summation is evaluated unchanged. */\n"
        "\t\t\t\tint tisc_03jb_definitely_no_delete=(tisc_03jb_safe && lake_evap==0);\n"
        "\t\t\t\tif (tisc_03jb_definitely_no_delete) tisc_03jb_predicate_skips++;\n"
        "\t\t\t\telse tisc_03jb_predicate_fallbacks++;\n"
        "\t\t\t\tif (!tisc_03jb_definitely_no_delete && Lake_Input_Discharge(cfg, il)<lake_evap && Lake[il].n>1) {",
        "conservative-predicate")
    p=once(p,
        "\t\t\tdrainage[row][col].C_Cl = final_C_Cl;\n\t}\n",
        "\t\t\t\tdrainage[row][col].C_Cl = final_C_Cl;\n"
        "\t\t\t/* Check every possible flow write destination before next node.\n"
        "\t\t\t * Once violated, original path is permanently restored. */\n"
        "\t\t\tif (tisc_03jb_safe) {\n"
        "\t\t\t\tif (!isfinite(drainage[row][col].discharge) || drainage[row][col].discharge<0)\n"
        "\t\t\t\t\ttisc_03jb_safe=0;\n"
        "\t\t\t\tif (IN_DOMAIN(drow,dcol)) {\n"
        "\t\t\t\t\tif (!isfinite(drainage[drow][dcol].discharge) || drainage[drow][dcol].discharge<0)\n"
        "\t\t\t\t\t\ttisc_03jb_safe=0;\n"
        "\t\t\t\t\tif (drainage[drow][dcol].type=='L' &&\n"
        "\t\t\t\t\t    IN_DOMAIN(drainage[drow][dcol].dr_row, drainage[drow][dcol].dr_col)) {\n"
        "\t\t\t\t\t\tint r2=drainage[drow][dcol].dr_row, c2=drainage[drow][dcol].dr_col;\n"
        "\t\t\t\t\t\tif (!isfinite(drainage[r2][c2].discharge) || drainage[r2][c2].discharge<0)\n"
        "\t\t\t\t\t\t\ttisc_03jb_safe=0;\n"
        "\t\t\t\t\t}\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        "\t}\n",
        "dynamic-invariant-maintenance")
    p=once(p,
        '\tfprintf(stderr,"\\nTISC_03J_A hits=%llu misses=%llu invalidations=%llu grid=%d\\n",',
        '\tfprintf(stderr,"\\nTISC_03J_B zero_evap_proven_skips=%llu original_predicate_fallbacks=%llu nonnegative_invariant_at_end=%d grid=%d\\n",\n'
        '\t\ttisc_03jb_predicate_skips,tisc_03jb_predicate_fallbacks,tisc_03jb_safe,Nx*Ny);\n'
        '\tfprintf(stderr,"\\nTISC_03J_A hits=%llu misses=%llu invalidations=%llu grid=%d\\n",',
        "summary")
    s=s[:start]+p+s[end:];path.write_text(s)
    out.mkdir(parents=True,exist_ok=True)
    (out/"03J_B_AUDIT.json").write_text(json.dumps({
        "patch":"03j-B proof-gated zero-evaporation lake-input fastpath",
        "baseline":"03g + 03j-A",
        "pinned_upstream":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd",
        "before_sha256":hashlib.sha256(b).hexdigest(),
        "after_sha256":hashlib.sha256(s.encode()).hexdigest(),
        "nonzero_evap_inflow_sum":"identical original helper",
        "zero_evap_shortcut":"only if ALL initial grid terms >=0, permeability=0 and no later negative discharge has occurred",
        "invariant_invalidated_on_negative":"permanent fallback to original helper",
        "changes_physical_parameters":False,
        "generic_incremental_lake_inflow_cache":False,
        "requires_forward_output_equivalence_tests":True
    },indent=2))
    (out/"03J_B.diff").write_text("".join(difflib.unified_diff(
        b.decode().splitlines(True),s.splitlines(True),
        fromfile="03j-A/surf_proc.c",tofile="03j-B/surf_proc.c")))
    print("03j-B guarded zero evaporation shortcut applied")

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("patch_03j_zero_evap_fastpath.py C_SOURCE AUDIT_DIR")
    main(Path(sys.argv[1]),Path(sys.argv[2]))
