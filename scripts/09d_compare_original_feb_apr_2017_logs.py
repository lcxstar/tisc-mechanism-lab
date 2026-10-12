#!/usr/bin/env python3
"""Audit same-input longitudinal first-upload February vs April 2017 and modern TISC.

The historical author screen isn't a binary; exact 2016 source unavailable.
Identify first threshold crossing for topology, flexure, sediment and mass metrics.
"""
from pathlib import Path
import argparse,json,csv,math,runpy,statistics
p=argparse.ArgumentParser()
for k in ['screen','feb-run','apr-run','modern-run','parser','out']:
    p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
fields=runpy.run_path(str(a.parser))['fields']
logs={'screen2016':fields(a.screen.read_text(errors='replace')),
      'feb2017':fields(a.feb_run.read_text(errors='replace')),
      'apr2017':fields(a.apr_run.read_text(errors='replace')),
      'modern_fixed':fields(a.modern_run.read_text(errors='replace'))}
ages=sorted(set.intersection(*(set(v) for v in logs.values())))
assert len(ages)>=120
values=['topography_max_m','topography_min_m','deflection_max_m','deflection_min_m',
   'load_now_max_pa','load_now_total_N','sediment_volume_km3','sediment_increment_N','export_sediment_N']
out=[]
for t in ages:
    row={'age_Ma':t}
    for k in values:
        ref=logs['screen2016'][t].get(k)
        row['screen2016_'+k]=ref
        for name in ['feb2017','apr2017','modern_fixed']:
            v=logs[name][t].get(k)
            row[name+'_'+k]=v
            row[name+'_minus_historical_'+k]=(v-ref if v is not None and ref is not None else None)
    out.append(row)
with (a.out/'FEB_APR_MODERN_2016_TIME_HISTORY.csv').open('w',newline='') as f:
    keys=list(out[0]);writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(out)
def rms(numbers):
    x=[v for v in numbers if v is not None]
    return math.sqrt(sum(v*v for v in x)/len(x)) if x else None
def thresholds(key,model,limits):
    return {str(v):next((r['age_Ma'] for r in out if r[model+'_minus_historical_'+key] is not None
        and abs(r[model+'_minus_historical_'+key])>v),None) for v in limits}
summ={'time_intersection_count':len(ages),
 'models':list(logs),
 'full_native_time_series_not_original_2016_binary':True,
 'metric_label_semantics_may_have_evolved':True,
 'rms_global':{},
 'first_divergence_absolute_thresholds':{},
 'age_snapshots':{},
 'evidence_limits':['global maxima occur at non-identical cells; maxima differences do not prove same-cell process',
    'Ebro 2016 screen is a historical output without original executable',
    'the 2017 Feb Git snapshot is closest available to 2016; it is not proven to be exact 2016 code']}
for name in ('feb2017','apr2017','modern_fixed'):
    summ['rms_global'][name]={key:rms([x[name+'_minus_historical_'+key] for x in out]) for key in values}
    summ['first_divergence_absolute_thresholds'][name]={
      'maxTopo_abs_m':thresholds('topography_max_m',name,[50,200,500,1000,3000]),
      'maxFlexure_abs_m':thresholds('deflection_max_m',name,[50,200,500,1000,3000]),
      'sediment_vol_abs_km3':thresholds('sediment_volume_km3',name,[1000,10000,30000,100000]),
      'load_max_abs_MPa':thresholds('load_now_max_pa',name,[1e6,1e7,1e8])}
for t in [-60,-59.5,-55,-50,-48,-45,-40,-35,-30,-23.5,-20,-15,-12.5,-10,-8,-5,-.5]:
    row=next((x for x in out if x['age_Ma']==t),None)
    if not row:continue
    summ['age_snapshots'][str(t)]={
      key:{model:row[model+'_'+key] for model in logs} for key in
      ('topography_max_m','deflection_max_m','sediment_volume_km3','load_now_max_pa')}
(a.out/'V09_FEB_APR_2017_SOURCE_DIVERGENCE.json').write_text(json.dumps(summ,indent=2))
m=['# Earliest publicly deposited source vs later 2017 TISC: whole Ebro 60Myr','',
   'Author 2016 output is archival, *not* an executable we can replay. '
   'This audit uses same original 2017 PRM and geometry at 104×55.',
   '',
   '| Age (Ma) | Author 2016 max z | Feb 2017 source | Apr 2017 source | Current 2026 gated V08 / old geometry |',
   '|---|---:|---:|---:|---:|']
for t in [-59.5,-55,-50,-45,-40,-35,-30,-23.5,-20,-15,-10,-5,-.5]:
    row=next((x for x in out if x['age_Ma']==t),None)
    if row:
        m.append('| '+str(t)+' | '+' | '.join(str(row.get(k+'_topography_max_m')) for k in ('screen2016','feb2017','apr2017','modern_fixed'))+' |')
m+=['','## First time thresholds are exceeded', '',
    '| Source versus author 2016 | >200m max z | >1000m max z | >200m max flexure |',
    '|---|---|---|---|']
for name in ('feb2017','apr2017','modern_fixed'):
    c=summ['first_divergence_absolute_thresholds'][name]
    m.append('| '+name+' | '+str(c['maxTopo_abs_m']['200'])+
       ' | '+str(c['maxTopo_abs_m']['1000'])+
       ' | '+str(c['maxFlexure_abs_m']['200'])+' |')
m+=['','## Differences in computational diagnostics',
      'The normal reference is a historical screen, not an exact binary. Native full-field snapshots for 2016 are unavailable, so only global diagnostics can be compared. '
      'A superficially similar flexure maximum does not prove identical uplift at the same cells.',
      '','Complete numerical differences per 0.5Myr are in FEB_APR_MODERN_2016_TIME_HISTORY.csv.']
(a.out/'V09_FEB_APR_2017_SOURCE_DIVERGENCE.md').write_text('\n'.join(m)+'\n')
print('V09_2016_FEB_APR_COMPARISON',json.dumps(summ)[:13500])
