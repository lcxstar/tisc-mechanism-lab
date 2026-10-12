#!/usr/bin/env python3
"""Exact same-geometry 104x55 Ebro modern-minus-2017 final surface difference.

Both models ran all -60..0 Myr with untouched byte-identical original old
PRM/UNIT/ZINI geometry; native .xyw XY+surface third column are aligned by
coordinate, not index. The author 2016 spatial snapshot is unavailable.
"""
from pathlib import Path
import argparse,tarfile,numpy as np,csv,json,math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
p=argparse.ArgumentParser()
for k in ['old-tar','new-tar','old-qc','new-qc','out']:
 p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
oldinfo=json.loads(a.old_qc.read_text());newinfo=json.loads(a.new_qc.read_text())
assert oldinfo['full_pass'] and newinfo['full_pass']
assert oldinfo['input_Nx']==newinfo['input_Nx']==104
assert oldinfo['input_Ny']==newinfo['input_Ny']==55
assert oldinfo['original_demo_file_hashes']==newinfo['original_demo_file_hashes']
def native(p):
 with tarfile.open(p,'r:gz') as tf:
  k=[x for x in tf.getmembers() if x.name=='Ebro_evol.xyw']
  assert len(k)==1
  s=tf.extractfile(k[0]).read().decode(errors='replace')
  out=[]
  for line in s.splitlines():
   q=line.split()
   if len(q)<3:continue
   try:row=list(map(float,q[:3]))
   except ValueError:continue
   if all(math.isfinite(x) for x in row):out.append(row)
  return np.asarray(out)
x=native(a.old_tar);y=native(a.new_tar)
assert x.shape==y.shape==(104*55,3)
# exact aligned coordinate invariant
if not np.array_equal(x[:,:2],y[:,:2]):
 o={(round(row[0],7),round(row[1],7)):row[2] for row in x}
 w={(round(row[0],7),round(row[1],7)):row[2] for row in y}
 assert o.keys()==w.keys()
 keys=sorted(o);aold=np.array([o[k] for k in keys]);anew=np.array([w[k] for k in keys]);coords=np.array(keys)
else:coords=x[:,:2];aold=x[:,2];anew=y[:,2]
dz=anew-aold
ux=np.sort(np.unique(coords[:,0]));uy=np.sort(np.unique(coords[:,1]))
assert len(ux)==104 and len(uy)==55,(len(ux),len(uy))
grid=np.full((55,104),np.nan)
for (cx,cy),delta in zip(coords,dz):
 i=np.searchsorted(uy,cy);j=np.searchsorted(ux,cx)
 grid[i,j]=delta
assert np.isfinite(grid).all()
extent=[float(ux[0]),float(ux[-1]),float(uy[0]),float(uy[-1])]
xunits='km' if max(abs(extent[0]),abs(extent[1]))<3000 else 'm'
imax=np.argmax(dz);imin=np.argmin(dz)
record={'comparison':'new2026_source_V08_salt_fixed__old2017_input MINUS old2017_source__old2017_input',
 'both_original_geological_input_SHA_identical':True,'same_coordinate_pairs':104*55,
 'max_positive_delta_m':float(dz[imax]),'positive_site_original_native_x':float(coords[imax,0]),'positive_site_original_native_y':float(coords[imax,1]),
 'max_negative_delta_m':float(dz[imin]),'negative_site_original_native_x':float(coords[imin,0]),'negative_site_original_native_y':float(coords[imin,1]),
 'mean_delta_m':float(dz.mean()),'median_delta_m':float(np.median(dz)),
 'rms_delta_m':float(np.sqrt(np.mean(dz**2))),
 'percentile_5_50_95_99_m':np.percentile(dz,[5,50,95,99]).tolist(),
 'n_abs_difference_more_than_100m':int((abs(dz)>100).sum()),
 'n_abs_difference_more_than_500m':int((abs(dz)>500).sum()),
 'n_abs_difference_more_than_1000m':int((abs(dz)>1000).sum()),
 'old_max_topography_native_m':float(aold.max()),'new_max_topography_native_m':float(anew.max()),
 'native_xy_units_inferred':xunits,'native_extent':extent,
 'age_interpretation':'native final 0 Ma grid output, not age -0.5 logged scalar checkpoint',
 'archived_2016_full_native_spatial_field_available':False,
 'source_change_includes_default_parameter_changes':True,
 'source_fixed_2026_has_minimal_salt_mode_gate':True}
(a.out/'MATCHED_2017_VS_2026_FINAL_GRID_QC.json').write_text(json.dumps(record,indent=2))
np.savetxt(a.out/'MATCHED_104x55_FINAL_DELTATOPO_XYZ.csv',
           np.column_stack([coords, aold,anew,dz]),fmt='%.9g',
           header='native_x,native_y,2017_orig_topography_m,2026_V08_topography_m,delta_m',delimiter=',',comments='')
fig,ax=plt.subplots(figsize=(11,6.3),layout="constrained")
vmax=max(abs(np.percentile(dz,1)),abs(np.percentile(dz,99)))
im=ax.imshow(grid,origin='lower',extent=extent,cmap='RdBu_r',vmin=-vmax,vmax=vmax,interpolation='nearest',aspect='auto')
ax.scatter(coords[[imax,imin],0],coords[[imax,imin],1],marker='x',s=90,color='black',label='Largest signed changes')
ax.set(xlabel='TISC native x ('+xunits+')',ylabel='TISC native y ('+xunits+')',
 title='Ebro final elevation difference (2026 fixed solver minus 2017 original solver)\nSame original 104 × 55 grid and identical geological inputs')
fig.colorbar(im,ax=ax,shrink=.85,label='Final topography difference (m)')
ax.legend(loc='best')
fig.savefig(a.out/'MATCHED_104x55_TERRAIN_SOURCE_DIFFERENCE.pdf')
fig.savefig(a.out/'MATCHED_104x55_TERRAIN_SOURCE_DIFFERENCE.png',dpi=180)
plt.close(fig)
fig,ax=plt.subplots(figsize=(8.6,5.5),layout='constrained')
ax.hist(dz,bins=70)
ax.axvline(0,ls='--',color='black')
ax.set(title='Distribution of final cell-by-cell elevation changes',xlabel='New source minus old source (m)',
 ylabel='Original 104 × 55 grid-cell count')
fig.savefig(a.out/'MATCHED_104x55_ELEVATION_DIFFERENCE_HISTOGRAM.pdf')
fig.savefig(a.out/'MATCHED_104x55_ELEVATION_DIFFERENCE_HISTOGRAM.png',dpi=180)
plt.close(fig)
markdown=['# Ebro modern versus 2017 original, matching exact geological grid and 60-Myr integration','',
 '**All 5720 native coordinate pairs matched; geological PRM/UNIT/ZINI/SVL files have identical SHA256.**',
 '', '| Diagnostic at final native 0 Ma | Value |','|---|---:|']
for label,key in [('Grid pairs','same_coordinate_pairs'),('RMS terrain change (m)','rms_delta_m'),
('Max positive delta (m)','max_positive_delta_m'),('Max negative delta (m)','max_negative_delta_m'),
('Cells changed more than 100m','n_abs_difference_more_than_100m'),
('Cells changed more than 1000m','n_abs_difference_more_than_1000m')]:
 markdown.append('| '+label+' | '+str(record[key])+' |')
markdown+=['','This is **not** a location-by-location comparison to the archived 2016 author screen. '
 'The 2016 native spatial grid was not preserved. These experiments identify the spatial signature '
 'of changing the 2017 source to 2026 salt-fixed C source on exactly the same archived 2017 geological input. '
 'Runtime inherited defaults may also differ.','',
 '## Plots','',
 '- MATCHED_104x55_TERRAIN_SOURCE_DIFFERENCE.pdf — exact spatial difference (not interpolated)',
 '- MATCHED_104x55_ELEVATION_DIFFERENCE_HISTOGRAM.pdf — magnitude/distribution',
 '- MATCHED_104x55_FINAL_DELTATOPO_XYZ.csv — every matched native x/y/old height/new height/difference row',
 '']
(a.out/'MATCHED_FINAL_GRID_SCIENCE_REPORT.md').write_text('\n'.join(markdown))
print('V09_MATCHED_SPATIAL_RESULTS',json.dumps(record,indent=2))
