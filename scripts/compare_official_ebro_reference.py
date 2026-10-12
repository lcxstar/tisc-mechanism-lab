#!/usr/bin/env python3
"""Compare pinned Ebro demo 60–0Ma log to author's included 2016 Ebro screen.

The historical log is a useful reference, not proof of physical correctness
or bitwise reproducibility across source versions/compilers.
"""
from pathlib import Path
import argparse,csv,json,re,tarfile,math,statistics

def steps(text):
    pattern=re.compile(r"(?m)^\s*T=\s*([-+]?\d+(?:\.\d+)?)\s*My")
    found=list(pattern.finditer(text))
    out={}
    specs={
      "model_surface_max_m":r"topogr\.\s*:\s*max=\s*([-+0-9.eE]+)\s*m",
      "model_surface_min_m":r"topogr\.\s*:\s*max=\s*[-+0-9.eE]+\s*m\s*min=\s*([-+0-9.eE]+)\s*m",
      "profile_max_m":r"2D prof\.\s*:\s*max=\s*([-+0-9.eE]+)\s*m",
      "profile_min_m":r"2D prof\.\s*:\s*max=\s*[-+0-9.eE]+\s*m\s*min=\s*([-+0-9.eE]+)\s*m",
      "printed_sediment_volume_km3":r"sediment_vol:\s*([-+0-9.eE]+)\s*km3",
      "printed_lake_volume_km3":r"lake\s+\d+/\d+\s*:\s*([-+0-9.eE]+)\s*km3"
    }
    for i,m in enumerate(found):
        age=round(float(m.group(1)),5)
        block=text[m.end():found[i+1].start() if i+1<len(found) else len(text)]
        result={"time_Myr":age}
        for name,p in specs.items():
            obj=re.search(p,block)
            result[name]=float(obj.group(1)) if obj else None
        out[age]=result
    return out

def rms(v):
    return math.sqrt(sum(q*q for q in v)/len(v)) if v else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--historical-screen",type=Path,required=True)
    ap.add_argument("--archived-run",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    historical=steps(args.historical_screen.read_text(errors="replace"))
    with tarfile.open(args.archived_run,"r:gz") as tar:
        f=tar.extractfile("RUN.log")
        assert f is not None
        current=steps(f.read().decode("utf-8",errors="replace"))
    shared=sorted(set(historical)&set(current))
    assert len(historical)>50 and len(current)>50 and len(shared)>50, (
       "Insufficient original Ebro time snapshots for science comparison",
       len(historical),len(current),len(shared))
    fields=["model_surface_max_m","model_surface_min_m",
            "profile_max_m","profile_min_m",
            "printed_sediment_volume_km3"]
    rows=[]
    changes={k:[] for k in fields}
    for age in shared:
        row={"time_Myr":age}
        for field in fields:
            av=historical[age][field]
            bv=current[age][field]
            row["author_"+field]=av
            row["current_"+field]=bv
            row["difference_"+field]=bv-av if av is not None and bv is not None else None
            if row["difference_"+field] is not None:
                changes[field].append(row["difference_"+field])
        rows.append(row)
    with (args.out/"EBRO_AUTHOR_SCREEN_COMPARISON.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    stats={}
    for k,vals in changes.items():
        stats[k]={"matched":len(vals),"signed_bias":statistics.mean(vals) if vals else None,
                  "RMS_difference":rms(vals),"max_absolute_difference":max(map(abs,vals)) if vals else None}
    meta={"full_author_model":"8_Ebro_evol","author_reference":"Ebro_evol.screen supplied with danigeos/tisc pinned checkout",
      "author_reference_log_origin":"historical 2016 output not guaranteed same compiler version",
      "archived_current_model_source_variant":"audited_03t_optimized",
      "n_original_stages":len(historical),"n_current_stages":len(current),
      "n_exact_matching_log_ages":len(shared),"time_range_common_Myr":[shared[0],shared[-1]],
      "field_comparison":stats,
      "conclusion_scope":"Independent reference log comparison; numerical magnitudes do not validate geology; source was optimized and TISC version differs from original reference run."}
    (args.out/"EBRO_AUTHOR_SCREEN_COMPARISON_QC.json").write_text(json.dumps(meta,indent=2))
    lines=[
      "# Original author's Ebro Basin screen-output comparison",
      "",
      "This compares the author's bundled Ebro_evol.screen with the fully completed modern pinned-input execution. "
      "The 2016 reference log may have a different version/compiler and is an independent quantitative check, not a bitwise reference.",
      "",
      "Matched geological-age time records: "+str(len(shared))+
      " (reference "+str(len(historical))+", replicated "+str(len(current))+").",
      "",
      "| Field | Matched records | RMS difference | Maximum absolute difference |",
      "|---|---:|---:|---:|"]
    for k,v in stats.items():
        lines.append("| "+k+" | "+str(v["matched"])+" | "+
                     str(v["RMS_difference"])+" | "+str(v["max_absolute_difference"])+" |")
    lines.extend([
      "",
      "The full time-dependent differences are archived in EBRO_AUTHOR_SCREEN_COMPARISON.csv. "
      "These figures must be assessed before claiming close numerical reproduction of a specific 2003 published geological forecast.",
      "",
      "The author inputs were unchanged; the accelerated run includes explicitly audited non-pristine source modifications.",
    ])
    (args.out/"EBRO_AUTHOR_SCREEN_COMPARISON.md").write_text("\n".join(lines)+"\n")
    print("EBRO_AUTHOR_REF_QC",json.dumps(meta))
if __name__=="__main__":main()
