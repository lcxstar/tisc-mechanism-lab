#!/usr/bin/env python3
"""Determine exact TISC call-stage that first raises a real Ebro cell by kilometres."""
import argparse,csv,gzip,json,math
from pathlib import Path
import numpy as np
phases=['after_increment','after_sort_topography','after_define_drainage','after_rain_evap',
        'after_ice_water','after_custom_node_defs','after_routing','after_transport']
p=argparse.ArgumentParser()
p.add_argument('--csv',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
arrays={};raw={};coords=None
with gzip.open(a.csv,'rt',newline='') as f:
    for rec in csv.DictReader(f):
        if int(rec['step'])!=1:continue
        ph=rec['phase']
        raw.setdefault(ph,[]).append(rec)
assert all(k in raw for k in phases),{k:len(x) for k,x in raw.items()}
n=max(int(r['row']) for r in raw[phases[0]])+1;m=max(int(r['col']) for r in raw[phases[0]])+1
assert n==110 and m==208,(n,m)
for ph in phases:
    assert len(raw[ph])==n*m
    z=np.full((n,m),np.nan);dq=z.copy();ero=z.copy();dep=z.copy();flow=z.copy();flux=z.copy();x=z.copy();y=z.copy()
    for r in raw[ph]:
        i=int(r['row']);j=int(r['col'])
        for dst,key in [(z,'topo_m'),(dq,'Dq_Pa'),(ero,'eroded_kg'),(dep,'deposited_kg'),
                        (flow,'discharge_m3s'),(flux,'masstr_kg_s'),(x,'x_km'),(y,'y_km')]:
            dst[i,j]=float(r[key])
    assert np.isfinite(z).all()
    arrays[ph]={'z':z,'Dq':dq,'erosion':ero,'deposition':dep,'flow':flow,'flux':flux,'x':x,'y':y}
main=[]
for ind,ph in enumerate(phases):
    z=arrays[ph]['z']
    idx=np.unravel_index(np.argmax(z),z.shape)
    rec=dict(phase=ph,phase_order=ind,maximum_topography_m=float(z[idx]),
       peak_row=int(idx[0]),peak_col=int(idx[1]),peak_x_km=float(arrays[ph]['x'][idx]),
       peak_y_km=float(arrays[ph]['y'][idx]),
       n_cells_over_1500m=int((z>1500).sum()),n_cells_over_2000m=int((z>2000).sum()),
       peak_Dq_Pa=float(arrays[ph]['Dq'][idx]),
       peak_deposition_kg=float(arrays[ph]['deposition'][idx]),
       peak_erosion_kg=float(arrays[ph]['erosion'][idx]))
    if ind:
        before=arrays[phases[ind-1]]['z'];diff=z-before
        changeidx=np.unravel_index(np.nanargmax(diff),diff.shape)
        rec.update(max_positive_stage_topographic_change_m=float(diff[changeidx]),
                   topographic_change_row=int(changeidx[0]),
                   topographic_change_col=int(changeidx[1]),
                   topographic_change_x_km=float(arrays[ph]['x'][changeidx]),
                   topographic_change_y_km=float(arrays[ph]['y'][changeidx]),
                   n_cells_positive_jump_over_100m=int((diff>100).sum()),
                   sum_positive_height_change_m=float(np.maximum(diff,0).sum()),
                   change_Dq_at_site_Pa=float(arrays[ph]['Dq'][changeidx]-arrays[phases[ind-1]]['Dq'][changeidx]),
                   change_eroded_kg=float(arrays[ph]['erosion'][changeidx]-arrays[phases[ind-1]]['erosion'][changeidx]),
                   change_deposited_kg=float(arrays[ph]['deposition'][changeidx]-arrays[phases[ind-1]]['deposition'][changeidx]))
    main.append(rec)
first=next((row for row in main if row['n_cells_over_1500m']>0),None)
assert first and first['phase_order']>0
stageidx=first['phase_order']
before=arrays[phases[stageidx-1]]['z']
after=arrays[phases[stageidx]]['z']
diff=after-before
inds=np.flatnonzero(diff>100)
top=np.argsort(diff.ravel())[::-1][:60]
events=[]
for flat in top:
    i,j=np.unravel_index(flat,diff.shape)
    events.append(dict(row=int(i),col=int(j),x_km=float(arrays[phases[stageidx]]['x'][i,j]),
        y_km=float(arrays[phases[stageidx]]['y'][i,j]),
        topo_before_m=float(before[i,j]),topo_after_m=float(after[i,j]),
        rise_during_stage_m=float(diff[i,j]),
        Dq_before_Pa=float(arrays[phases[stageidx-1]]['Dq'][i,j]),
        Dq_after_Pa=float(arrays[phases[stageidx]]['Dq'][i,j]),
        eroded_mass_delta_kg=float(arrays[phases[stageidx]]['erosion'][i,j]-
                                  arrays[phases[stageidx-1]]['erosion'][i,j]),
        deposited_mass_delta_kg=float(arrays[phases[stageidx]]['deposition'][i,j]-
                                   arrays[phases[stageidx-1]]['deposition'][i,j]),
        water_discharge_m3s=float(arrays[phases[stageidx]]['flow'][i,j]),
        sediment_transport_kg_s=float(arrays[phases[stageidx]]['flux'][i,j])))
with (a.out/'HYDRO_FUNCTION_STAGE_DIFFERENCES.csv').open('w',newline='') as f:
    cols=sorted({k for item in main for k in item})
    writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader();writer.writerows(main)
with (a.out/'FIRST_FUNCTION_RISE_TOP60_CELLS.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(events[0]));writer.writeheader();writer.writerows(events)
out={'original_solver_source':'danigeos/tisc d18b7d2 original C physics; V07 read-only instrumentation',
     'first_substep_Ma':[-60,-59.95],
     'phase_order':phases,
     'first_above_1500m_phase':first['phase'],
     'previous_phase':phases[stageidx-1],
     'first_phase_local_peak':first,
     'earliest_unphysical_growth_from_function':main[stageidx],
     'largest_60_grid_cells':events,
     'all_stage_diagnostics':main,
     'evidence_limit':'Atmosphere/water/discharge intermediate changes can have side-effects, per-call provenance requires C event instrumentation.'}
(a.out/'FUNCTION_STAGE_CAUSAL_LOCALIZATION.json').write_text(json.dumps(out,indent=2))
rows=['# Ebro 208×110: exact routine boundary of first anomalous grid elevation','',''
      'Cells are TISC local Cartesian x/y coordinates, NOT geographic lon/lat.',
      '',
      '| Stage | Max z (m) | Cells z>2000 m | Max positive jump from previous stage (m) |',
      '|---|---:|---:|---:|']
for r in main:
    rows.append('| '+r['phase']+' | '+str(round(r['maximum_topography_m'],3))+
        ' | '+str(r['n_cells_over_2000m'])+' | '+
        str(round(r.get('max_positive_stage_topographic_change_m',0),3))+' |')
rows+=['', '**First supra-1500 m appears at '+first['phase']+'**. Top 60 actual grid cells and '
       'incremental mass/load/discharge diagnostics in CSV.','',''
       'This is a routine-level cause localization. A positive terrain change during hydro network '
       'processing does not by itself imply physical sediment deposition; compare per-routine mass '
       'edits and follow up at line/function granularity.']
(a.out/'FUNCTION_STAGE_CAUSAL_LOCALIZATION.md').write_text('\n'.join(rows)+'\n')
print('V07_FUNCTION_STAGE_CAUSE',json.dumps({'stage':first['phase'],'old':phases[stageidx-1],
     'max':first['maximum_topography_m'],'jump':main[stageidx].get('max_positive_stage_topographic_change_m'),
     'events':events[:5]}))
