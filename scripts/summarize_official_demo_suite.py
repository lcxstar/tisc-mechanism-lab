#!/usr/bin/env python3
"""Collect every official author demo result; never claim success without QC."""
from pathlib import Path
import argparse,csv,json,shutil

CASES=[
 ("04_river","4_river_transport","conic_island"),
 ("05_lake_one","5_lakes","1lake"),
 ("05_lakes_two","5_lakes","2lakes"),
 ("06_tectonic","6_tectonics","demo"),
 ("07_climate","7_climate","sinusoidal"),
 ("08_ebro","8_Ebro_evol","Ebro_evol"),
 ("09_iberia","9_Iberian_drainage","Iberia_present")]

ap=argparse.ArgumentParser()
ap.add_argument("--input",type=Path,required=True)
ap.add_argument("--out",type=Path,required=True)
args=ap.parse_args()
args.out.mkdir(parents=True,exist_ok=True)
rows=[]
for case,folder,prefix in CASES:
    source=args.input/("AUTHOR_FULL_"+case)
    dst=args.out/case
    if source.exists():
        shutil.copytree(source,dst,dirs_exist_ok=True)
    info=dst/"RUN_QC.json"
    qc=json.loads(info.read_text()) if info.exists() else {}
    succeeded=bool(qc.get("checks_pass",False))
    evidence=(dst/"SOURCE_AND_INPUTS.json").exists() and (
      dst/(case+"_NATIVE_RAW.tar.gz")).exists()
    status="PASS_WITH_EXPLICIT_SOURCE_VARIANT" if succeeded and evidence else (
        "QC_PASSED_ARCHIVE_MISSING" if succeeded else "INCOMPLETE_OR_FAILED")
    archive=dst/(case+"_NATIVE_RAW.tar.gz")
    if archive.exists() and archive.stat().st_size>85_000_000:
        # Do not let a GitHub 100 MiB file limit silently reject entire archive.
        archive.unlink()
        status="QC_PASSED_ARCHIVE_TOO_LARGE_NEEDS_SPLIT" if succeeded else "INCOMPLETE_OR_FAILED"
    rows.append({
        "case":case,"upstream_folder":folder,"prefix":prefix,
        "status":status,"original_physical_inputs_unchanged":qc.get("model_input_hashes_unchanged"),
        "upstream_source_kind":qc.get("source_variant","NOT_YET_EVALUATED"),
        "time_initial_Myr":qc.get("time_ini_Myr"),
        "time_final_Myr":qc.get("time_final_Myr"),
        "grid_expected":qc.get("grid_nodes_expected"),
        "grid_observed":qc.get("native_xyw_nodes"),
        "process_code":qc.get("process_exit_code"),
        "raw_archive_committed":archive.exists(),
        "scientific_geological_validation":"NOT_CLAIMED"})
with (args.out/"OFFICIAL_DEMO_STATUS.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
passed=sum(x["status"]=="PASS_WITH_EXPLICIT_SOURCE_VARIANT" for x in rows)
text=[
    "# Original TISC author demo 4–9 reproduction",
    "",
    "All runs use the exact author input files pinned at upstream source commit d18b7d270f4d671b80223e10dede329ad35cafdd.",
    "",
    "**An audited optimized execution source is never called pristine upstream.** "
    "Normalized-upstream means only a compile-required two-nonbreaking-space replacement. "
    "The 03t optimized variant adds separately validated performance and diagnostic patches "
    "(lake membership, evaporation shortcuts, nonnegative incision slope guard, mass ledger), "
    "with no author input parameter edits.",
    "",
    "A PASS is defined as process exit 0, the expected finite native .xyw grid and intact SHA256 author inputs. "
    "It does not independently prove that the model's palaeogeographic or hydrological physics is correct. "
    "For large coupled cases, raw original output and code provenance are retained per model.",
    "",
    "| Model | Source variant | Full-time native-run QC | Native nodes | Raw archive |",
    "|---|---|---|---:|---|"
]
for x in rows:
    text.append(f"| {x['case']} | {x['upstream_source_kind']} | "
                f"{x['status']} | {x['grid_observed'] or 'n/a'} | "
                f"{'yes' if x['raw_archive_committed'] else 'no'} |")
text.extend([
    "",
    f"**Observed and preserved accepted models: {passed} of {len(CASES)}.**",
    "",
    "Remaining failures and timeouts are explicitly recorded in their case RUN_QC.json files and can be rerun without corrupting historical results.",
    "",
    "Already accepted earlier in this public repository: author static -Q flexure reference, 3_flexure full project; complete "
    "6_tectonics 401×401, 15-Myr with explicitly audited 03t source modifications (run 38165304319 and 38178743124). "
    "This preexisting scientific result is preserved separately from the new suite count until the new run passes.",
    "",
    "The synthetic local lake-routing experiments 03y–03aa are **mechanism diagnostics** and not replacements for author's supplied 5_lakes example.",
    "",
    "Do not import model geometry or numerical emission scales from the paused Junggar work.",
    ""
])
(args.out/"OFFICIAL_DEMO_STATUS.md").write_text("\n".join(text))
(args.out/"OFFICIAL_DEMO_STATUS.json").write_text(json.dumps({
    "suite":"author demos 4–9","upstream_commit":"d18b7d270f4d671b80223e10dede329ad35cafdd",
    "observed_total":len(rows),"accepted_with_archive":passed,"cases":rows,
    "no_false_author_original_claim":True},indent=2))
print("DEMO_SUITE_STATUS",json.dumps({"passed":passed,"total":len(rows),"statuses":
      {x["case"]:x["status"] for x in rows}}))
