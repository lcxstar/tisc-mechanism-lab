#!/usr/bin/env python3
"""Trace the pinned upstream TISC surface-process stages; no physics edits.

The upstream checkout is modified ONLY in the ephemeral CI workspace.
Apply after normalize_upstream_nbsp.py. Every source anchor is asserted unique.
This diagnostic build is NOT the byte-identical upstream executable.
"""
from pathlib import Path
import difflib
import hashlib
import json
import sys

HELPERS = r'''
/* TISC-LAB 03d timing ONLY. No numerical state is read or written. */
#include <sys/time.h>
static double tisc_lab_wall_seconds(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (double)tv.tv_sec + (double)tv.tv_usec * 1.0e-6;
}
static void tisc_lab_profile(const char *event, const char *stage,
                             int iter, int nodes, double elapsed_s) {
    fprintf(stderr, "\nTISC_PROFILE event=%s stage=%s iter=%d nodes=%d elapsed_s=%.6f\n",
            event, stage, iter, nodes, elapsed_s);
    fflush(stderr);
}
/* End TISC-LAB 03d timing. */
'''

def unique_replace(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Unsafe upstream change: {label}, expected 1 anchor, found {count}")
    return source.replace(old, new, 1)

def wrap_call(source: str, statement: str, stage: str) -> str:
    old = "\t\t" + statement + "\n"
    new = (
        "\t\t{\n"
        "\t\t\tdouble tisc_lab_start = tisc_lab_wall_seconds();\n"
        f'\t\t\ttisc_lab_profile("BEGIN", "{stage}", iter, cfg->Nx * cfg->Ny, 0.0);\n'
        "\t\t\t" + statement + "\n"
        f'\t\t\ttisc_lab_profile("END", "{stage}", iter, cfg->Nx * cfg->Ny, tisc_lab_wall_seconds()-tisc_lab_start);\n'
        "\t\t}\n"
    )
    return unique_replace(source, old, new, stage)

def main(source_path: Path, audit_dir: Path) -> None:
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    if "\u00a0" in source:
        raise RuntimeError("First run normalize_upstream_nbsp.py")
    if "TISC_PROFILE" in source:
        raise RuntimeError("Refusing duplicate instrumentation")
    audit_dir.mkdir(parents=True, exist_ok=True)
    source = unique_replace(
        source, "int Surface_Transport (ModelConfig *cfg",
        HELPERS + "\nint Surface_Transport (ModelConfig *cfg", "helper_injection"
    )
    source = unique_replace(
        source, "\tif (!cfg->hydro_model) return(0);",
        '\ttisc_lab_profile("BEGIN", "surface_transport", -1, cfg->Nx * cfg->Ny, 0.0);\n'
        "\tif (!cfg->hydro_model) return(0);", "surface_entry"
    )
    calls = [
        ("ReSort_Matrix (ctx->topo, sortcell, cfg->Nx, cfg->Ny);", "topography_sort"),
        ("Define_Drainage_Net(sortcell, cfg, ctx);", "drainage_network"),
        ("Calculate_Precipitation_Evaporation(cfg, ctx);", "precipitation_evaporation"),
        ("Ice_Flow(cfg, ctx, ice_velx_sl, ice_vely_sl, ice_velx_df, ice_vely_df, dt_st, &total_ice_melt, &total_ice_precip, &total_lost_water, &total_evap_water);", "ice_flow"),
        ("read_file_node_defs(cfg, ctx, dt_st);", "external_node_defs"),
        ("Calculate_Discharge(sortcell, cfg, ctx, &total_lost_water, &total_evap_water, &total_underground_water);", "calculate_discharge"),
        ("Fluvial_Transport(sortcell, cfg, ctx, dt_st, &total_lost_sed_mass, lake_instant_fill);", "fluvial_transport"),
        ("Ice_EroSed(cfg, ctx, ice_velx_sl, ice_vely_sl, dt_st, &total_ice_eros, &total_ice_sedim);", "ice_erosion"),
    ]
    for statement, stage in calls:
        source = wrap_call(source, statement, stage)

    source = unique_replace(
        source,
        "\t\t/* Re-sort topologically because lake shrinkage in Calculate_Discharge may have created new river nodes on flat areas */\n"
        "\t\tfor (int isort=0; isort<cfg->Nx*cfg->Ny-1; isort++) {",
        "\t\t/* Re-sort topologically because lake shrinkage in Calculate_Discharge may have created new river nodes on flat areas */\n"
        "\t\t{\n"
        "\t\t\tdouble tisc_lab_start = tisc_lab_wall_seconds();\n"
        '\t\t\ttisc_lab_profile("BEGIN", "equal_height_reorder", iter, cfg->Nx * cfg->Ny, 0.0);\n'
        "\t\tfor (int isort=0; isort<cfg->Nx*cfg->Ny-1; isort++) {",
        "equal_height_start"
    )
    source = unique_replace(
        source,
        "\t\t}\n\n\t\t{\n\t\t\tdouble tisc_lab_start = tisc_lab_wall_seconds();\n"
        '\t\t\ttisc_lab_profile("BEGIN", "fluvial_transport"',
        "\t\t}\n"
        '\t\t\ttisc_lab_profile("END", "equal_height_reorder", iter, cfg->Nx * cfg->Ny, tisc_lab_wall_seconds()-tisc_lab_start);\n'
        "\t\t}\n\n\t\t{\n\t\t\tdouble tisc_lab_start = tisc_lab_wall_seconds();\n"
        '\t\t\ttisc_lab_profile("BEGIN", "fluvial_transport"',
        "equal_height_end"
    )
    # For a large flat-area group, distinguish the dependency scan from
    # outlet-node partitioning. No rearrangement or stopping logic changes.
    source = unique_replace(
        source,
        "\t\t\tif (k_end > isort) {\n\t\t\t\tint max_swaps",
        "\t\t\tif (k_end > isort) {\n"
        "\t\t\t\tint tisc_lab_group_nodes = k_end-isort+1;\n"
        "\t\t\t\tdouble tisc_lab_group_start = tisc_lab_wall_seconds();\n"
        "\t\t\t\tif (tisc_lab_group_nodes >= 1024) {\n"
        '\t\t\t\t\ttisc_lab_profile("BEGIN", "large_equal_group", iter, tisc_lab_group_nodes, 0.0);\n'
        '\t\t\t\t\ttisc_lab_profile("BEGIN", "equal_group_dependency_scan", iter, tisc_lab_group_nodes, 0.0);\n'
        "\t\t\t\t}\n"
        "\t\t\t\tint max_swaps",
        "large_equal_group_start"
    )
    source = unique_replace(
        source,
        "\t\t\t\tint insert_pos = k_end;",
        "\t\t\t\tif (tisc_lab_group_nodes >= 1024) {\n"
        '\t\t\t\t\ttisc_lab_profile("END", "equal_group_dependency_scan", iter, tisc_lab_group_nodes, tisc_lab_wall_seconds()-tisc_lab_group_start);\n'
        '\t\t\t\t\ttisc_lab_profile("BEGIN", "equal_group_outlet_partition", iter, tisc_lab_group_nodes, 0.0);\n'
        "\t\t\t\t}\n"
        "\t\t\t\tint insert_pos = k_end;",
        "large_group_partition_start"
    )
    source = unique_replace(
        source,
        "\t\t\t\tisort = k_end;",
        "\t\t\t\tif (tisc_lab_group_nodes >= 1024) {\n"
        '\t\t\t\t\ttisc_lab_profile("END", "equal_group_outlet_partition", iter, tisc_lab_group_nodes, tisc_lab_wall_seconds()-tisc_lab_group_start);\n'
        '\t\t\t\t\ttisc_lab_profile("END", "large_equal_group", iter, tisc_lab_group_nodes, tisc_lab_wall_seconds()-tisc_lab_group_start);\n'
        "\t\t\t\t}\n"
        "\t\t\t\tisort = k_end;",
        "large_group_partition_end"
    )

    modified = source.encode("utf-8")
    source_path.write_bytes(modified)
    audit = {
        "label": "DIAGNOSTIC INSTRUMENTED BUILD, not byte-identical upstream",
        "source": str(source_path),
        "normalized_upstream_sha256": hashlib.sha256(original).hexdigest(),
        "instrumented_sha256": hashlib.sha256(modified).hexdigest(),
        "physical_parameters_changed": False,
        "physics_equations_intentionally_changed": False,
        "source_changed_for_timing": True,
        "anchor_checks": "all exact unique",
        "stages": [stage for _, stage in calls] + [
            "equal_height_reorder", "large_equal_group",
            "equal_group_dependency_scan", "equal_group_outlet_partition"
        ],
    }
    (audit_dir / "SOURCE_PROFILE_AUDIT.json").write_text(json.dumps(audit, indent=2))
    diff = difflib.unified_diff(
        original.decode("utf-8").splitlines(True), source.splitlines(True),
        fromfile="normalized-upstream/surf_proc.c",
        tofile="diagnostic-profile/surf_proc.c"
    )
    (audit_dir / "SURFACE_INSTRUMENTATION.diff").write_text("".join(diff))
    print(json.dumps(audit, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("profile_tisc_surface.py SOURCE_C AUDIT_DIR")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
