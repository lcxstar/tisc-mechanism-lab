#!/usr/bin/env python3
"""Experimental invariant-preserving fast duplicate check for Add_Node_To_Lake.

In the official TISC source, every entry in Lake[il] has
abs(drainage[row][col].lake) == il except temporarily in Unify_Lakes, which
explicitly preassigns the new lake ID before calling Add_Node_To_Lake.
Remove that unnecessary preassignment; Add_Node_To_Lake itself writes -il.
Only scan for an existing duplicate when drainage already indicates the
target lake.  A member of Lake[il] with a different marker violates the
original model's own drainage/lake invariant and is not a valid state.

All geometric/hydrological calculations, output fields and node order
remain untouched.  This experimental candidate must pass native regression.
"""
from pathlib import Path
import argparse

def once(s,old,new,name):
    k=s.count(old)
    if k!=1: raise RuntimeError(f"{name}: match count {k}, expected one")
    return s.replace(old,new,1)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("source",type=Path);args=ap.parse_args()
    path=args.source
    assert path.name=="surf_proc.c" and path.is_file()
    source=path.read_text()
    start=source.index("int Add_Node_To_Lake (int row, int col, int i_lake)")
    end=source.index("\n\nint Add_Outlet_To_Lake",start)
    body=source[start:end]
    old='''\tfor (i=0; i<Lake[il].n; i++) 
\t\tif (row==Lake[il].row[i] && col==Lake[il].col[i]) {
\t\t  \tPRINT_ERROR("[%d][%d] tried to repeat lake node.", row, col);
\t\t\treturn(0);
\t\t}'''
    new='''\t/* TISC_FAST_LAKE_MEMBERSHIP_V1: O(1) candidate exclusion before O(n) duplicate test.
\t * Existing members MUST carry their lake ID in drainage[]; the complete old
\t * scan is retained whenever the node is already labelled with the target ID.
\t */
\tif (drainage[row][col].lake == il || drainage[row][col].lake == -il)
\t\tfor (i=0; i<Lake[il].n; i++)
\t\t\tif (row==Lake[il].row[i] && col==Lake[il].col[i]) {
\t\t\t\tPRINT_ERROR("[%d][%d] tried to repeat lake node.", row, col);
\t\t\t\treturn(0);
\t\t\t}'''
    body=once(body,old,new,"duplicate_scan")
    source=source[:start]+body+source[end:]
    # Unify_Lakes has one call of Add_Node, before which an unnecessary write
    # fakes target membership; removal preserves the eventual -il assigned by Add_Node.
    oldmerge='''\tfor (i=0; i<Lake[ild].n; i++) {
\t\tdrainage[Lake[ild].row[i]][Lake[ild].col[i]].lake = i_lake;
\t\tAdd_Node_To_Lake(Lake[ild].row[i], Lake[ild].col[i], i_lake);
\t}'''
    newmerge='''\tfor (i=0; i<Lake[ild].n; i++) {
\t\tAdd_Node_To_Lake(Lake[ild].row[i], Lake[ild].col[i], i_lake);
\t}'''
    source=once(source,oldmerge,newmerge,"unify_membership")
    path.write_text(source)
    print("EXPERIMENTAL_LAKE_NODE_DUPLICATE_FASTPATH_APPLIED",path,flush=True)

if __name__=="__main__":main()
