#!/usr/bin/env python3
"""Final scientific acceptance from completed 14 native runs and full 60 Myr Ebro."""
from pathlib import Path
import argparse,json,csv,math,hashlib,tarfile
p=argparse.ArgumentParser()
p.add_argument('--dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
r=json.loads((a.dir/'08b_native14/V08_REGRESSION_RESULT.json').read_text())
n=json.loads((a.dir/'08d_native_numeric_comparison/NUMERIC_NATIVE_GRID_COMPARISON.json').read_text())
f=json.loads((a.dir/'08c_full_ebro_60Myr/FULL60_SALT_FIXED_QC.json').read_text())
rows=list(csv.DictReader((a.dir/'08c_full_ebro_60Myr/FULL60_AUTHOR2016_AND_ORIGINAL_V04_COMPARISON.csv').open(newline='')))
cases=r['runs'];q={}
q['14_original_input_runs_exit0_finite_native_grid']=len(cases)==14 and all(
 x['passed_basic'] and x['full_input_hashes_original_unchanged'] for x in cases.values())
for short,org,fix in [('Ebro','ebro_orig_on','ebro_fixed_on'),
 ('Lake1','lake1_orig_on','lake1_fixed_on'),('Lake2','lake2_orig_on','lake2_fixed_on')]:
 q['salt_on_'+short+'_bytewise_native_equal']=cases[org]['native_surface_sha256']==cases[fix]['native_surface_sha256']
q['fixed_off_default_equals_explicit_bytewise']=cases['ebro_fixed_off']['native_surface_sha256']==cases['ebro_fixed_off_explicit']['native_surface_sha256']
zero=next(x for x in n if x['case_A']=='ebro_fixed_off' and x['case_B']=='ebro_orig_zero_ions')
q['corrected_off_equals_original_zero_ions_all_22880_native_xyz']=zero['numpy_array_bitwise_equal'] and zero['nodes']==22880
q['fixed_off_removes_initial_9km_spike']=cases['ebro_orig_off']['max_topography_at_minus59_5_Ma']>8000 and 1100<cases['ebro_fixed_off']['max_topography_at_minus59_5_Ma']<2500
q['full_60Myr_patched_Ebro_valid_execution']=f['status']=='FULL_60MYR_EXECUTION_PASS' and f['actual_exit_code']==0
q['full_60Myr_native_22880_grid']=f['final_native_nodes']==22880
q['full_60Myr_121_printed_age_labels']=f['recorded_time_stages']==121
q['full_60Myr_no_author_input_edits']=f['native_author_inputs_modified'] is False
with tarfile.open(a.dir/'08c_full_ebro_60Myr/FULL60_NATIVE_FIXED_ORIGINAL_INPUTS.tar.gz','r:gz') as t:
 files={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest()
    for m in t.getmembers() if m.isfile() and m.name.endswith(('.PRM','.UNIT','.ZINI','.SLV','.INT','.INT2','.REC','.PRFL','.EET'))}
known=cases['ebro_orig_off']['original_author_geological_input_hashes']
q['full_original_inputs_sha256_match_pinned_upstream']=bool(known) and all(files.get(k)==v for k,v in known.items())
history=[]
for v in rows:
 if v['2016_author_topo_max_m']!='' and v['V08_fixed_03t_topo_max_m']!='':
  history.append({'age':float(v['age_Ma']),'author':float(v['2016_author_topo_max_m']),
  'baseline':float(v['V04_uncorrected_03t_topo_max_m']),'repaired':float(v['V08_fixed_03t_topo_max_m'])})
q['full_2016_comparison_120_numeric_printed_age_labels']=len(history)==120
rms=lambda a:math.sqrt(sum(v*v for v in a)/len(a))
stat={'author_vs_original_RMS_m':rms([v['baseline']-v['author'] for v in history]),
 'author_vs_repaired_RMS_m':rms([v['repaired']-v['author'] for v in history]),
 'ages':{str(age):next(v for v in history if v['age']==age) for age in (-59.5,-30,-0.5)}}
q['historical_2016_is_still_not_numerically_reproduced']=abs(stat['ages']['-0.5']['author']-stat['ages']['-0.5']['repaired'])>1000
result={'status':'PASS' if all(q.values()) else 'FAIL','passed_checks':sum(q.values()),'total_checks':len(q),
'checks':q,'comparison':stat,'original_bytewise_zero_ions_check_failed_but_numeric_xyz_exact':r['failure_causes'],
'proven_source_modes':'2026 normalized upstream + V08 salt gate for 14 regression runs',
'full_60_Myr_variant':'separately audited 03t optimized C + V08 salt gate; not bitwise original',
'original_author_input_untouched':True,'original_2016_full_match':False}
(a.out/'V08_SALT_MODULE_FINAL_ACCEPTANCE.json').write_text(json.dumps(result,indent=2))
md=['# V08 scientific salt-module fix final acceptance','',
'**FINAL '+result['status']+'**  '+str(result['passed_checks'])+'/'+str(result['total_checks'])+' checked invariants.','',
'## Regression evidence']
md+=['- '+('PASS' if v else 'FAIL')+'  '+k for k,v in q.items()]
md+=['','## Original Ebro early 0.5 Myr', '',
'| Source mode | Max elevation at -59.5 Ma |','|---|---:|',
'| 2026 original, salt_model=0 but unguarded deposition | '+str(cases['ebro_orig_off']['max_topography_at_minus59_5_Ma'])+' m |',
'| V08 salt-mode repaired, salt_model=0 | '+str(cases['ebro_fixed_off']['max_topography_at_minus59_5_Ma'])+' m |',
'| V08 patched source, salt_model=1 | '+str(cases['ebro_fixed_on']['max_topography_at_minus59_5_Ma'])+' m |',
'| 2016 historical output | 1200.8 m |',
'','## Complete Ebro 60 Myr, original input, audited 03t + V08 source','',
'| Ma | Author 2016 (m) | Original V04 uncorrected (m) | V08 fixed (m) |',
'|---|---:|---:|---:|']
for age in (-59.5,-30,-0.5):
 v=stat['ages'][str(age)]
 md+=['| '+str(age)+' | '+str(v['author'])+' | '+str(v['baseline'])+' | '+str(v['repaired'])+' |']
md+=['','RMS across 120 stages vs 2016 was '+str(round(stat['author_vs_original_RMS_m'],2))+
 ' m before salt correction and '+str(round(stat['author_vs_repaired_RMS_m'],2))+' m after correction.',
'','The 14 original-physics native models all completed (including 1lake and 2lakes).',
'Enabled salt-model output from corrected and original binaries is bytewise identical for Ebro, 1lake and 2lakes.',
'Both disabled mode variants are bytewise identical.',
'The failed cross-input strict file-hash comparison is NOT a physical failure: the independently checked original zero-ion run and corrected salt-off run are exactly equal on all 22880 native coordinate/elevation columns (zero RMS).',
'','## Scope and limitations','',
'- The fix isolates physical sediment salt deposition and chemical mass counters; dissolved-ion tracer arithmetic can still run without physical effect when the switch is off.',
'- Full 60 Myr uses the already separately audited 03t optimized variant plus this fix, not a pristine 2026 binary.',
'- Input SHA256 was compared independently between full repaired Ebro and short pinned original-source experiment.',
'- The repaired Ebro does NOT reproduce all 2016 history (at -0.5 Ma elevation remains widely different).',
'- Neither upstream author repository nor Junggar evolution code was changed.',
'','## Artifacts','',
'- Source-only patch diff and manifest: ../08b_native14/MINIMAL_SALT_MODULE_FIX.diff',
'- Actual fourteen forward model runs and logs: ../08b_native14',
'- Independent numerical native grid differences: ../08d_native_numeric_comparison/NUMERIC_NATIVE_GRID_COMPARISON.md',
'- Complete Ebro 60 Myr QC and raw outputs: ../08c_full_ebro_60Myr']
(a.out/'V08_SALT_MODULE_FINAL_ACCEPTANCE.md').write_text('\n'.join(md)+'\n')
print('V08_FINAL_ACCEPTANCE',json.dumps({'status':result['status'],'q':q,'rms':stat}))
if not all(q.values()):raise SystemExit(1)
