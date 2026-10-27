#!/usr/bin/env python3
"""EXPERIMENTAL lake-check acceleration with exact cache invalidation on lake mutation.
Only in isolated source checkout; require native science regression.
Assumes nonnegative lake inflow when evaporation sum is exactly zero. Test
that assumption under independent native cases before scientific promotion.
"""
from pathlib import Path
import argparse
def rep(s,old,new,k):
    if s.count(old)!=1:raise ValueError(f"{k} anchors {s.count(old)}")
    return s.replace(old,new,1)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("source",type=Path);a=ap.parse_args()
    path=a.source
    assert path.name=="surf_proc.c"
    raw=path.read_text()
    start=raw.index("int Calculate_Discharge (struct GRIDNODE *sortcell, ModelConfig *cfg, ModelContext *ctx, float *total_lost_water, float *total_evap_water, float *total_underground_water)\n{")
    end=raw.index("free_matrix(gypsum_flux_grid",start)
    body=raw[start:end]
    assert "TISC_CACHED_LAKE_EVAP_CANDIDATE_V1" not in body
    body=rep(body,
        '\tfloat **gypsum_flux_grid = alloc_matrix(cfg->Ny, cfg->Nx);\n\tfloat **halite_flux_grid = alloc_matrix(cfg->Ny, cfg->Nx);',
        '\tfloat **gypsum_flux_grid = alloc_matrix(cfg->Ny, cfg->Nx);\n\tfloat **halite_flux_grid = alloc_matrix(cfg->Ny, cfg->Nx);\n'
        '\t/* TISC_CACHED_LAKE_EVAP_CANDIDATE_V1: lazily recalculate only after lake changes. */\n'
        '\tconst size_t _max_lakes=(size_t)cfg->Nx*(size_t)cfg->Ny+1;\n'
        '\tfloat *_lake_evap_val=calloc(_max_lakes,sizeof(float));\n'
        '\tunsigned int *_lake_evap_stamp=calloc(_max_lakes,sizeof(unsigned int));\n'
        '\tunsigned int _lake_epoch=1;\n'
        '\tif (!_lake_evap_val || !_lake_evap_stamp) {fprintf(stderr,"lake evap cache allocation failed\\n");exit(1);}\n',
        "cache init")
    check_old='''\t\t\tif (il) {
\t\t\t\tfloat lake_evap=0;
\t\t\t\tfor (int i=0; i<Lake[il].n;i++) lake_evap += evaporation[Lake[il].row[i]][Lake[il].col[i]];
\t\t\t\tlake_evap *= dx*dy;
\t\t\t\tif (Lake_Input_Discharge(cfg, il)<lake_evap && Lake[il].n>1) {
\t\t\t\t\tPRINT_DEBUGPLUS("Deletion attempt for [%d][%d] from lake %d ; lake_inp:%f ; evap:%f ; lakenodes:%d", row,col, il, Lake_Input_Discharge(cfg, il), lake_evap, Lake[il].n);
\t\t\t\t\t
\t\t\t\t\tAttempt_Delete_Node_From_Lake (cfg, ctx, row,col);
\t\t\t\t\t
\t\t\t\t\tdrow = drainage[row][col].dr_row;
\t\t\t\t\tdcol = drainage[row][col].dr_col;
\t\t\t\t\til = drainage[row][col].lake;
\t\t\t\t}
\t\t\t}'''
    check_new='''\t\t\tif (il && Lake[il].n>1) {
\t\t\t\tbool _is_sea=false;
\t\t\t\tIF_LAKE_IS_SEA(il) _is_sea=true;
\t\t\t\t/* Attempt_Delete_Node_From_Lake returns immediately for sea. */
\t\t\t\tif (!_is_sea) {
\t\t\t\t\tif ((size_t)il>=_max_lakes) {fprintf(stderr,"invalid lake index\\n");exit(1);}
\t\t\t\t\tif (_lake_evap_stamp[il]!=_lake_epoch) {
\t\t\t\t\t\tfloat _sum=0;
\t\t\t\t\t\tfor (int i=0;i<Lake[il].n;i++) _sum+=evaporation[Lake[il].row[i]][Lake[il].col[i]];
\t\t\t\t\t\t_lake_evap_val[il]=_sum*dx*dy;
\t\t\t\t\t\t_lake_evap_stamp[il]=_lake_epoch;
\t\t\t\t\t}
\t\t\t\t\tfloat lake_evap=_lake_evap_val[il];
\t\t\t\t\t/* Zero-evap shortcut is valid only for nonnegative water input;
\t\t\t\t\t   the unmodified TISC hydrological source model assumes that. */
\t\t\t\t\tif (lake_evap > 0 && Lake_Input_Discharge(cfg, il)<lake_evap) {
\t\t\t\t\t\tPRINT_DEBUGPLUS("Deletion attempt for [%d][%d] from lake %d ; lake_inp:%f ; evap:%f ; lakenodes:%d", row,col, il, Lake_Input_Discharge(cfg, il), lake_evap, Lake[il].n);
\t\t\t\t\t\tAttempt_Delete_Node_From_Lake (cfg, ctx, row,col);
\t\t\t\t\t\t/* A mutation may split/delete a lake or renumber lake indices. */
\t\t\t\t\t\tif (++_lake_epoch==0) {memset(_lake_evap_stamp,0,_max_lakes*sizeof(unsigned int));_lake_epoch=1;}
\t\t\t\t\t\tdrow = drainage[row][col].dr_row;
\t\t\t\t\t\tdcol = drainage[row][col].dr_col;
\t\t\t\t\t\til = drainage[row][col].lake;
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}'''
    body=rep(body,check_old,check_new,"check")
    outlet='''\t\t\tif (drainage[row][col].type == 'E') {
\t\t\t\tfloat lake_evap=0, input_disch, factor;
\t\t\t\tfor (int i=0; i<Lake[il].n; i++) lake_evap += evaporation[Lake[il].row[i]][Lake[il].col[i]];
\t\t\t\tlake_evap *= dx*dy;
\t\t\t\tinput_disch = Lake_Input_Discharge(cfg, il);'''
    better='''\t\t\tif (drainage[row][col].type == 'E') {
\t\t\t\tfloat lake_evap=0, input_disch, factor;
\t\t\t\tif ((size_t)il>=_max_lakes || il<=0) {fprintf(stderr,"invalid outlet lake\\n");exit(1);}
\t\t\t\tif (_lake_evap_stamp[il]!=_lake_epoch) {
\t\t\t\t\tfor (int i=0; i<Lake[il].n; i++) lake_evap += evaporation[Lake[il].row[i]][Lake[il].col[i]];
\t\t\t\t\t_lake_evap_val[il]=lake_evap*dx*dy;
\t\t\t\t\t_lake_evap_stamp[il]=_lake_epoch;
\t\t\t\t}
\t\t\t\tlake_evap=_lake_evap_val[il];
\t\t\t\tinput_disch = Lake_Input_Discharge(cfg, il);'''
    body=rep(body,outlet,better,"outlet cache")
    marker='\t/* Distribute salt deposition */'
    body=rep(body,marker,
        '\tfree(_lake_evap_val);free(_lake_evap_stamp);\n'+marker,"free cache")
    path.write_text(raw[:start]+body+raw[end:])
    print("LAKE_CACHE_CANDIDATE_PATCHED",path,flush=True)
if __name__=="__main__":main()
