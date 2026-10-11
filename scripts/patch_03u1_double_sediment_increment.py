#!/usr/bin/env python3
"""03u-1A controlled single-variable float->double physical experiment.

Only local temporary dh_sed in Sediment() is promoted from 32 to 64 bits.
Source-mass calculations, topo/Block storage and all TISC input/output types
remain float, including the sediment balance sidecar. This CAN change
scientific output; must compare numerical fields rather than demand equality.
"""
import difflib,hashlib,json,sys
from pathlib import Path
def main(path,audit):
    p=Path(path);audit=Path(audit);old=p.read_bytes();s=old.decode()
    if "TISC_03T_CORRECTED_BALANCE" not in s:raise RuntimeError("Compile accepted 03t baseline before physical precision change")
    i=s.index("int Sediment (ModelConfig *cfg")
    j=s.index("int Erode (ModelConfig *cfg",i)
    f=s[i:j]
    anchor="\tfloat dh_sed;"
    if f.count(anchor)!=1:raise RuntimeError("Missing unique Sediment() local float increment")
    f=f.replace(anchor,"\t/* 03u1 controlled higher precision of deposition thickness intermediate only. */\n\tdouble dh_sed;",1)
    s=s[:i]+f+s[j:]
    p.write_text(s);audit.mkdir(parents=True,exist_ok=True)
    (audit/"03U1_PRECISION_CHANGE.json").write_text(json.dumps({
       "upstream":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd",
       "physical_numerics_changed":True,
       "target":"only Sediment() local dh_sed float to double",
       "source_before_sha256":hashlib.sha256(old).hexdigest(),
       "source_after_sha256":hashlib.sha256(s.encode()).hexdigest(),
       "state_storage_unchanged":True,"model_parameters_unchanged":True,
       "model_binary_restart_ABI_unchanged":True,
       "not_a_full_double_state_model":True,
       "interpretation":"local arithmetic promotion, may alter numerical trajectory and routing even with float grid state"
    },indent=2))
    (audit/"03U1_INCREMENT_DOUBLE.diff").write_text("".join(difflib.unified_diff(
       old.decode().splitlines(True),s.splitlines(True),
       fromfile="03t/accepted/surf_proc.c",tofile="03u1/local-dh-sed-double/surf_proc.c")))
    print("03u1 isolated temporary dh_sed double promotion added")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("patch_03u1_double_sediment_increment.py C_SOURCE AUDIT_DIR")
    main(sys.argv[1],sys.argv[2])
