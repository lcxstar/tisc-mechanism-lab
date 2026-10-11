#!/usr/bin/env python3
"""03u-0 OBSERVER ONLY: float32 storage vs double64 single-addition precision.

No declared input types or original statements are changed; observations
are inserted before the exact original assignments. Each metric estimates
the local rounding error of *one* physical update to its existing FLOAT32
state. This does NOT simulate a persistent FLOAT64 physical state.
"""
import hashlib,json,difflib,sys
from pathlib import Path

HELPER=r'''
/* 03u observational numerical-precision study, no feedback to simulation. */
enum { TISC03U_TOPO_DEP=0, TISC03U_BLOCK_DEP=1, TISC03U_LOAD_DEP=2,
       TISC03U_TOPO_ERODE=3, TISC03U_BLOCK_ERODE=4,
       TISC03U_RIVER_TRANSFER=5, TISC03U_LAKE_TRANSFER=6,
       TISC03U_OUTLET_TRANSFER=7, TISC03U_NTYPES=8 };
static const char *tisc03u_name[TISC03U_NTYPES] = {
    "sediment_topo", "sediment_block", "sediment_Dq",
    "erosion_topo", "erosion_block",
    "river_inflow", "lake_inflow", "lake_outflow"
};
static struct {
    unsigned long long calls, tiny_dropped, finite_errors;
    double ideal_increment_sum, dropped_abs_sum, error_signed_sum;
    double error_abs_sum, max_abs_error, max_abs_dropped;
    double max_existing_value, max_abs_increment;
} tisc03u_stats[TISC03U_NTYPES];
static void tisc03u_note(int k, float original, float increment) {
    if (k<0 || k>=TISC03U_NTYPES ||
        !isfinite((double)original) || !isfinite((double)increment)) {
        return;
    }
    tisc03u_stats[k].calls++;
    if (fabs((double)original)>tisc03u_stats[k].max_existing_value)
        tisc03u_stats[k].max_existing_value=fabs((double)original);
    if (fabs((double)increment)>tisc03u_stats[k].max_abs_increment)
        tisc03u_stats[k].max_abs_increment=fabs((double)increment);
    /* Cast from the already stored float: this estimates storage-rounding
       at the CURRENT float state, not a hypothetical full-double history. */
    const double exact=(double)original+(double)increment;
    const float rounded=original+increment;
    const double err=(double)rounded-exact;
    if (!isfinite((double)rounded)) {
        tisc03u_stats[k].finite_errors++;
        return;
    }
    tisc03u_stats[k].ideal_increment_sum += (double)increment;
    tisc03u_stats[k].error_signed_sum += err;
    tisc03u_stats[k].error_abs_sum += fabs(err);
    if (fabs(err)>tisc03u_stats[k].max_abs_error)
        tisc03u_stats[k].max_abs_error=fabs(err);
    if (increment!=0 && rounded==original) {
        tisc03u_stats[k].tiny_dropped++;
        tisc03u_stats[k].dropped_abs_sum+=fabs((double)increment);
        if (fabs((double)increment)>tisc03u_stats[k].max_abs_dropped)
            tisc03u_stats[k].max_abs_dropped=fabs((double)increment);
    }
}
static void tisc03u_emit(double time_myr) {
    for (int k=0;k<TISC03U_NTYPES;k++) {
        fprintf(stderr,
          "\nTISC_03U0 kind=%s timeMyr=%.6f calls=%llu round_to_zero=%llu "
          "finite_errors=%llu ideal_increment_sum=%.17g dropped_abs_sum=%.17g "
          "error_signed_sum=%.17g error_abs_sum=%.17g max_abs_error=%.17g "
          "max_abs_dropped=%.17g max_existing=%.17g max_abs_increment=%.17g\n",
          tisc03u_name[k],time_myr,tisc03u_stats[k].calls,
          tisc03u_stats[k].tiny_dropped,tisc03u_stats[k].finite_errors,
          tisc03u_stats[k].ideal_increment_sum,tisc03u_stats[k].dropped_abs_sum,
          tisc03u_stats[k].error_signed_sum,tisc03u_stats[k].error_abs_sum,
          tisc03u_stats[k].max_abs_error,tisc03u_stats[k].max_abs_dropped,
          tisc03u_stats[k].max_existing_value,tisc03u_stats[k].max_abs_increment);
    }
    fflush(stderr);
}
'''
def replace_count(s,a,b,n,label):
    count=s.count(a)
    if count!=n:raise RuntimeError(f"{label}: expected {n} original anchors, found {count}")
    return s.replace(a,b)

def main(src,out):
    src=Path(src);out=Path(out);raw=src.read_bytes();s=raw.decode("utf-8")
    if "TISC_03T_CORRECTED_BALANCE" not in s or "tisc03s_sed_kg" not in s:
        raise RuntimeError("03u-0 requires already accepted 03t input")
    if "TISC_03U0" in s:raise RuntimeError("Already patched")
    s=replace_count(s,"int Surface_Transport (ModelConfig *cfg",
        HELPER+"\nint Surface_Transport (ModelConfig *cfg",1,"helper")
    st=s.index("int Surface_Transport (ModelConfig *cfg")
    end=s.index("int Calculate_Discharge (struct GRIDNODE *sortcell",st)
    part=s[st:end]
    part=replace_count(part,
        '\tPRINT_DEBUG("Calculating surface transport");',
        '\tPRINT_DEBUG("Calculating surface transport");\n'
        '\tmemset(tisc03u_stats, 0, sizeof(tisc03u_stats));',
        1,"observer-reset")
    part=replace_count(part,
       "\t/* Update lake elevations one last time to perfectly match final topography for output files */",
       "\ttisc03u_emit((double)(ctx->Time/Matosec));\n"
       "\t/* Update lake elevations one last time to perfectly match final topography for output files */",
       1,"report-at-time-step")
    s=s[:st]+part+s[end:]
    st=s.index("int Sediment (ModelConfig *cfg");end=s.index("int Erode (ModelConfig *cfg",st)
    part=s[st:end]
    part=replace_count(part,
      "\tDq[row][col] +=  dh_sed * g * (cfg->denssedim-cfg->densenv);",
      "\ttisc03u_note(TISC03U_LOAD_DEP, Dq[row][col], dh_sed * g * (cfg->denssedim-cfg->densenv));\n"
      "\tDq[row][col] +=  dh_sed * g * (cfg->denssedim-cfg->densenv);",1,"sediment-load")
    part=replace_count(part,
      "\t\tBlocks[ctx->numBlocks-1].thick[row][col] += dh_sed;",
      "\t\ttisc03u_note(TISC03U_BLOCK_DEP, Blocks[ctx->numBlocks-1].thick[row][col], dh_sed);\n"
      "\t\tBlocks[ctx->numBlocks-1].thick[row][col] += dh_sed;",1,"sediment-block")
    part=replace_count(part,
      "\tctx->topo[row][col] += dh_sed;",
      "\ttisc03u_note(TISC03U_TOPO_DEP,ctx->topo[row][col],dh_sed);\n"
      "\tctx->topo[row][col] += dh_sed;",1,"sediment-topography")
    s=s[:st]+part+s[end:]
    st=s.index("int Erode (ModelConfig *cfg");end=s.index("int Damn_River_Node (",st)
    part=s[st:end]
    part=replace_count(part,
      "\t\tBlocks[k].thick[row][col] -= dh_eros_Block;",
      "\t\ttisc03u_note(TISC03U_BLOCK_ERODE, Blocks[k].thick[row][col], -dh_eros_Block);\n"
      "\t\tBlocks[k].thick[row][col] -= dh_eros_Block;",1,"erosion-block")
    part=replace_count(part,
      "\tctx->topo[row][col] -= dh_eros;",
      "\ttisc03u_note(TISC03U_TOPO_ERODE,ctx->topo[row][col],-dh_eros);\n"
      "\tctx->topo[row][col] -= dh_eros;",1,"erosion-topo")
    s=s[:st]+part+s[end:]
    st=s.index("int Fluvial_Transport(struct GRIDNODE *sortcell")
    end=s.index("\n\nint Ice_Flow(ModelConfig",st)
    part=s[st:end]
    # two direct destination inflow accumulation sites have identical statement,
    # classify by destination at runtime.
    target="\t\t\tdrainage[drow][dcol].masstr += transfer_mass;"
    part=replace_count(part,target,
      "\t\t\ttisc03u_note(drainage[drow][dcol].type=='L' ? TISC03U_LAKE_TRANSFER : TISC03U_RIVER_TRANSFER,\n"
      "\t\t\t\tdrainage[drow][dcol].masstr,transfer_mass);\n"+target,2,"regular-transfer")
    part=replace_count(part,
       "\t\t\t\t\tdrainage[erow][ecol].masstr += drainage[drow][dcol].masstr;",
       "\t\t\t\t\ttisc03u_note(TISC03U_OUTLET_TRANSFER,drainage[erow][ecol].masstr,drainage[drow][dcol].masstr);\n"
       "\t\t\t\t\tdrainage[erow][ecol].masstr += drainage[drow][dcol].masstr;",1,"lake-outlet-transfer")
    s=s[:st]+part+s[end:]
    src.write_text(s);out.mkdir(parents=True,exist_ok=True)
    (out/"03U0_OBSERVER_AUDIT.json").write_text(json.dumps({
        "experiment":"03u-0 read-only per-operation float32 store vs float64 ideal update",
        "pinned_upstream":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd",
        "source_before_sha256":hashlib.sha256(raw).hexdigest(),
        "source_after_sha256":hashlib.sha256(s.encode()).hexdigest(),
        "physical_parameter_changes":False,"physical_state_type_changes":False,
        "original_code_statements_replaced":False,
        "measured_sites":["Sediment topo","Sediment top Block thick","Sediment Dq",
                          "Erode topo","Erode Blocks thick","R/E transport",
                          "Lake inlet","Open lake outlet"],
        "interpretation_warning":"A double hypothetical single update at CURRENT float state; not full double trajectory",
        "review_gate":"byte-for-byte seven forward output files versus 03t baseline"
    },indent=2))
    (out/"03U0_OBSERVER.diff").write_text("".join(difflib.unified_diff(raw.decode().splitlines(True),s.splitlines(True),
      fromfile="03t/accepted/surf_proc.c",tofile="03u0/observed/surf_proc.c")))
    print("03u-0 read-only precision observer added")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("profile_03u0_precision_updates.py C_SOURCE AUDIT_DIR")
    main(sys.argv[1],sys.argv[2])
