#!/usr/bin/env python3
"""Read-only format extension: print exact recoverable float32 topo in .xyw.
No solver arrays, equations, drainage ordering, sediment dynamics are changed.
Used to inspect whether apparently equal 0.1m-level outlets differ at float ULP.
"""
import difflib,hashlib,json,sys
from pathlib import Path
if len(sys.argv)!=3:raise SystemExit("patch_03x_raw_float_xyw.py tiscio.c AUDIT_FOLDER")
p=Path(sys.argv[1]);a=Path(sys.argv[2]);old=p.read_text()
s0='%7.2f\\t%7.2f\\t%.2f\\t%.2f\\t%c\\t%.1f\\t%7.2f\\t%7.2f\\t%.1f\\t%7.1f'
s1='%7.2f\\t%7.2f\\t%.2f\\t%.2f\\t%c\\t%.9g\\t%7.2f\\t%7.2f\\t%.9g\\t%7.1f'
if old.count(s0)!=1:raise RuntimeError("Expected exactly one xyw record writer, found "+str(old.count(s0)))
new=old.replace(s0,s1,1)
p.write_text(new)
a.mkdir(parents=True,exist_ok=True)
(a/"03X_XYW_HIGH_PRECISION_FORMAT_AUDIT.json").write_text(json.dumps({
"physical_changes":False,"binary_struct_changes":False,"floating_state_changes":False,
"changed_output":".xyw topography and downstream topography only (9 significant digits)",
"tiscio_old_sha256":hashlib.sha256(old.encode()).hexdigest(),
"tiscio_new_sha256":hashlib.sha256(new.encode()).hexdigest(),
"interpretation":"exact roundtrip printed float32; not actual float64 physical state"},indent=2))
(a/"03X_IO_PRINT_DIFF.patch").write_text("".join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
fromfile="author/tiscio.c",tofile="03x/io-only/tiscio.c")))
print("03x high precision output-only probe patched")
