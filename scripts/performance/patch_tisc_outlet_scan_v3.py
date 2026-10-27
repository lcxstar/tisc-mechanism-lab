#!/usr/bin/env python3
"""Candidate-only: eliminate redundant whole-lake scans in Define_Drainage_Net.

A lake with an outlet at the current topographic level must have had
Add_Outlet_To_Lake called since the previous level was finalized.  When that
never happened, the original n_lakes scan can have no new positive effect.
At all other heights, preserve the complete native loop untouched.

Not accepted without byte-identical numeric regression on 5km, long 10km
and multiple drainage-boundary cases.  Works only on pinned TISC source.
"""
import argparse
from pathlib import Path

def once(txt, old, new, name):
    count=txt.count(old)
    if count != 1:
        raise RuntimeError(f"Anchor {name}: expected 1, got {count}")
    return txt.replace(old, new, 1)

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("source",type=Path)
    args=cli.parse_args()
    path=args.source
    assert path.name=="surf_proc.c" and path.is_file()
    orig=path.read_text()
    start=orig.index("int Define_Drainage_Net (struct GRIDNODE *sortcell, ModelConfig *cfg, ModelContext *ctx)")
    end=orig.index("\n\nint ",start+30)
    body=orig[start:end]
    if "TISC_SKIP_REDUNDANT_OUTLET_SCAN_V1" in body:
        raise RuntimeError("Already applied")
    body=once(body,
        '\t/*Define lakes ascending in the topo grid (bottom-up).*/',
        '\t/* TISC_SKIP_REDUNDANT_OUTLET_SCAN_V1: only skip scans without any new outlet at this height. */\n'
        '\tbool _tisc_any_outlet_at_level=false;\n'
        '\t/*Define lakes ascending in the topo grid (bottom-up).*/',"flag")
    for old,name in [
        ('Add_Outlet_To_Lake(i,j,ro[imaxderneg_noundef],co[imaxderneg_noundef], undef_lake_adj);',"undef"),
        ('Add_Outlet_To_Lake(i,j, ro[imaxderneg], co[imaxderneg], i_lake);',"newlake"),
        ('Add_Outlet_To_Lake(i,j,SIGNAL,SIGNAL,drainage[i][j].lake);',"border")]:
        body=once(body,old,old+' _tisc_any_outlet_at_level=true;',name)
    # Preserve native lake-defining for all heights with potential newly created outlet.
    body=once(body,
        '''\t\t\tif (switch_change_in_next_height || isort==0) {
\t\t\t\tfor (int l=1; l<=nlakes; l++) {''',
        '''\t\t\tif (switch_change_in_next_height || isort==0) {
\t\t\t\tif (_tisc_any_outlet_at_level) for (int l=1; l<=nlakes; l++) {''',"full_lake_scan")
    body=once(body,
        '''\t\t\t\t}
\t\t\t}
\t\t}
\t\telse {
\t\t\t/*''',
        '''\t\t\t\t}
\t\t\t\t_tisc_any_outlet_at_level=false;
\t\t\t}
\t\t}
\t\telse {
\t\t\t/*''',"reset")
    # sea case scan always remains original; do not optimize it.
    path.write_text(orig[:start]+body+orig[end:])
    print("OUTLET_LEVEL_SKIP_PATCH_APPLIED (experimental only)",path,flush=True)

if __name__=="__main__":
    main()
