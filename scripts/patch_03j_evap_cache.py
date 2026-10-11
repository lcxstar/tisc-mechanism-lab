#!/usr/bin/env python3
"""03j-A: exact per-lake evaporation summation memoization.

Only temporary pinned TISC checkout is modified. Apply AFTER 03g.
Within a Calculate_Discharge call precipitation/evaporation arrays do not
change; lake membership may change only through Attempt_Delete_Node_From_Lake,
so *all* cache records are invalidated immediately after that call.

Cache uses original float summation and multiplication in the original
order. Any allocation failure falls back to the exact unmodified sum.
"""
import difflib
import hashlib
import json
import sys
from pathlib import Path

DECL="int Calculate_Discharge (struct GRIDNODE *sortcell, ModelConfig *cfg, ModelContext *ctx, float *total_lost_water, float *total_evap_water, float *total_underground_water)"
HELPER=r'''
/* TISC-LAB 03j-A. Only caches lake evaporation, no water-routing changes. */
static unsigned long long tisc_03ja_cache_hits=0, tisc_03ja_cache_misses=0;
static unsigned long long tisc_03ja_cache_invalidations=0;
static float tisc_03ja_lake_evap(int il, float *cache, unsigned int *stamps, unsigned int gen, size_t cap) {
    if (cache && stamps && il>0 && (size_t)il<cap && stamps[il]==gen) {
        tisc_03ja_cache_hits++;
        return cache[il];
    }
    tisc_03ja_cache_misses++;
    float lake_evap=0;
    for (int i=0; i<Lake[il].n;i++) lake_evap += evaporation[Lake[il].row[i]][Lake[il].col[i]];
    lake_evap *= dx*dy;
    if (cache && stamps && il>0 && (size_t)il<cap) {
        cache[il]=lake_evap;
        stamps[il]=gen;
    }
    return lake_evap;
}
/* End 03j-A cache helper. */
'''

def once(s,old,new,label):
    n=s.count(old)
    if n!=1: raise RuntimeError(f"03j-A {label}: expected 1 source anchor, got {n}")
    return s.replace(old,new,1)

def main(path:Path,out:Path):
    b=path.read_bytes();s=b.decode("utf8")
    if "tisc_fast_merge_target" not in s: raise RuntimeError("Must run 03g patch first")
    if "tisc_03ja_lake_evap" in s: raise RuntimeError("03j-A already injected")
    prefix=DECL+"\n{"
    if s.count(prefix)!=1:raise RuntimeError("Missing unique Calculate_Discharge definition")
    s=once(s,prefix,HELPER+"\n"+prefix,"helper")
    start=s.index(prefix);end=s.index("\n\n\nint constant_rate_eros (",start)
    f=s[start:end]
    f=once(f,
      '\tPRINT_DEBUG("Calculating discharge");',
      '\tPRINT_DEBUG("Calculating discharge");\n'
      "\t/* One independent cache lifecycle for each hydrological substep. */\n"
      "\tsize_t tisc_03ja_cap=(size_t)cfg->Nx*(size_t)cfg->Ny+1;\n"
      "\tfloat *tisc_03ja_cache=calloc(tisc_03ja_cap,sizeof(float));\n"
      "\tunsigned int *tisc_03ja_stamps=calloc(tisc_03ja_cap,sizeof(unsigned int));\n"
      "\tunsigned int tisc_03ja_gen=1;\n"
      "\ttisc_03ja_cache_hits=tisc_03ja_cache_misses=tisc_03ja_cache_invalidations=0;",
      "cache-setup")
    scan="\t\t\t\tfor (int i=0; i<Lake[il].n;i++) lake_evap += evaporation[Lake[il].row[i]][Lake[il].col[i]];\n\t\t\t\tlake_evap *= dx*dy;"
    if f.count(scan)!=1:raise RuntimeError("Expected 1 precheck evaporation sum, got "+str(f.count(scan)))
    f=f.replace(scan,
      "\t\t\t\tlake_evap=tisc_03ja_lake_evap(il, tisc_03ja_cache, tisc_03ja_stamps, tisc_03ja_gen, tisc_03ja_cap);",1)
    scan2="\t\t\t\tfor (int i=0; i<Lake[il].n; i++) lake_evap += evaporation[Lake[il].row[i]][Lake[il].col[i]];\n\t\t\t\tlake_evap *= dx*dy;"
    if f.count(scan2)!=1:raise RuntimeError("Expected 1 outlet evaporation sum, got "+str(f.count(scan2)))
    f=f.replace(scan2,
      "\t\t\t\tlake_evap=tisc_03ja_lake_evap(il, tisc_03ja_cache, tisc_03ja_stamps, tisc_03ja_gen, tisc_03ja_cap);",1)
    f=once(f,
      "\t\t\t\t\tAttempt_Delete_Node_From_Lake (cfg, ctx, row,col);",
      "\t\t\t\t\tAttempt_Delete_Node_From_Lake (cfg, ctx, row,col);\n"
      "\t\t\t\t\t/* The call may remove, split, renumber, or merge lakes. */\n"
      "\t\t\t\t\tif (++tisc_03ja_gen==0) {\n"
      "\t\t\t\t\t\tif (tisc_03ja_stamps) memset(tisc_03ja_stamps,0,tisc_03ja_cap*sizeof(unsigned int));\n"
      "\t\t\t\t\t\ttisc_03ja_gen=1;\n"
      "\t\t\t\t\t}\n"
      "\t\t\t\t\ttisc_03ja_cache_invalidations++;",
      "cache-invalidation")
    old="\treturn (1);"
    if f.count(old)!=1:raise RuntimeError("Unexpected exit sites")
    f=f.replace(old,
      "\tfprintf(stderr,\"\\nTISC_03J_A hits=%llu misses=%llu invalidations=%llu grid=%d\\n\",\n"
      "\t\ttisc_03ja_cache_hits,tisc_03ja_cache_misses,tisc_03ja_cache_invalidations,Nx*Ny);\n"
      "\tfflush(stderr);\n"
      "\tfree(tisc_03ja_cache);\n"
      "\tfree(tisc_03ja_stamps);\n"
      +old,1)
    s=s[:start]+f+s[end:]
    path.write_text(s)
    out.mkdir(parents=True,exist_ok=True)
    (out/"03J_A_AUDIT.json").write_text(json.dumps({
        "patch":"03j-A exact original-order per-lake evaporation memoization",
        "upstream":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd",
        "prior_03g_sha256":hashlib.sha256(b).hexdigest(),
        "03j_a_sha256":hashlib.sha256(s.encode()).hexdigest(),
        "source_diff_saved":True,
        "physical_parameters_changed":False,
        "hydrology_and_flow_source_unchanged":True,
        "cache_miss_summation":"same float loop and same multiply",
        "invalidation":"every Attempt_Delete_Node_From_Lake and 32-bit generation rollover",
        "allocation_failure":"recompute exact original sum"
    },indent=2))
    (out/"03J_A.diff").write_text("".join(difflib.unified_diff(
        b.decode().splitlines(True),s.splitlines(True),
        fromfile="03g/surf_proc.c",tofile="03j-A/surf_proc.c")))
    print("03j-A exact evaporation memoization applied and audited.")

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("patch_03j_evap_cache.py C_SOURCE AUDIT_DIRECTORY")
    main(Path(sys.argv[1]),Path(sys.argv[2]))
