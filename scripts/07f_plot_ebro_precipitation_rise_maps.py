#!/usr/bin/env python3
"""Plot spatial exact first-substep ion precipitation height and load increments.

Uses native before/after Calculate_Discharge() grid traces; no interpolation or
forward simulation. Local model Cartesian coordinate axis, never lat/lon.
"""
from pathlib import Path
import argparse,csv,gzip,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=argparse.ArgumentParser()
p.add_argument('--csv',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
nrows,ncols=110,208
z1=np.full((nrows,ncols),np.nan);z2=z1.copy();q1=z1.copy();q2=z1.copy();xx=z1.copy();yy=z1.copy()
with gzip.open(a.csv,'rt',newline='') as f:
    for r in csv.DictReader(f):
        if int(r['step'])!=1 or r['phase'] not in ('after_custom_node_defs','after_routing'):continue
        i,j=int(r['row']),int(r['col'])
        if r['phase']=='after_custom_node_defs':
            z1[i,j]=float(r['topo_m']);q1[i,j]=float(r['Dq_Pa'])
        else:
            z2[i,j]=float(r['topo_m']);q2[i,j]=float(r['Dq_Pa'])
            xx[i,j]=float(r['x_km']);yy[i,j]=float(r['y_km'])
assert np.isfinite(z1).all() and np.isfinite(z2).all()
extent=[xx.min(),xx.max(),yy.min(),yy.max()]
dz=z2-z1
dq=(q2-q1)/1e6
rmax,cmax=np.unravel_index(np.argmax(dz),dz.shape)
assert (rmax,cmax)==(83,130)
metadata={'first_stable_phase':'after_custom_node_defs',
'first_abnormal_phase':'after_routing',
'source_C':'Calculate_Discharge',
'row':int(rmax),'col':int(cmax),'x_km':float(xx[rmax,cmax]),'y_km':float(yy[rmax,cmax]),
'delta_topography_m':float(dz[rmax,cmax]),'delta_Dq_MPa':float(dq[rmax,cmax]),
'n_cells_above_100m_chemical_height_change':int((dz>100).sum()),
'not_WGS84_geographic_coordinates':True,'no_numeric_interpolation':True,
'source_2017_old_solver_does_not_have_salt_chemistry':True}
(a.out/'FIRST_HYDRO_SALT_SPATIAL_QC.json').write_text(json.dumps(metadata,indent=2))
for title,arr,name,unit in [
 ('Height added during Calculate_Discharge() — first Ebro surface substep',dz,
  'SALT_DEPOSITION_HEIGHT_FIRST_005MYR','Topography increase (m)'),
 ('Load increment during Calculate_Discharge() — first Ebro surface substep',dq,
  'SALT_DEPOSITION_LOAD_FIRST_005MYR','TISC Dq increment (MPa)')
]:
    fig,ax=plt.subplots(figsize=(10,6),layout='constrained')
    im=ax.imshow(arr,origin='upper',extent=extent,aspect='auto',interpolation='nearest')
    ax.scatter([xx[rmax,cmax]],[yy[rmax,cmax]],s=170,marker='*',
        label=f'first extreme ({rmax},{cmax})',edgecolors='black')
    ax.set(title=title,xlabel='Local TISC model x (km)',ylabel='Local TISC model y (km)')
    ax.legend(loc='upper left')
    fig.colorbar(im,ax=ax,label=unit,shrink=.8)
    fig.text(.1,.012,
      'Original 2026 C code, unaltered geology; read-only native cell diagnostics. 0.05 Myr is a surface substep, not a new paleogeographic age.',
      fontsize=8)
    fig.savefig(a.out/(name+'.png'),dpi=180)
    fig.savefig(a.out/(name+'.pdf'))
    plt.close(fig)
print('EBRO_SALT_PLOT_PASS',json.dumps(metadata))
