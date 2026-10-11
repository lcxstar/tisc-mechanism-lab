#!/usr/bin/env python3
"""03i: zero-physics-change nested timing of Calculate_Discharge.

Apply to *temporary upstream checkout* after, in order:
  normalize_upstream_nbsp.py
  patch_fast_lake_membership.py [03g validated source derivative]
  profile_tisc_surface.py
  profile_tisc_drainage.py

The patch records cumulative costs of repeated lake evaporation scans,
Lake_Input_Discharge, rain/outlet routing, subsurface transfer, attempted lake
deletion, salts, lake volumes and final checks.  Original calculations stay in
their original order. Source anchors, hashes and diff are archived.
"""
from pathlib import Path
import hashlib
import difflib
import json
import re
import sys

HELPERS=r'''
/* 03i TISC-LAB observability only, requires 03d wall timer. */
static int tisc_03i_active=0, tisc_03i_substep=0;
static unsigned long long tisc_03i_lake_input_calls=0, tisc_03i_lake_input_nodes=0;
static unsigned long long tisc_03i_lake_input_outlets=0, tisc_03i_attempt_calls=0;
static unsigned long long tisc_03i_lake_nodes=0, tisc_03i_outlet_nodes=0;
static unsigned long long tisc_03i_max_lake_size=0;
static double tisc_03i_clock_start=0, tisc_03i_precheck_s=0;
static double tisc_03i_outlet_rain_s=0, tisc_03i_outlet_evap_s=0;
static double tisc_03i_permeability_s=0, tisc_03i_attempt_s=0;
static double tisc_03i_lake_input_s=0, tisc_03i_salt_deposit_s=0;
static double tisc_03i_lake_volume_s=0, tisc_03i_checks_s=0;
static void tisc_03i_report(const char *event, const char *stage, int nodes) {
    fprintf(stderr,
      "\nTISC_DISCHARGE event=%s stage=%s substep=%d nodes=%d grid=%d "
      "elapsed_s=%.6f precheck_s=%.6f lake_input_s=%.6f "
      "outlet_rain_s=%.6f outlet_evap_s=%.6f "
      "permeability_s=%.6f attempt_delete_s=%.6f "
      "salt_deposit_s=%.6f lake_volume_s=%.6f checks_s=%.6f "
      "lake_input_calls=%llu lake_input_nodes=%llu lake_input_outlets=%llu "
      "attempt_calls=%llu lake_nodes=%llu outlet_nodes=%llu max_lake_size=%llu "
      "nlakes=%d\n",
      event, stage, tisc_03i_substep, nodes, Nx*Ny,
      tisc_lab_wall_seconds()-tisc_03i_clock_start,
      tisc_03i_precheck_s, tisc_03i_lake_input_s,
      tisc_03i_outlet_rain_s, tisc_03i_outlet_evap_s,
      tisc_03i_permeability_s, tisc_03i_attempt_s,
      tisc_03i_salt_deposit_s, tisc_03i_lake_volume_s, tisc_03i_checks_s,
      tisc_03i_lake_input_calls, tisc_03i_lake_input_nodes,
      tisc_03i_lake_input_outlets, tisc_03i_attempt_calls,
      tisc_03i_lake_nodes, tisc_03i_outlet_nodes, tisc_03i_max_lake_size,
      nlakes);
    fflush(stderr);
}
/* End 03i diagnostic helpers. */
'''

def once(s, old, new, label):
    count=s.count(old)
    if count!=1:
        raise RuntimeError(f"03i unsafe patch {label}: expected 1 anchor, got {count}")
    return s.replace(old,new,1)

def extract_function(s,decl):
    first=s.find(decl+"\n{")
    if first<0 or s.find(decl+"\n{",first+1)>=0:
        raise RuntimeError("03i expected one exact function definition: "+decl)
    begin=s.index("{", first)
    depth=0
    # Avoid general C parser; this function contains braces in comments,
    # so use a next-definition anchor outside the function instead.
    if decl.startswith("int Calculate_Discharge"):
        endmarker="\n\n\nint constant_rate_eros ("
        end=s.find(endmarker,begin)
        if end<0: raise RuntimeError("Missing next top-level function marker")
        return first,end
    if decl.startswith("float Lake_Input_Discharge"):
        endmarker="\n\n\nint Lake_Node_Number"
        end=s.find(endmarker,begin)
        if end<0: raise RuntimeError("Missing following Lake_Node_Number")
        return first,end
    raise ValueError(decl)

def patch_lake_input(s):
    decl="float Lake_Input_Discharge (ModelConfig *cfg, int ilake) "
    start=s.index(decl+"\n{")
    finish=s.index("\n\n\nint Lake_Node_Number",start)
    part=s[start:finish]
    part=once(part,
      "\tint \ti;\n\tfloat \tinput_discharge=0;",
      "\tint \ti;\n\tfloat \tinput_discharge=0;\n"
      "\tdouble tisc_03i_input_start=0;\n"
      "\tif (tisc_03i_active) {\n"
      "\t\ttisc_03i_input_start=tisc_lab_wall_seconds();\n"
      "\t\ttisc_03i_lake_input_calls++;\n"
      "\t\ttisc_03i_lake_input_nodes += (unsigned long long)Lake[ilake].n;\n"
      "\t\ttisc_03i_lake_input_outlets += (unsigned long long)Lake[ilake].n_sd;\n"
      "\t}", "lake-input-entry")
    part=once(part,
      "\treturn (input_discharge);",
      "\tif (tisc_03i_active) tisc_03i_lake_input_s += tisc_lab_wall_seconds()-tisc_03i_input_start;\n"
      "\treturn (input_discharge);", "lake-input-exit")
    return s[:start]+part+s[finish:]

def patch_discharge(s):
    decl="int Calculate_Discharge (struct GRIDNODE *sortcell, ModelConfig *cfg, ModelContext *ctx, float *total_lost_water, float *total_evap_water, float *total_underground_water)"
    start=s.index(decl+"\n{")
    finish=s.index("\n\n\nint constant_rate_eros (",start)
    part=s[start:finish]
    part=once(part,
      '\tPRINT_DEBUG("Calculating discharge");',
      '\tPRINT_DEBUG("Calculating discharge");\n'
      "\t/* Reset counters before each discharge pass; no model state touched. */\n"
      "\ttisc_03i_active=1;\n"
      "\ttisc_03i_substep++;\n"
      "\ttisc_03i_lake_input_calls=tisc_03i_lake_input_nodes=tisc_03i_lake_input_outlets=0;\n"
      "\ttisc_03i_attempt_calls=tisc_03i_lake_nodes=tisc_03i_outlet_nodes=0;\n"
      "\ttisc_03i_max_lake_size=0;\n"
      "\ttisc_03i_precheck_s=tisc_03i_outlet_rain_s=tisc_03i_outlet_evap_s=0;\n"
      "\ttisc_03i_permeability_s=tisc_03i_attempt_s=tisc_03i_lake_input_s=0;\n"
      "\ttisc_03i_salt_deposit_s=tisc_03i_lake_volume_s=tisc_03i_checks_s=0;\n"
      "\ttisc_03i_clock_start=tisc_lab_wall_seconds();\n"
      '\ttisc_03i_report("BEGIN","calculate_discharge",0);',
      "function_entry")
    part=once(part,
      "\tfor (int isort=0; isort < Nx*Ny; isort++) {",
      "\tfor (int isort=0; isort < Nx*Ny; isort++) {\n"
      '\t\t\tif ((isort % 4096)==0 && isort>0) tisc_03i_report("PROGRESS","node_scan",isort);\n'
      "\t\t\tdouble tisc_03i_t0=0;\n",
      "node_scan_checkpoints")
    part=once(part,
      "\t\t\til   = drainage[row][col].lake;",
      "\t\t\til   = drainage[row][col].lake;\n"
      "\t\t\tif (il) {\n"
      "\t\t\t\ttisc_03i_lake_nodes++;\n"
      "\t\t\t\tif ((unsigned long long)Lake[il].n>tisc_03i_max_lake_size)\n"
      "\t\t\t\t\ttisc_03i_max_lake_size=(unsigned long long)Lake[il].n;\n"
      "\t\t\t}\n"
      "\t\t\ttisc_03i_t0=tisc_lab_wall_seconds();",
      "first-node-precheck-start")
    part=once(part,
      "\t\t\t\t\tAttempt_Delete_Node_From_Lake (cfg, ctx, row,col);",
      "\t\t\t\t\ttisc_03i_attempt_calls++;\n"
      "\t\t\t\t\t{\n"
      "\t\t\t\t\t\tdouble tisc_03i_attempt_start=tisc_lab_wall_seconds();\n"
      "\t\t\t\t\t\tAttempt_Delete_Node_From_Lake (cfg, ctx, row,col);\n"
      "\t\t\t\t\t\ttisc_03i_attempt_s+=tisc_lab_wall_seconds()-tisc_03i_attempt_start;\n"
      "\t\t\t\t\t}",
      "attempt_delete_call")
    part=once(part,
      "\t\t\t/*Calculate the distance to the output node*/",
      "\t\t\ttisc_03i_precheck_s+=tisc_lab_wall_seconds()-tisc_03i_t0;\n"
      "\t\t\t/*Calculate the distance to the output node*/",
      "first-node-precheck-end")
    part=once(part,
      "\t\t\tif (drainage[row][col].type == 'E') {\n"
      "\t\t\t\t/*Put into this outlet the rain from lake nodes draining here.*/",
      "\t\t\ttisc_03i_t0=tisc_lab_wall_seconds();\n"
      "\t\t\tif (drainage[row][col].type == 'E') {\n"
      "\t\t\t\ttisc_03i_outlet_nodes++;\n"
      "\t\t\t\t/*Put into this outlet the rain from lake nodes draining here.*/",
      "outlet_rain_start")
    part=once(part,
      "\t\t\t/* Add ions from local rain */",
      "\t\t\ttisc_03i_outlet_rain_s+=tisc_lab_wall_seconds()-tisc_03i_t0;\n"
      "\t\t\t/* Add ions from local rain */",
      "outlet_rain_end")
    part=once(part,
      "\t\t\t//If this node remained as lake exit after Attempt_Delete_Node, remove evaporated lake water from this outlet",
      "\t\t\ttisc_03i_t0=tisc_lab_wall_seconds();\n"
      "\t\t\t//If this node remained as lake exit after Attempt_Delete_Node, remove evaporated lake water from this outlet",
      "outlet_evap_start")
    part=once(part,
      "\t\t\t/*Underground seepage of part of the water to lower nodes*/",
      "\t\t\ttisc_03i_outlet_evap_s+=tisc_lab_wall_seconds()-tisc_03i_t0;\n"
      "\t\t\ttisc_03i_t0=tisc_lab_wall_seconds();\n"
      "\t\t\t/*Underground seepage of part of the water to lower nodes*/",
      "outlet_evap_end_permeability_start")
    part=once(part,
      "\t\t\t/*Transfers water and salt.*/",
      "\t\t\ttisc_03i_permeability_s+=tisc_lab_wall_seconds()-tisc_03i_t0;\n"
      "\t\t\t/*Transfers water and salt.*/",
      "permeability_end")
    part=once(part,
      "\t/* Distribute salt deposition */",
      '\ttisc_03i_report("END","node_scan",Nx*Ny);\n'
      "\tdouble tisc_03i_post_start=tisc_lab_wall_seconds();\n"
      "\t/* Distribute salt deposition */",
      "post_salt_start")
    part=once(part,
      "\t/*Calculate lake elevation and volume*/",
      "\ttisc_03i_salt_deposit_s=tisc_lab_wall_seconds()-tisc_03i_post_start;\n"
      '\ttisc_03i_report("END","salt_deposition",Nx*Ny);\n'
      "\ttisc_03i_post_start=tisc_lab_wall_seconds();\n"
      "\t/*Calculate lake elevation and volume*/",
      "post_salt_end_volume_start")
    part=once(part,
      "\t/*CHECKS:*/",
      "\ttisc_03i_lake_volume_s=tisc_lab_wall_seconds()-tisc_03i_post_start;\n"
      '\ttisc_03i_report("END","lake_volume",Nx*Ny);\n'
      "\ttisc_03i_post_start=tisc_lab_wall_seconds();\n"
      "\t/*CHECKS:*/",
      "volume_end_checks_start")
    # Last return in this function is its unconditional exit.
    last=part.rfind("\treturn (1);")
    if last<0 or part.count("\treturn (1);")!=1:
        raise RuntimeError("Unexpected discharge return statements")
    part=part[:last]+(
      "\ttisc_03i_checks_s=tisc_lab_wall_seconds()-tisc_03i_post_start;\n"
      '\ttisc_03i_report("END","checks_and_total",Nx*Ny);\n'
      "\ttisc_03i_active=0;\n")+part[last:]
    return s[:start]+part+s[finish:]

def main(src:Path,out:Path):
    original=src.read_bytes()
    s=original.decode("utf-8")
    if "tisc_lab_wall_seconds" not in s or "tisc_fast_merge_target" not in s:
        raise RuntimeError("Requires pinned 03g optimization + 03d stage timing applied first")
    if "TISC_DISCHARGE event=" in s: raise RuntimeError("03i already applied")
    s=once(s,"/* End TISC-LAB 03d timing. */",
           "/* End TISC-LAB 03d timing. */\n"+HELPERS,
           "03i-helper-injection")
    s=patch_lake_input(s)
    s=patch_discharge(s)
    result=s.encode("utf-8")
    src.write_bytes(result)
    out.mkdir(parents=True,exist_ok=True)
    (out/"03I_DISCHARGE_PROFILE_AUDIT.json").write_text(json.dumps({
      "experiment":"03i Calculate_Discharge nested trace",
      "upstream_sha":"d18b7d270f4d671b80223e10dede329ad35cafdd",
      "previous_instrumented_source_sha256":hashlib.sha256(original).hexdigest(),
      "03i_instrumented_source_sha256":hashlib.sha256(result).hexdigest(),
      "previous_validated_speedup":"03g merge-only stamp check (unchanged)",
      "no_physical_settings_or_equations_changed":True,
      "includes_source_diff":True,
      "cumulative_discharge_functions":["Lake_Input_Discharge","Attempt_Delete_Node_From_Lake"],
      "stages":["evap_lake_precheck","outlet_rain","outlet_evap","permeability",
                "salt_deposition","lake_volume","checks"],
      "overlapping_timer_note":"lake_input_s and attempt_delete_s are subsets of precheck/outlet timing; do not sum them."
    },indent=2))
    (out/"03I_DISCHARGE_INSTRUMENTATION.diff").write_text("".join(
      difflib.unified_diff(original.decode("utf-8").splitlines(True),
                           s.splitlines(True),
                           fromfile="03h-optimized-profile/surf_proc.c",
                           tofile="03i-discharge-profile/surf_proc.c")))
    print("03i source tracing successfully applied; scientific equations not changed.")

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("profile_tisc_discharge.py SOURCE_C AUDIT_DIR")
    main(Path(sys.argv[1]),Path(sys.argv[2]))
