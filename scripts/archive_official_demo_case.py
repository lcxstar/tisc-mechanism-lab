#!/usr/bin/env python3
"""Archive unchanged pinned author input files and selected native run evidence."""
from pathlib import Path
import argparse,hashlib,json,tarfile

p=argparse.ArgumentParser()
p.add_argument("--case-dir",type=Path,required=True)
p.add_argument("--result-dir",type=Path,required=True)
p.add_argument("--case-name",required=True)
args=p.parse_args()
d=args.case_dir;out=args.result_dir;out.mkdir(parents=True,exist_ok=True)
manifest=json.loads((d/"ORIGINAL_INPUT_MANIFEST.json").read_text())
prefix=manifest["prefix"]
files=set(manifest["files_sha256"])
for name in ("RUN.log","EXIT_CODE.txt","WALL_SECONDS.txt",
             "ACTUAL_COMMAND.txt","ORIGINAL_INPUT_MANIFEST.json",
             "AUTHOR_COMMIT.txt","EXECUTION_SOURCE_SHA256.txt"):
    if (d/name).exists():files.add(name)
for ext in ("xyw","xyzt","hrz","lak","bas","st","PRFL","RIV"):
    file=d/(prefix+"."+ext)
    if file.exists():files.add(file.name)
# Never add restart blocks .all or unrelated, enormous plotting files.
tar=out/(args.case_name+"_NATIVE_RAW.tar.gz")
with tarfile.open(tar,"w:gz",compresslevel=5) as t:
    for fname in sorted(files):
        f=d/fname
        if f.is_file():t.add(f,arcname=fname,recursive=False)
h=hashlib.sha256(tar.read_bytes()).hexdigest()
(out/"RAW_ARCHIVE_SHA256.txt").write_text(h+"  "+tar.name+"\n")
(out/"ARCHIVE_CONTENTS.txt").write_text("\n".join(sorted(files))+"\n")
print("SAVED_ARCHIVE",args.case_name,tar.stat().st_size,"bytes",h)
