#!/usr/bin/env python3
"""One narrowly scoped *non-physical* build portability fix for pinned TISC.

The official upstream surf_proc.c pinned at d18b7d2 contains two U+00A0
nonbreaking spaces in C boolean expressions. GCC errors with stray '\\302'.
Replace ONLY those spaces with ASCII space; assert exactly two occur and
that both surround '| |' boolean OR operators. Preserve exact hashes.
"""
import hashlib
import json
import sys
from pathlib import Path

def main(source:Path,report:Path):
    before=source.read_bytes()
    text=before.decode("utf-8")
    candidates=[i for i,c in enumerate(text) if c=="\u00a0"]
    if len(candidates)!=2:
        raise RuntimeError(f"Refusing unexpected upstream changes: expected exactly 2 NBSP, observed {len(candidates)}")
    contexts=[text[max(0,i-45):min(len(text),i+45)] for i in candidates]
    if not all("||\u00a0(" in line for line in contexts):
        raise RuntimeError(f"Unexpected NBSP expression contexts: {contexts}")
    after=text.replace("\u00a0"," ").encode("utf-8")
    source.write_bytes(after)
    report.parent.mkdir(parents=True,exist_ok=True)
    diag={
      "reason":"Two U+00A0 no-break spaces are invalid in C source",
      "file":str(source),
      "number_of_nbsp_whitespace_changes":len(candidates),
      "before_sha256":hashlib.sha256(before).hexdigest(),
      "after_sha256":hashlib.sha256(after).hexdigest(),
      "surrounding_source_text":contexts,
      "actual_change":"U+00A0 to ASCII SPACE; no changed operators, constants or algorithms",
    }
    report.write_text(json.dumps(diag,indent=2,ensure_ascii=False))
    print(json.dumps(diag,indent=2,ensure_ascii=False))
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("normalize_upstream_nbsp.py INPUT_C_FILE REPORT_JSON")
    main(Path(sys.argv[1]),Path(sys.argv[2]))
