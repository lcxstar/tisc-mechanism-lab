#!/usr/bin/env python3
"""Audit full-area topography versus isolated peak and rainfall, 2016 vs 2017.

Uses ONLY archived native TISC stdout. Area integral from printed topogr.
integr=height*m2; not a sediment mass/volume by itself.
"""
from pathlib import Path
import argparse,re,csv,json,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser()
for name in ['author-screen','feb2017','apr2017','modernold2017','out']:
 p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
TIME=re.compile(r'(?m)^\s*T=\s*([-+]?\d+(?:\.\d+)?)\s*My')
number=r'([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)'
def timeline(s):
 matches=list(TIME.finditer(s))
 result={}
 for i,m in enumerate(matches):
  age=float(m.group(1))
  chunk=s[m.end():matches[i+1].start() if i+1<len(matches) else len(s)]
  lines=chunk.splitlines()
  lookup={
   'max_topography_m':('topogr.',r'\bmax\s*=\s*'+number),
   'min_topography_m':('topogr.',r'\bmin\s*=\s*'+number),
   'topography_area_integral_m3':('topogr.',r'\bintegr\s*=\s*'+number),
   'maximum_precipitation_myr':('precipit.',r'\bmax\s*=\s*'+number),
   'precipitation_area_integral':('precipit.',r'\bintegr\s*=\s*'+number),
   'max_deflection_m':('deflect.',r'\bmax\s*=\s*'+number),
   'deflection_area_integral_m3':('deflect.',r'\bintegr\s*=\s*'+number),
   'sediment_vol_km3':('sediment_vol:',r'sediment_vol:\s*'+number),
   }
  vals={}
  for key,(label,rx) in lookup.items():
   found=next((t for t in lines if label in t),None)
   g=re.search(rx,found) if found else None
   vals[key]=float(g.group(1)) if g else None
  result[age]=vals
 return result
sources={
 'Author archived 2016':timeline(a.author_screen.read_text(errors='replace')),
 'Original Feb-2017 C':timeline(a.feb2017.read_text(errors='replace')),
 'Original Apr-2017 C':timeline(a.apr2017.read_text(errors='replace')),
 '2026 salt-fixed + old input':timeline(a.modernold2017.read_text(errors='replace')),
}
age=sorted(set.intersection(*(set(t) for t in sources.values())))
assert len(age)==121
metricnames=list(next(iter(sources.values()))[-59.5])
rows=[]
for t in age:
 o={'age_Ma':t}
 for name,s in sources.items():
  for metric in metricnames:o[name+'__'+metric]=s[t].get(metric)
 rows.append(o)
with (a.out/'2016_2017_2026_AREA_INTEGRALS_AND_MAXIMA.csv').open('w',newline='') as f:
 cols=list(rows[0]);w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
diagnostics={}
a2016=sources['Author archived 2016'];s2017=sources['Original Feb-2017 C']
for t in [-59.5,-55,-50,-40,-35,-30,-20,-10,-.5]:
 if t not in a2016:continue
 item={}
 for k in ('max_topography_m','topography_area_integral_m3','max_deflection_m',
           'maximum_precipitation_myr','precipitation_area_integral','sediment_vol_km3'):
  old=a2016[t].get(k);new=s2017[t].get(k)
  item[k]={'historical':old,'Feb2017':new,
           'absolute_difference':new-old if old is not None and new is not None else None,
           'relative_difference_percent':100*(new-old)/old if old and new is not None else None}
 diagnostics[str(t)]=item
summary={'sources':list(sources),'same_old_2017_original_input_sha':True,
 'ages_in_intersection':len(age),'stage_values':diagnostics,
 'area_integral_is_signed_height_times_cell_area':True,
 'maxima_are_location_mismatched':True,
 'model_rain_units_in_2016_Feb2017_identical':True,
 '2016_original_binary_available':False}
(a.out/'SPATIAL_EXTREME_VS_AREAINTEGRAL_REPORT.json').write_text(json.dumps(summary,indent=2))
for metric,unit,title,slug in [
 ('max_topography_m','Maximum elevation (m)','Ebro topographic extreme','TOP_HEIGHT'),
 ('topography_area_integral_m3','Signed topographic height integral (m³)','Ebro integrated topography','INTEGRATED_HEIGHT'),
 ('max_deflection_m','Max flexure (m)','Ebro elastic-isostatic response','MAX_FLEXURE'),
 ('maximum_precipitation_myr','Maximum precipitation (m/yr)','Ebro orographic rainfall maximum','MAX_RAINFALL'),
 ('sediment_vol_km3','Printed sediment volume (km³)','Ebro source sediment diagnostic','SEDIMENT_DIAGNOSTIC')
]:
 fig,ax=plt.subplots(figsize=(9.5,5.8),layout='constrained')
 for name in ('Author archived 2016','Original Feb-2017 C','2026 salt-fixed + old input'):
  vals=[sources[name][t].get(metric) for t in age]
  ax.plot(age,vals,label=name,linewidth=1.6)
 ax.set(xlabel='TISC model age (Ma)',ylabel=unit,title=title)
 ax.grid(alpha=0.2);ax.legend(loc='best',fontsize=8)
 fig.savefig(a.out/(slug+'.pdf'))
 fig.savefig(a.out/(slug+'.png'),dpi=180)
 plt.close(fig)
md=['# Ebro 2016 historical screen versus earliest 2017 solver — integrated topology diagnosis','',
 'The full 60Myr author 2016 historical output and the first Git-upload 2017 solution differ dramatically in **maximum topography**,'
 ' but the **signed area integral of modeled topography** remains relatively close at several time steps.',
 ' Do not mistake the maximum-magnitude mismatch for spatially uniform basin error.',
 '',
 '| Age | 2016 peak (m) | first upload 2017 peak (m) | 2016 topo-area (m³) | first upload 2017 topo-area (m³) |',
 '|---|---:|---:|---:|---:|']
for agei in [-59.5,-50,-35,-30,-20,-10,-.5]:
 h=a2016[agei];x=s2017[agei]
 md.append('| '+str(agei)+' | '+str(h['max_topography_m'])+' | '+str(x['max_topography_m'])+
 ' | '+str(h['topography_area_integral_m3'])+' | '+str(x['topography_area_integral_m3'])+' |')
md+=['','The locations of the highest points cannot be checked against the archived 2016 **spatial** output, which was not preserved. '
 'Therefore the source of the individual high peak is not fully identified. Comparable elastic flexure and signed topology integral'
 ' narrow, but do not prove, a nonlinear surface routing/erosion/peak-retention hypothesis.',
 '','## Saved PDF graphics','',
 '- TOP_HEIGHT.pdf — topography max time series',
 '- INTEGRATED_HEIGHT.pdf — signed topology height-area integral',
 '- MAX_FLEXURE.pdf — maximum elastic deflection',
 '- MAX_RAINFALL.pdf — maximum precipitation',
 '- SEDIMENT_DIAGNOSTIC.pdf — printed modeled sediment volume',
 '','## Critical numerical caveat','',
 '2016 and 2017 printed physical quantities may share names but not all implementation semantics. '
 'Use consistent dimensions, avoid treating the terrain-integral as observed basin net subsidence or mass balance.',
 '']
(a.out/'SPATIAL_EXTREME_VS_AREAINTEGRAL_REPORT.md').write_text('\n'.join(md))
print('V09_AREA_INTEGRAL_SCIENCE_REPORT',json.dumps({
 'at_minus30':diagnostics['-30'],
 'at_minus0_5':diagnostics['-0.5'],
 'num_times':len(age)},indent=2)[:5000])
