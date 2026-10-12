#!/usr/bin/env python3
"""Apply minimal, auditable salt_model=0 physics gate in upstream TISC.

Only a disposable checkout's tisc/src/surf_proc.c is edited. Preserve
hydrological routing, runoff, ionic transport calculation, and, when
salt_model=1, the entire original precipitation algorithm and its numerical
operation ordering. With salt_model=0, prevent ANY salt accumulation counters,
spatial gypsum/halite deposition, block-thickness and height changes or Dq
updates from the current original Calculate_Discharge() implementation.

See 2026-10-12 V07 source-level original-input five-case causal audit.
"""
from pathlib import Path
import argparse,hashlib,json,difflib,re

def sha(s):return hashlib.sha256(s.encode()).hexdigest()
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('out',type=Path)
a=p.parse_args()
src=a.source.read_text()
original=src
start=src.index('int Calculate_Discharge (struct GRIDNODE *sortcell, ModelConfig *cfg')
end=src.index('\nint ',start+10)
pre=src[:start]
func=src[start:end]
post=src[end:]
assert len(func)>15000 and len(func)<25000

# The new version did not include the salt_model external in surf_proc.c.
# Fail closed if source altered, no loose global regex.
extern='extern int salt_model;\n'
assert extern not in pre, "unexpected pre-existing salt_model declaration"
assert pre.count('/*Declaration of functions at libreria.c*/')==1
pre=pre.replace('/*Declaration of functions at libreria.c*/',extern+'/*Declaration of functions at libreria.c*/',1)

# Require TWO existing nested salt precipitation checks. Gate first one
# (the only branch that accumulates mass counters and flux grids) and its
# redundant inner check too, without changing enabled arithmetic.
original_cond='if (precip_Gypsum_flux > 0 || precip_Halite_flux > 0)'
assert func.count(original_cond)==2,func.count(original_cond)
func=func.replace(original_cond,
  'if (salt_model && (precip_Gypsum_flux > 0 || precip_Halite_flux > 0))')

# Gate BOTH direct precipitation loops as a unit; keep allocations/frees and
# unrelated hydrology/lake bookkeeping outside the guard.
begin='\t/* Distribute salt deposition */'
endmarker='\tfree(lake_gypsum_flux);'
assert func.count(begin)==1 and func.count(endmarker)==1
assert func.count('ctx->topo[r][c] += dh_salt;')==2
assert func.count('Dq[r][c] += dh_salt * g')==2
func=func.replace(begin,begin+'\n\tif (salt_model) {  /* 2026 Ebro V08: no salt material updates when mode is off */',1)
func=func.replace(endmarker,'\t} /* end physically active salt precipitation */\n'+endmarker,1)

patched=pre+func+post
assert original!=patched
a.source.write_text(patched)
a.out.mkdir(parents=True,exist_ok=True)
diff=''.join(difflib.unified_diff(original.splitlines(keepends=True),
   patched.splitlines(keepends=True),
   fromfile='pinned_upstream_normalized/surf_proc.c',
   tofile='v08_experimental_fixed/surf_proc.c'))
(a.out/'MINIMAL_SALT_MODULE_FIX.diff').write_text(diff)
result={'original_upstream_commit':'d18b7d270f4d671b80223e10dede329ad35cafdd',
'scope':'TISC 2026 src/surf_proc.c, inside original Calculate_Discharge() ONLY',
'author_original_demo_files_modified':False,
'bytewise_original_src_sha256_after_NBSP_compiler_normalization':sha(original),
'fixed_src_sha256':sha(patched),
'changes':['add explicit extern salt_model declaration',
         'when disabled gate the 2 source precipitation flux/counter accumulations',
         'when disabled gate entire direct & lake precipitation deposition and isostatic load contributions'],
'enabled_mode_numeric_expression_order_preserved':True,
'hydrological_routing_and_flushing_outside_chemical_guard':True,
'chemical_tracer_transport_still_computed_if_disabled':True,
'chemistry_inactive_has_no_physical_terrain_or_load_effect_from_this_function':True,
'upstream_authors_repo_changed':False,
'warning':'Experimentally validated patch, not upstream release or 2016 equivalence proof.'}
(a.out/'PATCH_MANIFEST.json').write_text(json.dumps(result,indent=2))
print('V08_SALT_MODULE_PATCH',json.dumps(result,indent=2))
