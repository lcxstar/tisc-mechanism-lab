#!/usr/bin/env python3
"""Published 3-corner longitudinal controlled contrast, without fourth running arm.

Uses 2017 C+old inputs, 2026 salt-corrected C+old inputs and same C+new
inputs. Source effect includes associated defaults; input effect changes
resolution and erosional timestep jointly. Do not imply a complete 2x2.
"""
from pathlib import Path
import argparse,csv,json,math,runpy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

p=argparse.ArgumentParser()
for k in ('original-screen','old-old','new-old','new-new','parser','out'):
    p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
fun=runpy.run_path(str(a.parser))['fields']
records={'2016_author':fun(a.original_screen.read_text(errors='replace')),
         '2017_original_old_input':fun(a.old_old.read_text(errors='replace')),
         '2026_fixed_old_input':fun(a.new_old.read_text(errors='replace')),
         '2026_fixed_new_input':fun(a.new_new.read_text(errors='replace'))}
ages=sorted(set.intersection(*(set(v) for v in records.values())))
assert len(ages)==121
metrics=['topography_max_m','topography_min_m','deflection_max_m',
 'sediment_volume_km3','load_now_max_pa','load_now_total_N']
rows=[]
for age in ages:
 row={'age_Ma':age}
 for m in metrics:
    H=records['2016_author'][age].get(m)
    OO=records['2017_original_old_input'][age].get(m)
    NO=records['2026_fixed_old_input'][age].get(m)
    NN=records['2026_fixed_new_input'][age].get(m)
    row.update({f'2016_{m}':H,f'2017_OLD_{m}':OO,f'2026_OLD_{m}':NO,
      f'2026_NEW_{m}':NN})
    row[f'new_source_plus_defaults_effect_fixed_old_geometry_{m}']=NO-OO if NO is not None and OO is not None else None
    row[f'input_grid_dt_effect_fixed_2026_solver_{m}']=NN-NO if NN is not None and NO is not None else None
    row[f'remaining_2016_residual_newsolver_newinput_{m}']=NN-H if NN is not None and H is not None else None
 rows.append(row)
with (a.out/'THREE_CORNER_60Myr_SOURCE_AND_INPUT_EFFECTS.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
RMS=lambda vals:math.sqrt(sum(x*x for x in vals)/len(vals)) if vals else None
def stats(rr):
 out={}
 for k in ['topography_max_m','deflection_max_m','sediment_volume_km3']:
  for tag in ['new_source_plus_defaults_effect_fixed_old_geometry',
     'input_grid_dt_effect_fixed_2026_solver','remaining_2016_residual_newsolver_newinput']:
   vals=[float(x[tag+'_'+k]) for x in rr if x[tag+'_'+k] is not None]
   out[tag+'__'+k+'__RMS']=RMS(vals)
 return out
summary={'reported_model_runs_passed':3,'fourth_2017_solver_on_new2026_grid_required_for_full_2x2':True,
 'physical_2016_model_input_not_independently_reproduced':True,
 'original_source_ref':'38c63ab5bacf2045530160ba8e41ae0071a04065',
 'updated_source_ref':'d18b7d270f4d671b80223e10dede329ad35cafdd',
 'source_effect_includes_defaults':True,
 'new_input_effect_includes_both_grid_size_and_surface_dt_eros':True,
 'age_count':len(ages),
 'global_rms':stats(rows),'stage_rms':{},
 'representative_times':{}}
periods=[(-60,-50),(-50,-35),(-35,-23.5),(-23.5,-12.5),(-12.5,-8),(-8,0)]
for lo,hi in periods:
 rr=[x for x in rows if (lo<=x['age_Ma']<hi if hi<0 else lo<=x['age_Ma']<=hi)]
 summary['stage_rms'][f'{lo}_to_{hi}']=dict(n=len(rr),**stats(rr))
for t in [-59.5,-55,-50,-35,-30,-20,-10,-.5]:
 row=next((x for x in rows if x['age_Ma']==t),None)
 if row:
   summary['representative_times'][str(t)]={k:v for k,v in row.items() if
     k=='age_Ma' or k.endswith('_topography_max_m') or k.endswith('_deflection_max_m') or k.endswith('_sediment_volume_km3')}
(a.out/'THREE_CORNER_CAUSAL_COMPARISON.json').write_text(json.dumps(summary,indent=2))
names={'2016_author':'2016 archived','2017_original_old_input':'2017 C, old 104x55',
   '2026_fixed_old_input':'2026 fixed C, old 104x55',
   '2026_fixed_new_input':'2026 fixed C, new 208x110'}
for metric,unit,label in [
 ('topography_max_m','Maximum z (m)','EARLY_TO_LATE_TOPO_PEAK'),
 ('deflection_max_m','Maximum flexure (m)','FLEXURE_SOURCE_EFFECT'),
 ('sediment_volume_km3','Printed sediment volume (km³)','SEDIMENT_SOURCE_EFFECT')]:
 fig,ax=plt.subplots(figsize=(10,5.8),layout='constrained')
 for k in records:
  ax.plot(ages,[records[k][age].get(metric) for age in ages],lw=1.7,label=names[k])
 ax.set(xlabel='TISC geological model age (Ma)',ylabel=unit)
 ax.set_title('Ebro 2016 history vs archived full C solver versions')
 ax.grid(alpha=.22);ax.legend(fontsize=8)
 fig.savefig(a.out/(label+'.pdf'))
 fig.savefig(a.out/(label+'.png'),dpi=180)
 plt.close(fig)
outmd=[
'# Controlled Ebro original-author three-arm longterm response (fourth heavy arm pending)','',
'Real entire -60 to 0Ma forward runs, all complete 121 age labels, unlike the incomplete 2×2.',
'2016 historical is a saved original stdout log and **not** a runnable 2016 binary.','',
'| Age | Historic 2016 max topo | 2017 solver + old grid | 2026 fixed + old grid | 2026 fixed + new grid |',
'|---|---:|---:|---:|---:|']
for t in [-59.5,-50,-35,-30,-20,-10,-.5]:
 x=summary['representative_times'][str(t)]
 outmd.append('| '+str(t)+' | '+
  ' | '.join(str(x.get(k+'_topography_max_m')) for k in
   ('2016','2017_OLD','2026_OLD','2026_NEW'))+' |')
outmd+=['','## Inference allowed with these three complete results','',
'2017 old to 2026 fixed on the same 2017 input isolates **source implementation plus inherited defaults**.',
'2026 fixed old to 2026 fixed new isolates **joint grid and dt_eros input differences**.',
'Do not separately attribute this difference solely to grid or solely to erosion time step.',
'The fourth source×input cross (2017 source on new fine grid) is required to compute a complete interaction effect.',
'2016 historical extrema are not physical calibration targets; integrated terrain and other outputs must be checked independently.',
'','The source-controlled phase RMS and all 121 time-stage physical values are stored in machine-readable JSON/CSV.',
'']
(a.out/'THREE_CORNER_60Myr_SCIENTIFIC_NOTE.md').write_text('\n'.join(outmd))
print('V09_THREE_CORNER_FINAL',json.dumps(summary['representative_times'],indent=2)[:6500])
