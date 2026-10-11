#!/usr/bin/env python3
"""Experiment 03f: aggregate lake-operation timing for pinned official TISC.

Apply AFTER the 03d + 03e profile scripts to a disposable upstream checkout.
All edits are instrument-only. The temporary executable is NOT the original
byte-for-byte upstream executable. Nothing in numerical equations or control
logic is intentionally modified.
"""
from pathlib import Path
import difflib
import hashlib
import json
import re
import sys

HELPERS = r'''
/* TISC-LAB 03f: summary counters, never print inside each lake call. */
static unsigned long long tisc_lab_add_calls=0, tisc_lab_add_duplicates=0;
static unsigned long long tisc_lab_new_calls=0, tisc_lab_merge_calls=0;
static unsigned long long tisc_lab_merged_node_copies=0;
static int tisc_lab_max_lake_nodes=0;
static double tisc_lab_add_total_s=0, tisc_lab_add_search_s=0, tisc_lab_add_realloc_s=0;
static double tisc_lab_new_total_s=0, tisc_lab_merge_total_s=0;
static void tisc_lab_lake_progress(int processed_nodes) {
    fprintf(stderr,
      "TISC_LAKE_STATS nodes=%d add_calls=%llu add_duplicates=%llu "
      "add_total_s=%.6f add_search_s=%.6f add_realloc_s=%.6f "
      "new_calls=%llu new_total_s=%.6f merge_calls=%llu "
      "merge_total_s=%.6f merged_node_copies=%llu max_lake_nodes=%d nlakes=%d\n",
      processed_nodes, tisc_lab_add_calls, tisc_lab_add_duplicates,
      tisc_lab_add_total_s, tisc_lab_add_search_s, tisc_lab_add_realloc_s,
      tisc_lab_new_calls, tisc_lab_new_total_s, tisc_lab_merge_calls,
      tisc_lab_merge_total_s, tisc_lab_merged_node_copies,
      tisc_lab_max_lake_nodes, nlakes);
    fflush(stderr);
}
/* End TISC-LAB 03f. */
'''

def change_once(s, old, new, label):
    n=s.count(old)
    if n != 1:
        raise RuntimeError(f"Anchor {label}: expected exactly one occurrence, got {n}")
    return s.replace(old,new,1)

def function_patch(source, name, modify):
    pat=rf'(?ms)^int {re.escape(name)} \([^\n]*\)\s*\{{.*?^\}}'
    matches=list(re.finditer(pat,source))
    if len(matches)!=1:
        raise RuntimeError(f"Unsafe function match {name}: {len(matches)}")
    m=matches[0]
    original=m.group(0)
    revised=modify(original)
    if revised==original: raise RuntimeError(f"No changes in {name}")
    return source[:m.start()]+revised+source[m.end():]

def add_node(s):
    s=change_once(s,'\tint i, il;',
        '\tint i, il;\n'
        '\tdouble tisc_lab_add_start=tisc_lab_wall_seconds();\n'
        '\tdouble tisc_lab_scan_start=0.0, tisc_lab_alloc_start=0.0;\n'
        '\ttisc_lab_add_calls++;\n', 'add_decl')
    s=change_once(s,'\til = fabs((float) i_lake);',
        '\til = fabs((float) i_lake);\n'
        '\tif (Lake[il].n > tisc_lab_max_lake_nodes) '
        'tisc_lab_max_lake_nodes = Lake[il].n;\n'
        '\ttisc_lab_scan_start=tisc_lab_wall_seconds();', 'add_start_scan')
    s=change_once(s,'\t\t\treturn(0);',
        '\t\t\ttisc_lab_add_search_s += tisc_lab_wall_seconds()-tisc_lab_scan_start;\n'
        '\t\t\ttisc_lab_add_duplicates++;\n'
        '\t\t\ttisc_lab_add_total_s += tisc_lab_wall_seconds()-tisc_lab_add_start;\n'
        '\t\t\treturn(0);','add_duplicate_exit')
    s=change_once(s,'\tLake[il].n++;',
        '\ttisc_lab_add_search_s += tisc_lab_wall_seconds()-tisc_lab_scan_start;\n'
        '\ttisc_lab_alloc_start=tisc_lab_wall_seconds();\n'
        '\tLake[il].n++;', 'add_alloc_begin')
    s=change_once(s,'\tLake[il].col = realloc(Lake[il].col, Lake[il].n*sizeof(int));',
        '\tLake[il].col = realloc(Lake[il].col, Lake[il].n*sizeof(int));\n'
        '\ttisc_lab_add_realloc_s += tisc_lab_wall_seconds()-tisc_lab_alloc_start;\n'
        '\tif (Lake[il].n > tisc_lab_max_lake_nodes) '
        'tisc_lab_max_lake_nodes = Lake[il].n;', 'add_alloc_end')
    s=change_once(s,'\treturn (1);',
        '\ttisc_lab_add_total_s += tisc_lab_wall_seconds()-tisc_lab_add_start;\n'
        '\treturn (1);','add_return')
    return s

def new_lake(s):
    s=change_once(s,'\tnlakes++;',
        '\tdouble tisc_lab_new_start=tisc_lab_wall_seconds();\n'
        '\ttisc_lab_new_calls++;\n'
        '\tnlakes++;','new_start')
    s=change_once(s,'\treturn (nlakes);',
        '\ttisc_lab_new_total_s += tisc_lab_wall_seconds()-tisc_lab_new_start;\n'
        '\treturn (nlakes);','new_end')
    return s

def unify_lakes(s):
    s=change_once(s,'\tint i, j, k, il, ild;',
        '\tint i, j, k, il, ild;\n'
        '\tdouble tisc_lab_merge_start=tisc_lab_wall_seconds();\n'
        '\ttisc_lab_merge_calls++;\n','merge_start')
    s=change_once(s,'\tild = fabs((float) i_lake_to_delete);',
        '\tild = fabs((float) i_lake_to_delete);\n'
        '\ttisc_lab_merged_node_copies += (unsigned long long)Lake[ild].n;', 'merge_size')
    s=change_once(s,'\treturn (1);',
        '\ttisc_lab_merge_total_s += tisc_lab_wall_seconds()-tisc_lab_merge_start;\n'
        '\treturn (1);', 'merge_exit')
    return s

def main(source_path:Path, audit_dir:Path):
    before=source_path.read_bytes()
    s=before.decode('utf-8')
    if 'tisc_lab_wall_seconds' not in s or 'drainage_node_scan' not in s:
        raise RuntimeError('Apply 03d + 03e instrumentation first')
    if 'TISC_LAKE_STATS' in s: raise RuntimeError('Already instrumented')
    s=change_once(s,'/* End TISC-LAB 03d timing. */',
        '/* End TISC-LAB 03d timing. */\n'+HELPERS,'helpers')
    s=function_patch(s,'Add_Node_To_Lake',add_node)
    s=function_patch(s,'New_Lake',new_lake)
    s=function_patch(s,'Unify_Lakes',unify_lakes)

    progress=(
      '\t\tif ((isort % 4096) == 0)\n'
      '\t\t\ttisc_lab_profile("PROGRESS", "drainage_node_scan", -1, '
      'cfg->Nx*cfg->Ny-1-isort, tisc_lab_wall_seconds()-tisc_lab_drainage_phase_start);'
    )
    progress_new=(
      '\t\tif ((isort % 4096) == 0) {\n'
      '\t\t\ttisc_lab_profile("PROGRESS", "drainage_node_scan", -1, '
      'cfg->Nx*cfg->Ny-1-isort, tisc_lab_wall_seconds()-tisc_lab_drainage_phase_start);\n'
      '\t\t\ttisc_lab_lake_progress(cfg->Nx*cfg->Ny-1-isort);\n'
      '\t\t}'
    )
    s=change_once(s,progress,progress_new,'periodic_lake_stats')
    # The first 0.5-Myr step may finish; preserve a final snapshot even
    # when the selected interval is not divisible by 4096.
    s=change_once(s,
      '\t/*\n\t  Delete all lakes which nodes are all of them outlets.',
      '\ttisc_lab_lake_progress(cfg->Nx*cfg->Ny);\n'
      '\t/*\n\t  Delete all lakes which nodes are all of them outlets.',
      'end_scan_snapshot')
    after=s.encode('utf-8')
    source_path.write_bytes(after)
    audit_dir.mkdir(parents=True,exist_ok=True)
    (audit_dir/'LAKE_OPERATION_PROFILE_AUDIT.json').write_text(json.dumps({
        'experiment':'03f',
        'source_modified_for_timing':True,
        'unchanged_geology_and_physics_intended':True,
        'source_prior_sha256':hashlib.sha256(before).hexdigest(),
        'source_instrumented_sha256':hashlib.sha256(after).hexdigest(),
        'profiled_calls':['Add_Node_To_Lake','New_Lake','Unify_Lakes'],
        'limits':'Unify_Lakes elapsed is inclusive of nested Add_Node_To_Lake; do NOT sum times.',
        'sampling':'cumulative totals on every 4096th drainage node, and at scan completion',
    },indent=2))
    (audit_dir/'LAKE_OPERATION_INSTRUMENTATION.diff').write_text(''.join(
        difflib.unified_diff(before.decode('utf-8').splitlines(True),
                             s.splitlines(True),
                             fromfile='03e/surf_proc.c',tofile='03f/surf_proc.c')))
    print('03f lake operations instrumented, SHA256 and diff recorded')

if __name__=='__main__':
    if len(sys.argv)!=3:
        raise SystemExit('profile_tisc_lake_ops.py SOURCE_C AUDIT_DIR')
    main(Path(sys.argv[1]),Path(sys.argv[2]))
