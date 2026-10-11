#!/usr/bin/env python3
"""03s pure observability: independent 64-bit sediment source/sink/export ledger.

Author model totals are floats, so many small lake deposits are lost to
float32 rounding when totals are ~1e14-1e16 kg. This sidecar increments
double counters with *the same original source expressions*, while keeping
all original float counters, routing and physical fields untouched.
"""
import json,difflib,hashlib,sys
from pathlib import Path
def once(s,o,n,label):
 c=s.count(o)
 if c!=1:raise ValueError(f"{label} expected 1 exact anchor; got {c}")
 return s.replace(o,n,1)
HELPER=r'''
/* TISC-LAB 03s: independent double-precision observational mass ledger. */
static double tisc03s_bed_kg=0.0, tisc03s_sed_kg=0.0, tisc03s_export_kg=0.0;
static double tisc03s_sed_increment_erased_kg=0.0;
static unsigned long long tisc03s_sed_increment_erased_count=0;
static unsigned long long tisc03s_sediment_calls=0;
'''
def main(path,audit):
 p=Path(path);audit=Path(audit);b=p.read_bytes();s=b.decode("utf8")
 if "tisc_03ja_lake_evap" not in s or "TISC_03K_GUARD" not in s:raise ValueError("Requires source 03g,03j,03k")
 if "tisc03s_sed_kg" in s:raise ValueError("Already instrumented")
 s=once(s,"int Surface_Transport (ModelConfig *cfg",HELPER+"\nint Surface_Transport (ModelConfig *cfg","define sidecar")
 first=s.index("int Surface_Transport (ModelConfig *cfg");last=s.index("int Calculate_Discharge (struct GRIDNODE *sortcell",first)
 f=s[first:last]
 f=once(f,
     '\tPRINT_DEBUG("Calculating surface transport");',
     '\tPRINT_DEBUG("Calculating surface transport");\n'
     "\t/* Reset only independent observer values; author counters are untouched. */\n"
     "\ttisc03s_bed_kg=(double)ctx->total_bedrock_eros_mass;\n"
     "\ttisc03s_sed_kg=(double)ctx->total_sed_mass;\n"
     "\ttisc03s_export_kg=0.0;\n"
     "\ttisc03s_sed_increment_erased_kg=0.0;\n"
     "\ttisc03s_sed_increment_erased_count=0;\n"
     "\ttisc03s_sediment_calls=0;",
     "observer reset")
 marker='\tPRINT_SUMLINE("eros_nosd:'
 report=r'''
    {
        const double tisc03s_native_bed=(double)ctx->total_bedrock_eros_mass;
        const double tisc03s_native_sed=(double)ctx->total_sed_mass;
        const double tisc03s_native_out=(double)total_lost_sed_mass;
        const double tisc03s_native_gap=tisc03s_native_bed-tisc03s_native_sed-tisc03s_native_out;
        const double tisc03s_precise_gap=tisc03s_bed_kg-tisc03s_sed_kg-tisc03s_export_kg;
        fprintf(stderr,
          "\nTISC_03S_LEDGER timeMyr=%.6f "
          "float_bed_kg=%.17g float_sed_kg=%.17g float_out_kg=%.17g "
          "float_gap_kg=%.17g float_gap_pct=%.12g "
          "double_bed_kg=%.17g double_sed_kg=%.17g double_out_kg=%.17g "
          "double_gap_kg=%.17g double_gap_pct=%.12g "
          "sed_round_to_zero_count=%llu sed_round_to_zero_kg=%.17g sed_calls=%llu\n",
          (double)(ctx->Time/Matosec),
          tisc03s_native_bed,tisc03s_native_sed,tisc03s_native_out,
          tisc03s_native_gap,tisc03s_native_bed?tisc03s_native_gap/tisc03s_native_bed*100:0.0,
          tisc03s_bed_kg,tisc03s_sed_kg,tisc03s_export_kg,
          tisc03s_precise_gap,tisc03s_bed_kg?tisc03s_precise_gap/tisc03s_bed_kg*100:0.0,
          tisc03s_sed_increment_erased_count,tisc03s_sed_increment_erased_kg,tisc03s_sediment_calls);
        fflush(stderr);
    }
'''
 if f.count(marker)!=1:raise ValueError("Surface_Transport mass-summary marker not unique")
 f=f.replace(marker,report+marker,1)
 s=s[:first]+f+s[last:]
 # Mass export exactly at both source code sites.
 first=s.index("int Fluvial_Transport(struct GRIDNODE *sortcell");last=s.index("\n\nint Ice_Flow(ModelConfig",first)
 f=s[first:last]
 f=once(f,
   "\t\t\t\t\t*total_lost_sed_mass += drainage[drow][dcol].masstr * dt_st;",
   "\t\t\t\t\t*total_lost_sed_mass += drainage[drow][dcol].masstr * dt_st;\n"
   "\t\t\t\t\ttisc03s_export_kg += (double)drainage[drow][dcol].masstr * (double)dt_st;",
   "lake export")
 f=once(f,
   "\t\t\t\t*total_lost_sed_mass += transfer_mass * dt_st;",
   "\t\t\t\t*total_lost_sed_mass += transfer_mass * dt_st;\n"
   "\t\t\t\ttisc03s_export_kg += (double)transfer_mass * (double)dt_st;",
   "border export")
 s=s[:first]+f+s[last:]
 # Add exact original double mass to observer whenever Sediment() is invoked.
 first=s.index("int Sediment (ModelConfig *cfg");last=s.index("int Erode (ModelConfig *cfg",first)
 f=s[first:last]
 f=once(f,
   "\tctx->total_sed_mass += d_mass;",
   "\tfloat tisc03s_native_before=ctx->total_sed_mass;\n"
   "\tctx->total_sed_mass += d_mass;\n"
   "\ttisc03s_sed_kg += d_mass;\n"
   "\ttisc03s_sediment_calls++;\n"
   "\tif (d_mass!=0.0 && ctx->total_sed_mass==tisc03s_native_before) {\n"
   "\t\ttisc03s_sed_increment_erased_count++;\n"
   "\t\ttisc03s_sed_increment_erased_kg+=d_mass;\n"
   "\t}",
   "sediment source")
 s=s[:first]+f+s[last:]
 # Erosion removes prior deposited sediment or produces new bedrock sediment.
 first=s.index("int Erode (ModelConfig *cfg");last=s.index("int Damn_River_Node (",first)
 f=s[first:last]
 f=once(f,
   "\t\t\tctx->total_sed_mass -= THICK2SEDMASS(cfg, dh_eros_Block);",
   "\t\t\tctx->total_sed_mass -= THICK2SEDMASS(cfg, dh_eros_Block);\n"
   "\t\t\ttisc03s_sed_kg -= (double)THICK2SEDMASS(cfg, dh_eros_Block);",
   "sediment reerosion")
 f=once(f,
   "\t\t\tctx->total_bedrock_eros_mass += dh_eros_Block * Blocks[k].density * cfg->dx*cfg->dy;",
   "\t\t\tctx->total_bedrock_eros_mass += dh_eros_Block * Blocks[k].density * cfg->dx*cfg->dy;\n"
   "\t\t\ttisc03s_bed_kg += (double)dh_eros_Block * (double)Blocks[k].density * (double)cfg->dx * (double)cfg->dy;",
   "bedrock block erosion")
 f=once(f,
   "\t\tctx->total_bedrock_eros_mass +=  mass_per_m2 * cfg->dx*cfg->dy;",
   "\t\tctx->total_bedrock_eros_mass +=  mass_per_m2 * cfg->dx*cfg->dy;\n"
   "\t\ttisc03s_bed_kg += (double)mass_per_m2 * (double)cfg->dx * (double)cfg->dy;",
   "basement erosion")
 s=s[:first]+f+s[last:]
 p.write_text(s);audit.mkdir(parents=True,exist_ok=True)
 (audit/"03S_DOUBLE_LEDGER_AUDIT.json").write_text(json.dumps({
  "upstream_commit":"d18b7d270f4d671b80223e10dede329ad35cafdd",
  "before_sha256":hashlib.sha256(b).hexdigest(),"after_sha256":hashlib.sha256(s.encode()).hexdigest(),
  "changes_original_source_equations":False,"changes_original_float_counters":False,
  "double_ledger_types":"static double, reset each Surface_Transport call",
  "tracks_bedrock":"all Erode() bedrock + basement source code sites",
  "tracks_net_sediment":"every Sediment() and sedimentary Erode() source code site",
  "tracks_export":"both Fluvial_Transport boundary and lake export sites",
  "known_limits":"no proof of cell block thickness rounding, burial compaction or all reservoirs; test scientific fields separately"
 },indent=2))
 (audit/"03S_DOUBLE_LEDGER.diff").write_text("".join(difflib.unified_diff(b.decode().splitlines(True),s.splitlines(True),fromfile="03k-candidate/surf_proc.c",tofile="03s-observation/surf_proc.c")))
 print("03s independent double ledger inserted without changing physics")
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("profile_03s_double_ledger.py C_SOURCE AUDIT_DIR")
 main(sys.argv[1],sys.argv[2])
