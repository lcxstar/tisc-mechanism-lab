#!/usr/bin/env python3
"""03y SINGLE-MECHANISM physical test, not a production correction.

In Define_Drainage_Net, select the first downhill neighbor as before, but
replace a previously chosen downhill route only when the next candidate's
gradient is STEEPER by more than epsilon (dimensionless m/m).  Lake formation,
exact-zero-slope identification, outlets, minimum slope in lake-removal and all
other physics remain UNCHANGED.  epsilon=0 is strict baseline semantics.
"""
from pathlib import Path
import sys,json,difflib,hashlib
if len(sys.argv)!=4:raise SystemExit("patch_03y_routing_slope_tiebreak.py surf_proc.c AUDIT_DIR EPSILON")
path=Path(sys.argv[1]);out=Path(sys.argv[2]);eps=float(sys.argv[3])
if eps not in (0.0,1.e-8):raise SystemExit("Pre-registered epsilon = 0 or 1e-8 dimensionless")
raw=path.read_bytes();original=raw.decode("utf-8")
start=original.index("int Define_Drainage_Net (struct GRIDNODE *sortcell",original.index("int Surface_Transport ("))
end=original.index("int Diffusive_Eros (ModelConfig",start)
section=original[start:end]
anchors={
"if (deriv<0 && deriv<maxderneg_noundef) {imaxderneg_noundef=l; maxderneg_noundef=deriv;}":
"if (deriv<0 && (imaxderneg_noundef==SIGNAL || deriv < maxderneg_noundef - 1.0e-8f)) {imaxderneg_noundef=l; maxderneg_noundef=deriv;}",
"if (deriv<0 && deriv<maxderneg) {imaxderneg=l; maxderneg=deriv;}":
"if (deriv<0 && (imaxderneg==SIGNAL || deriv < maxderneg - 1.0e-8f)) {imaxderneg=l; maxderneg=deriv;}",
}
if eps>0:
    for old,new in anchors.items():
        if section.count(old)!=1:raise RuntimeError("Missing or duplicate drainage branch anchor "+old)
        section=section.replace(old,new,1)
    changed=original[:start]+section+original[end:]
    path.write_text(changed)
else:changed=original
out.mkdir(parents=True,exist_ok=True)
(out/"03Y_ROUTING_TIE_AUDIT.json").write_text(json.dumps({
"source_revision":"danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd",
"epsilon_gradient_m_per_m":eps,
"equivalent_height_gap_per_1p25km_m":eps*1250,
"original_sha256":hashlib.sha256(raw).hexdigest(),
"patched_sha256":hashlib.sha256(changed.encode()).hexdigest(),
"target":"ONLY two steepest downslope neighbor replacement comparisons in Define_Drainage_Net",
"first_downhill_candidate_preserved":True,
"lake_zero_slope_equality_preserved":True,
"lake_saddle_classification_preserved":True,
"physical_numerics_changed":eps>0,
"geology_and_loading_preserved":True,
"restarts_binary_layout_preserved":True,
"threshold_is_hypothesis_not_factual_correction":True
},indent=2))
(out/"03Y_ROUTING_TIE.diff").write_text("".join(difflib.unified_diff(
 original.splitlines(True),changed.splitlines(True),
 fromfile="03t-original/source/surf_proc.c",
 tofile=f"03y-gradient-tie-{eps}/source/surf_proc.c")))
print("03Y_PATCH_QC epsilon="+str(eps)+" unchanged="+str(raw==changed.encode()))
