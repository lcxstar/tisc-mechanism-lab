#!/usr/bin/env python3
"""03g: accelerate ONLY duplicate membership checks during Unify_Lakes().

Pinned TISC source remains authoritative. This patch creates a separate,
explicitly optimized derivative in ephemeral CI checkout. Build the original
normalized source first and save its executable as reference.

Correctness: a generation-stamped coordinate membership table is populated
from the destination lake once per merge; new appended nodes are marked.
The Add_Node_To_Lake duplicate guard is RETAINED. All calls outside a merge
execute the original linear duplicate scan verbatim. No physics settings,
numerical calculations, lake-list ordering or merge sequence are changed.
"""
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

HELPERS = r"""
/* TISC LAB 03g isolated performance optimization; NOT original upstream. */
static unsigned int *tisc_fast_lake_marks = NULL;
static unsigned int tisc_fast_lake_generation = 0;
static int tisc_fast_merge_target = -1;
/* End 03g helper globals. */
"""

def once(s, old, new, label):
    count=s.count(old)
    if count!=1:
        raise RuntimeError(f"03g refusing ungrounded patch {label}: anchor count {count}")
    return s.replace(old,new,1)

def patch_function(s,name,cb):
    pattern=rf'(?ms)^int {re.escape(name)} \([^\n]*\)\s*\{{.*?^\}}'
    matches=list(re.finditer(pattern,s))
    if len(matches)!=1:
        raise RuntimeError(f"{name} definition count: {len(matches)}")
    m=matches[0]
    old=m.group(0)
    new=cb(old)
    return s[:m.start()]+new+s[m.end():]

def patch_add(s):
    anchor=(
        "\tfor (i=0; i<Lake[il].n; i++) \n"
        "\t\tif (row==Lake[il].row[i] && col==Lake[il].col[i]) {\n"
        "\t\t  \tPRINT_ERROR(\"[%d][%d] tried to repeat lake node.\", row, col);\n"
        "\t\t\treturn(0);\n"
        "\t\t}\n"
    )
    repl=(
        "\t/* 03g: constant-time exact duplicate check only for an active merge. */\n"
        "\tif (tisc_fast_merge_target == il) {\n"
        "\t\tconst size_t tisc_index = (size_t)row*(size_t)Nx+(size_t)col;\n"
        "\t\tif (tisc_fast_lake_marks[tisc_index] == tisc_fast_lake_generation) {\n"
        "\t\t\tPRINT_ERROR(\"[%d][%d] tried to repeat lake node.\", row, col);\n"
        "\t\t\treturn(0);\n"
        "\t\t}\n"
        "\t} else {\n"
        "\t\tfor (i=0; i<Lake[il].n; i++) \n"
        "\t\t\tif (row==Lake[il].row[i] && col==Lake[il].col[i]) {\n"
        "\t\t  \t\tPRINT_ERROR(\"[%d][%d] tried to repeat lake node.\", row, col);\n"
        "\t\t\t\treturn(0);\n"
        "\t\t\t}\n"
        "\t}\n"
    )
    s=once(s,anchor,repl,"Add_Node_To_Lake duplicate guard")
    s=once(s,
        "\tLake[il].col[Lake[il].n-1] = col;",
        "\tLake[il].col[Lake[il].n-1] = col;\n"
        "\tif (tisc_fast_merge_target == il)\n"
        "\t\ttisc_fast_lake_marks[(size_t)row*(size_t)Nx+(size_t)col] = tisc_fast_lake_generation;",
        "mark new node in target lake")
    return s

def patch_merge(s):
    markstart=(
        "\t/* 03g: stamp destination membership before append/merge. */\n"
        "\tif (tisc_fast_lake_marks == NULL) {\n"
        "\t\ttisc_fast_lake_marks = calloc((size_t)Nx*(size_t)Ny, sizeof(*tisc_fast_lake_marks));\n"
        "\t}\n"
        "\tif (tisc_fast_lake_marks != NULL) {\n"
        "\t\tif (tisc_fast_lake_generation == UINT_MAX) {\n"
        "\t\t\tmemset(tisc_fast_lake_marks, 0, (size_t)Nx*(size_t)Ny*sizeof(*tisc_fast_lake_marks));\n"
        "\t\t\ttisc_fast_lake_generation = 0;\n"
        "\t\t}\n"
        "\t\ttisc_fast_lake_generation++;\n"
        "\t\tfor (i=0; i<Lake[il].n; i++)\n"
        "\t\t\ttisc_fast_lake_marks[(size_t)Lake[il].row[i]*(size_t)Nx+\n"
        "\t\t\t\t(size_t)Lake[il].col[i]] = tisc_fast_lake_generation;\n"
        "\t\ttisc_fast_merge_target = il;\n"
        "\t} else {\n"
        "\t\t/* Allocation failure: fall back to original exact linear scan. */\n"
        "\t\ttisc_fast_merge_target = -1;\n"
        "\t}\n"
    )
    s=once(s,
        "\t/*Changes the associated drainage lake signal*/",
        markstart+"\n\t/*Changes the associated drainage lake signal*/",
        "set up merge stamp")
    s=once(s,
        "\tDeallocate_Lake(ild);",
        "\t/* Deallocation renumbers lake IDs: discard temporary merge target first. */\n"
        "\ttisc_fast_merge_target = -1;\n"
        "\tDeallocate_Lake(ild);",
        "clear merge stamp before deallocation")
    return s

def main(src:Path,audit_dir:Path):
    before=src.read_bytes()
    s=before.decode("utf-8")
    if "\u00a0" in s:
        raise RuntimeError("Normalize upstream source compile-only NBSP before patching")
    if "tisc_fast_merge_target" in s:
        raise RuntimeError("Already optimized")
    s=once(s,'#include "tisclib.h"',
        '#include "tisclib.h"\n#include <limits.h>\n#include <string.h>\n'+HELPERS,
        "safe performance helper definitions")
    s=patch_function(s,"Add_Node_To_Lake",patch_add)
    s=patch_function(s,"Unify_Lakes",patch_merge)
    result=s.encode("utf-8")
    src.write_bytes(result)
    audit_dir.mkdir(parents=True,exist_ok=True)
    (audit_dir/"PATCH_AUDIT.json").write_text(json.dumps({
        "patch":"03g merge-only lake membership guard with O(1) stamp lookup",
        "repository":"danigeos/tisc",
        "pinned_upstream":"d18b7d270f4d671b80223e10dede329ad35cafdd",
        "normalized_reference_sha256":hashlib.sha256(before).hexdigest(),
        "optimized_surf_proc_sha256":hashlib.sha256(result).hexdigest(),
        "equations_or_user_parameters_changed":False,
        "list_order_or_merge_order_changed":False,
        "fallback_duplicate_check_outside_merge":"original linear scan",
        "duplicate_detection_during_merge":"same semantics via target lake membership stamp",
        "malloc_failure":"fallback to original linear scan",
        "scientific_status":"performance experiment; must pass numerical equivalence checks",
    },indent=2))
    (audit_dir/"SURF_PROC_OPTIMIZATION.diff").write_text("".join(
        difflib.unified_diff(before.decode("utf-8").splitlines(True),
                             s.splitlines(True),
                             fromfile="normalized-author/surf_proc.c",
                             tofile="03g-performance-derivative/surf_proc.c")))
    print(json.dumps(json.loads((audit_dir/"PATCH_AUDIT.json").read_text()),indent=2))

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("patch_fast_lake_membership.py SOURCE_C AUDIT_DIR")
    main(Path(sys.argv[1]),Path(sys.argv[2]))
