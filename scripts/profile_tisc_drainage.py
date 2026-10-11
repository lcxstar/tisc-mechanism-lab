#!/usr/bin/env python3
"""Further timing inside the verified 03d hotspot Define_Drainage_Net.

Apply after profile_tisc_surface.py on the pinned temporary upstream checkout.
This is profiling only: no changes to control flow, parameters, or physics.
"""
from pathlib import Path
import hashlib
import json
import sys
import difflib

def replace1(s, old, new, label):
    n=s.count(old)
    if n!=1:
        raise RuntimeError(f"{label}: expected 1 exact upstream anchor; found {n}")
    return s.replace(old,new,1)

def phase_start(stage):
    return (
        "\ttisc_lab_drainage_phase_start = tisc_lab_wall_seconds();\n"
        f'\ttisc_lab_profile("BEGIN", "{stage}", -1, cfg->Nx * cfg->Ny, 0.0);\n'
    )

def phase_end(stage):
    return (
        f'\ttisc_lab_profile("END", "{stage}", -1, cfg->Nx * cfg->Ny, '
        "tisc_lab_wall_seconds()-tisc_lab_drainage_phase_start);\n"
    )

def main(src:Path, out:Path):
    original=src.read_bytes()
    s=original.decode("utf-8")
    if "TISC_PROFILE" not in s or "tisc_lab_wall_seconds" not in s:
        raise RuntimeError("First apply profile_tisc_surface.py")
    out.mkdir(parents=True,exist_ok=True)
    s=replace1(s,
        '\tPRINT_DEBUG("Defining drainage network");',
        '\tPRINT_DEBUG("Defining drainage network");\n'
        '\tdouble tisc_lab_drainage_phase_start = 0.0;\n',
        "drainage_function_entry")
    s=replace1(s,
        "\t/*Delete all lakes*/",
        phase_start("drainage_lake_reset")+"\t/*Delete all lakes*/",
        "lake_reset_begin")
    s=replace1(s,
        "\t/*Define lakes ascending in the topo grid (bottom-up).*/",
        phase_end("drainage_lake_reset")+
        phase_start("drainage_node_scan")+
        "\t/*Define lakes ascending in the topo grid (bottom-up).*/",
        "node_scan_begin")
    s=replace1(s,
        "\tfor (int isort=cfg->Nx*cfg->Ny-1; isort>=0; isort--) {\n\t\tint i, j;",
        "\tfor (int isort=cfg->Nx*cfg->Ny-1; isort>=0; isort--) {\n"
        "\t\tint i, j;\n"
        "\t\tif ((isort % 4096) == 0)\n"
        '\t\t\ttisc_lab_profile("PROGRESS", "drainage_node_scan", -1, '
        'cfg->Nx*cfg->Ny-1-isort, tisc_lab_wall_seconds()-tisc_lab_drainage_phase_start);',
        "node_scan_progress")
    s=replace1(s,
        "\t/*\n\t  Delete all lakes which nodes are all of them outlets.",
        phase_end("drainage_node_scan")+
        phase_start("drainage_lake_finalize")+
        "\t/*\n\t  Delete all lakes which nodes are all of them outlets.",
        "lake_finalize_begin")
    s=replace1(s,
        "\t/*For the same altitude, topologically sort upstream nodes first, and put saddles last in sortcell*/",
        phase_end("drainage_lake_finalize")+
        phase_start("drainage_internal_flat_sort")+
        "\t/*For the same altitude, topologically sort upstream nodes first, and put saddles last in sortcell*/",
        "internal_flat_sort_begin")
    s=replace1(s,
        "\t\tif (k_end > isort) {\n\t\t\tint max_swaps",
        "\t\tif (k_end > isort) {\n"
        "\t\t\tif (k_end-isort+1 >= 1024)\n"
        '\t\t\t\ttisc_lab_profile("PROGRESS", "drainage_internal_large_flat_group", -1, '
        'k_end-isort+1, tisc_lab_wall_seconds()-tisc_lab_drainage_phase_start);\n'
        "\t\t\tint max_swaps",
        "internal_large_group_start")
    s=replace1(s,
        "\t/*CHECK RESULTS*/",
        phase_end("drainage_internal_flat_sort")+
        phase_start("drainage_checks")+
        "\t/*CHECK RESULTS*/",
        "drainage_checks_begin")
    modified=s.encode("utf-8")
    src.write_bytes(modified)
    (out/"DRAINAGE_PROFILE_AUDIT.json").write_text(json.dumps({
        "experiment":"03e nested drainage timing",
        "source_relative_path":str(src),
        "prior_03d_instrumented_sha256":hashlib.sha256(original).hexdigest(),
        "with_nested_instrumentation_sha256":hashlib.sha256(modified).hexdigest(),
        "no_physical_parameters_or_equations_changed":True,
        "exact_anchors_checked":7,
        "note":"A C tracing build is not an unmodified executable"
    },indent=2))
    (out/"DRAINAGE_INSTRUMENTATION.diff").write_text("".join(difflib.unified_diff(
        original.decode("utf-8").splitlines(True),s.splitlines(True),
        fromfile="profile03d/surf_proc.c",tofile="profile03e/surf_proc.c")))
    print("03e drainage internal instrumentation active; source diff and SHA256 preserved")

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("profile_tisc_drainage.py SOURCE_C AUDIT_DIR")
    main(Path(sys.argv[1]),Path(sys.argv[2]))
