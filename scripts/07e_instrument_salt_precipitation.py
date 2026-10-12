#!/usr/bin/env python3
"""Source-localized causality test: 2026 TISC salts are deposited when salt_model=0.

Only disposable checkout source is instrumented/guarded; original TISC repo
and all author input files are unchanged. Compile-only NBSP normalization first.
"""
from pathlib import Path
import hashlib,json,sys,difflib
src=Path(sys.argv[1]); audit=Path(sys.argv[2]);mode=sys.argv[3]
before=src.read_text();txt=before
# salt_model globally defined by TISC globals.c; the unpatched source does not
# refer to the flag inside Calculate_Discharge at all.
anchor='/*Declaration of functions at libreria.c*/'
assert txt.count(anchor)==1
txt=txt.replace(anchor,'extern int salt_model;\n'+anchor,1)
statement='\t\t\t\t\tctx->topo[r][c] += dh_salt;'
assert txt.count(statement)==2,('Unexpected TWO precipitation branches',txt.count(statement))
replacement1=r'''                    if ((r==83 && c==130) || dh_salt > 50.0f)
                        fprintf(stderr,"V07SALTEVENT branch=direct salt_model=%d row=%d col=%d precip_gypsum_kg_s=%.9g precip_halite_kg_s=%.9g rise_m=%.9g dt_sec=%.9g\n",
                            salt_model,r,c,gypsum_flux_grid[r][c],halite_flux_grid[r][c],dh_salt,dt_st);
'''
replacement2=r'''                    if ((r==83 && c==130) || dh_salt > 50.0f)
                        fprintf(stderr,"V07SALTEVENT branch=lake salt_model=%d row=%d col=%d precip_gypsum_kg_s=%.9g precip_halite_kg_s=%.9g rise_m=%.9g dt_sec=%.9g\n",
                            salt_model,r,c,per_node_gypsum_flux,per_node_halite_flux,dh_salt,dt_st);
'''
p=txt.split(statement)
assert len(p)==3
txt=p[0]+replacement1+statement+p[1]+replacement2+statement+p[2]
if mode=="guard":
    # Allocation and deallocation remain unconditional and intact.
    marker='\tfloat *lake_halite_flux = calloc(nlakes + 1, sizeof(float));'
    close='\tfree(lake_gypsum_flux);'
    assert txt.count(marker)==1 and txt.count(close)==1
    txt=txt.replace(marker,marker+'\n    if (salt_model) { /* V07 TEST: obey declared 0 default salt switch */',1)
    txt=txt.replace(close,'    } /* V07 TEST: end opt-in salt precipitation */\n'+close,1)
elif mode!="logonly":raise RuntimeError(mode)
src.write_text(txt)
audit.parent.mkdir(parents=True,exist_ok=True)
diff=''.join(difflib.unified_diff(before.splitlines(True),txt.splitlines(True),
          fromfile='pinned_normalized_upstream_surf_proc.c',tofile='diagnostic_'+mode+'_surf_proc.c'))
(audit.parent/(mode.upper()+'_SOURCE.diff')).write_text(diff)
audit.write_text(json.dumps({
    'source_original_sha256':hashlib.sha256(before.encode()).hexdigest(),
    'source_modified_sha256':hashlib.sha256(txt.encode()).hexdigest(),
    'mode':mode,
    'instrumentation':'Read-only source-proximate gypsum/halite flux, height and timestep logging at 2 sink branches.',
    'physics_delta':('none' if mode=='logonly' else 'only if(salt_model) gate enclosing salt-deposition loops while retaining chemical transport'),
    'original_TISC_PRM_UNIT_ZINI_files_changed':False,
    'not_proposed_upstream_fix_without_full_validation':True
},indent=2));print('V07_SALT_SOURCE_PATCH',mode)
