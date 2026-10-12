#!/usr/bin/env python3
"""Decompose the Ebro 2016-v-2017-v-2026 full 60 Myr discrepancy.

Causal design: 2x2 original source x original archived input cross-over.
Semantics: source change includes different defaults, not only C arithmetic.
Maps are different resolutions: compare only like-named logged GLOBAL metrics,
never cellwise/volume differences across grid sizes as a paired map.
"""
from pathlib import Path
import argparse,json,csv,statistics,math,difflib,hashlib,runpy
from collections import defaultdict

ap=argparse.ArgumentParser()
for name in ('matrix-root','old-input','new-input','old-screen','v08-full-csv','parser','out'):
 ap.add_argument('--'+name,type=Path,required=True)
a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
names={'OO':'old2017__old2017','ON':'old2017__new2026',
'NO':'new2026__old2017','NN':'new2026__new2026'}
qc={k:json.loads((a.matrix_root/name/'FULL_RUN_QC.json').read_text()) for k,name in names.items()}
assert len(qc)==4
assert all(v['full_pass'] and v['process_exit_code']==0 for v in qc.values())
fields=runpy.run_path(str(a.parser))['fields']
runs={k:fields((a.matrix_root/names[k]/'RUN.log').read_text(errors='replace')) for k in names}
ref=fields(a.old_screen.read_text(errors='replace'))
origV08=list(csv.DictReader(a.v08_full_csv.open(newline='')))
v08={float(x['age_Ma']):x for x in origV08}
stages=sorted(set.intersection(set(ref),*(set(x) for x in runs.values())))
print('V09_SIMULATION_AGE_INTERSECTION',len(stages),stages[:3],stages[-3:])
assert len(stages)>=120 and -0.5 in stages
keymetrics=['topography_max_m','topography_min_m','load_now_max_pa','load_now_total_N','deflection_max_m','deflection_min_m',
 'sediment_volume_km3','sediment_increment_N','erosion_without_sediment_N','export_sediment_N']
stages_to_end=[]
phase_bounds=[(-60,-48,'early_Pyrenean'),(-48,-35,'Iberian_thrust_and_endorheic'),
 (-35,-23.5,'pre_Valencia_extension'),(-23.5,-12.5,'extension_to_opening_window'),
 (-12.5,-8,'opening_window'),(-8,0,'late_Miocene_to_present')]
rows=[]
for t in stages:
 rec={'age_Ma':t}
 for key in keymetrics:
  H=ref[t].get(key)
  values={k:runs[k][t].get(key) for k in names}
  rec['2016_'+key]=H
  for label,value in values.items():
   rec[label+'_'+key]=value
   rec[label+'_minus_2016_'+key]=value-H if H is not None and value is not None else None
  if all(v is not None for v in values.values()):
   rec['INPUT_effect_old_solver_'+key]=values['ON']-values['OO']
   rec['SOURCE_effect_old_input_'+key]=values['NO']-values['OO']
   rec['SOURCE_effect_new_input_'+key]=values['NN']-values['ON']
   rec['INTERACTION_'+key]=values['NN']-values['NO']-values['ON']+values['OO']
  else:
   rec.update({k+'_'+key:None for k in ('INPUT_effect_old_solver','SOURCE_effect_old_input',
        'SOURCE_effect_new_input','INTERACTION')})
 if t in v08:
  zz=v08[t].get('V08_fixed_03t_topo_max_m')
  rec['V08_03t_gated_topography_max_m']=float(zz) if zz else None
  if zz and runs['NN'][t].get('topography_max_m') is not None:
   rec['03t_optimization_vs_normalized_salt_gated_m']=float(zz)-runs['NN'][t]['topography_max_m']
 rows.append(rec)
def sf(x):
 try:return float(x)
 except (ValueError,TypeError):return None
with (a.out/'V09_FULL60_ALL_DIAGNOSTICS_2016_2x2.csv').open('w',newline='') as f:
 keys=list(dict.fromkeys(k for rr in rows for k in rr))
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def rms(v):
 vals=[x for x in v if x is not None and math.isfinite(x)]
 return math.sqrt(sum(x*x for x in vals)/len(vals)) if vals else None
def mean(v):
 vals=[x for x in v if x is not None and math.isfinite(x)]
 return statistics.mean(vals) if vals else None
summary={'scientific_design':'complete 2017 C/2026 minimally salt-gated C x original 2017/2026 input 2x2',
 'old_solver_ref':'38c63ab5bacf2045530160ba8e41ae0071a04065',
 'new_solver_ref':'d18b7d270f4d671b80223e10dede329ad35cafdd + V08 corrected salt_model gate',
 'original_author_2016_screen':'TISC_2016-08-30 archived in original upstream Git repo',
 'all_runs_pass':True,'original_input_NxNy':{k:[v['input_Nx'],v['input_Ny']] for k,v in qc.items()},
 'source_version_change_also_includes_inherited_default_changes':True,
 'history_intersection_points':len(stages),'phase_metrics':{},
 'events':{}}
for lab,t in {'initial':-59.5,'minus50':-50.,'minus35':-35.,'minus30':-30.,
  'minus23_5':-23.5,'minus20':-20.,'minus12_5':-12.5,'minus10':-10.,'minus8':-8.,'last_-0_5':-0.5}.items():
 rr=next((x for x in rows if x['age_Ma']==t),None)
 if rr:
  summary['events'][lab]={k:rr.get(k) for k in [
   '2016_topography_max_m','OO_topography_max_m','ON_topography_max_m',
   'NO_topography_max_m','NN_topography_max_m','V08_03t_gated_topography_max_m',
   'OO_sediment_volume_km3','NN_sediment_volume_km3',
   'INTERACTION_topography_max_m','SOURCE_effect_old_input_topography_max_m']}
for lo,hi,name in phase_bounds:
 subset=[x for x in rows if (lo<=x['age_Ma']<hi if hi<0 else lo<=x['age_Ma']<=hi)
       and x['2016_topography_max_m'] is not None]
 phase={'start_Ma':lo,'end_Ma':hi,'n_time_points':len(subset)}
 for k in names:
  phase[k+'_maxTopo_RMS_vs2016_m']=rms([x.get(k+'_minus_2016_topography_max_m') for x in subset])
  phase[k+'_sedVolume_RMS_vs2016_km3']=rms([x.get(k+'_minus_2016_sediment_volume_km3') for x in subset])
 phase['topo_SOURCE_oldInput_RMS_m']=rms([x.get('SOURCE_effect_old_input_topography_max_m') for x in subset])
 phase['topo_INPUT_oldSolver_RMS_m']=rms([x.get('INPUT_effect_old_solver_topography_max_m') for x in subset])
 phase['topo_INTERACTION_RMS_m']=rms([x.get('INTERACTION_topography_max_m') for x in subset])
 summary['phase_metrics'][name]=phase
summary['all_time_global_RMS']={}
for k in names:
 summary['all_time_global_RMS'][k+'_topo_vs2016_m']=rms([x.get(k+'_minus_2016_topography_max_m') for x in rows])
 summary['all_time_global_RMS'][k+'_sediment_vs2016_km3']=rms([x.get(k+'_minus_2016_sediment_volume_km3') for x in rows])
summary['all_time_global_RMS']['03t_minus_pristine_fixed_topography_m']=rms([x.get('03t_optimization_vs_normalized_salt_gated_m') for x in rows])
summary['max_metric_data_coverage']={
    key:{k:sum(1 for age in stages if runs[k][age].get(key) is not None) for k in names} for key in keymetrics}
# Preserve bytewise provenance of 2017 vs 2026 files.
file_extensions=('.PRM','.UNIT','.ZINI','.SLV','.INT','.INT2','.REC','.PRFL','.EET')
old={p.name:p for p in a.old_input.iterdir() if p.is_file() and p.name.endswith(file_extensions)}
new={p.name:p for p in a.new_input.iterdir() if p.is_file() and p.name.endswith(file_extensions)}
files=[]
for name in sorted(set(old)|set(new)):
 oo=old.get(name);nn=new.get(name)
 oldbytes=oo.read_bytes() if oo else b''
 newbytes=nn.read_bytes() if nn else b''
 files.append({'filename':name,'2017_present':bool(oo),'2026_present':bool(nn),
    'identical_sha256':bool(oo and nn and oldbytes==newbytes),
    '2017_sha256':hashlib.sha256(oldbytes).hexdigest() if oo else None,
    '2026_sha256':hashlib.sha256(newbytes).hexdigest() if nn else None,
    '2017_bytes':len(oldbytes),'2026_bytes':len(newbytes)})
summary['geology_input_manifest']=files
with (a.out/'V09_ORIGINAL_AUTHOR_INPUT_DIFF_MANIFEST.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(files[0]));w.writeheader();w.writerows(files)
s=[]
for name in sorted(set(old)&set(new)):
 if old[name].read_bytes()==new[name].read_bytes():continue
 try:
  a1=old[name].read_text().splitlines(True);a2=new[name].read_text().splitlines(True)
 except UnicodeError:continue
 s.append('## '+name+'\n'+''.join(difflib.unified_diff(a1,a2,
       fromfile='2017/'+name,tofile='2026/'+name))+'\n')
(a.out/'V09_AUTHOR_INPUT_TEXT_DIFFS.md').write_text('# Original archived author Ebro input deltas\n\n'+''.join(s))
summary['2026_vs_2017_identical_geologic_geometry_files']=all(
  v['identical_sha256'] for v in files if v['filename'].endswith(('.UNIT','.ZINI','.SLV')) and v['2017_present'] and v['2026_present'])
(a.out/'V09_FULL60_CAUSAL_DECOMPOSITION.json').write_text(json.dumps(summary,indent=2))
markdown=[
 '# Full 60-Myr Ebro audit — 2016 archived screen versus real 2017 and 2026 solver×input factorial','',
 '**All four source×input original author forward simulations have completed and passed numerical and native-grid QC.**',
 ' The upstream 2026 source has ONLY the minimal V08 salt_model=0 patch (plus whitespace compilation fix), not 03t optimization. The older 2017 source is original (modern toolchain compatibility flags).',
 '',
 '| Era / pairing | 2017 Ebro inputs 104×55 | 2026 Ebro inputs 208×110 |',
 '|---|---|---|',
 '| Original 2017 source | **OO** | ON |',
 '| 2026 source + V08 salt gate | NO | **NN** |',
 '',
 'The author 2016 reference is an archived **historical log**, not a compiled executable; therefore the source effect here is a **source-plus-inherited-default effect**. The 2003 paper is not assumed to use either input snapshot.',
 '',
 '## Original input SHA256 provenance','',
 'Geological UNIT, ZINI and SLV files unchanged byte-for-byte between the two source checkouts: **'+str(summary['2026_vs_2017_identical_geologic_geometry_files'])+'**.',
 'Differences in PRM include grid size and erosion substep; other files are inventoried in V09_ORIGINAL_AUTHOR_INPUT_DIFF_MANIFEST.csv and textual diffs.',
 '',
 '## Actual time-series residual RMS by tectonic/sedimentary age stage','',
 '| Age window | Records | OO zmax RMS | ON zmax RMS | NO zmax RMS | NN zmax RMS |',
 '|---|---:|---:|---:|---:|---:|']
for name,p in summary['phase_metrics'].items():
 markdown.append('| '+str(p['start_Ma'])+' to '+str(p['end_Ma'])+' Ma | '+str(p['n_time_points'])+' | '+
 ' | '.join(('N/A' if p[k+'_maxTopo_RMS_vs2016_m'] is None else str(round(p[k+'_maxTopo_RMS_vs2016_m'],1))) for k in names)+' |')
markdown+=['', '## Key stage topography and sediment overview','',
 '| Time | 2016 original (m) | OO (m) | ON (m) | NO (m) | NN (m) | V08 optimized-fixed (m) |',
 '|---|---:|---:|---:|---:|---:|---:|']
for label in ('initial','minus50','minus35','minus30','minus23_5','minus20','minus12_5','minus10','minus8','last_-0_5'):
 event=summary['events'].get(label)
 if not event:continue
 vals=['2016_topography_max_m','OO_topography_max_m','ON_topography_max_m','NO_topography_max_m',
       'NN_topography_max_m','V08_03t_gated_topography_max_m']
 markdown.append('| '+label+' | '+' | '.join(str(event.get(k)) for k in vals)+' |')
markdown+=['','## Scientific interpretation guards','',
 '1. These are global TISC *maximum topography and printed sediment volume*; not foredeep accommodation, sedimentary wedges, basin mean height or fixed-cell topographic cross sections.',
 '2. The 2017 and 2026 source implementations have other differences including **inherited defaults**; a solver×input contrast does not isolate one line of C code by itself.',
 '3. Printed sediment volume accounting may vary in implementation; use it first as a code-diagnostic metric, not an observational sediment mass balance.',
 '4. These independent model comparisons have only the actual native final-grid archive and age-by-age logged scalar physical metrics, not full 3D palaeogeography at every age. Do not imply cell-level evolution is known at all time steps.',
 '5. The 2026 source V09 is clean source + V08 salt-gate; the separately completed V08 optimized-03t + salt-gate full run is a third implementation variant, and its differences are reported but not silently pooled.',
 '',
 '**Next work:** follow the first geological interval at which OO and 2016 historical values diverge most, then inspect the exact source functions controlling the matching field (structural topographic load, stratigraphic sediment, hydrology or lake routing); avoid global parameter tuning.',
 ]
(a.out/'V09_FULL60_CAUSAL_DECOMPOSITION.md').write_text('\n'.join(markdown)+'\n')
print('V09_FULL60_FACTORIAL_PASS',json.dumps({
 'time_points':len(stages),'global_RMS':summary['all_time_global_RMS'],
 'input_geometry_identical':summary['2026_vs_2017_identical_geologic_geometry_files'],
 'events':summary['events']},indent=2)[:14000])
