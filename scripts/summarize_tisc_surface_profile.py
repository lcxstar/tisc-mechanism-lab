#!/usr/bin/env python3
"""Parse completed and interrupted TISC surface profiling runs.

A timeout is not a numerical crash; a still-open BEGIN without END identifies
the active call when timeout stopped the model, not the ultimate root cause.
"""
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

PROFILE = re.compile(
    r"TISC_PROFILE event=(BEGIN|END) stage=([a-z_]+) "
    r"iter=(-?\d+) nodes=(\d+) elapsed_s=([0-9.]+)"
)
TIME = re.compile(r"\bT=\s*(\d+(?:\.\d+)?)\s*My")

def summarize(folder: Path) -> dict:
    raw_log = (folder / "RUN.log").read_text(errors="replace") if (folder / "RUN.log").exists() else ""
    exit_code = int((folder / "EXIT_CODE.txt").read_text().strip()) if (folder / "EXIT_CODE.txt").exists() else None
    events = []
    duration_by_stage = defaultdict(list)
    unfinished = {}
    for hit in PROFILE.finditer(raw_log):
        event, stage, substep, nodes, seconds = hit.groups()
        e = {"event": event, "stage": stage, "iter": int(substep),
             "nodes": int(nodes), "elapsed_s": float(seconds)}
        events.append(e)
        key = (stage, int(substep))
        if event == "BEGIN":
            unfinished[key] = len(events) - 1
        elif event == "END":
            unfinished.pop(key, None)
            if math.isfinite(e["elapsed_s"]):
                duration_by_stage[stage].append(e["elapsed_s"])
    # The special umbrella marker is intentionally BEGIN-only.
    open_calls = [
        events[position] for (stage, _), position in unfinished.items()
        if stage != "surface_transport"
    ]
    open_calls.sort(key=lambda e: next(
        (i for i in range(len(events)-1, -1, -1) if events[i] is e), -1))
    # Last still-open BEGIN is the deepest active stage (if present).
    active = open_calls[-1] if open_calls else None
    stages = sorted(
        ({"stage": s, "completed_calls": len(v), "total_s": round(sum(v), 6),
          "max_s": round(max(v), 6)} for s, v in duration_by_stage.items()),
        key=lambda x: x["total_s"], reverse=True
    )
    times = [float(t) for t in TIME.findall(raw_log)]
    sha_audit = folder / "INPUT_AUDIT.json"
    audit = json.loads(sha_audit.read_text()) if sha_audit.exists() else {}
    source_audit = folder / "SOURCE_PROFILE_AUDIT.json"
    src = json.loads(source_audit.read_text()) if source_audit.exists() else {}
    report = {
        "experiment": "TISC 03d first-step surface stage timing",
        "case": folder.name,
        "original_input_grid": audit.get("grid"),
        "original_401_inputs_hash_identical": (
            audit.get("grid") == 401 and
            audit.get("source_hashes") == audit.get("run_hashes")
        ),
        "instrumented_source": bool(src.get("source_changed_for_timing")),
        "source_is_byte_identical_to_upstream": False,
        "physics_overrides_for_diagnostic": audit.get("run_override_flags"),
        "process_exit": exit_code,
        "timed_out": exit_code == 124,
        "logged_model_times_Myr": times,
        "last_model_time_Myr": times[-1] if times else None,
        "profile_event_count": len(events),
        "stage_totals_completed_calls_only": stages,
        "active_stage_at_interrupt": active["stage"] if active else None,
        "active_substep_at_interrupt": active["iter"] if active else None,
        "open_nested_stages": [e["stage"] for e in open_calls],
        "last_ten_trace_events": events[-10:],
        "last_25_log_lines": raw_log.splitlines()[-25:],
        "diagnostic_trace_present": len(events) > 1,
        "sediment_mass_balance_validated": False,
        "interpretation_limit": (
            "Only completed stages have durations. If timed out, the deepest "
            "unfinished stage is a measured blocking location, not proof of "
            "which loop or algorithm caused the slowdown."
        )
    }
    (folder / "STAGE_PROFILE_QC.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps({k:v for k,v in report.items() if k != "last_25_log_lines"}, indent=2))
    return report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("summarize_tisc_surface_profile.py PROFILE_RUN_DIR")
    report = summarize(Path(sys.argv[1]))
    if not report["diagnostic_trace_present"]:
        raise SystemExit("No usable timing trace, inspect RUN.log before interpreting.")
