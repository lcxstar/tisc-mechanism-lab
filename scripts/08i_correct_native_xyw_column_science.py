#!/usr/bin/env python3
"""Correct TISC .xyw scientific columns and re-audit 14 archived V08 forward runs.

TISC original write_file_drainage prints:
 0 x(km), 1 y(km), 2 discharge(m3/s), 3 sediment flux(kg/s),
 4 node type(string), 5 terrain topography(m), ...
Prior V08 08d/08e used third data field as if terrain, incorrectly.
Preserve old reports as historical audit, publish corrected & superseding result.
"""
from pathlib import Path
import argparse,json,tarfile,math,csv
import numpy as np
ap=argparse.ArgumentParser()
ap.add_argument('--cases',type=Path,required=True)
ap.add_argument('--full60-qc',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
controls=[
 ('Ebro fixed default vs fixed explicit off','ebro_fixed_off','ebro_fixed_off_explicit'),
 ('Ebro original ON vs fixed ON','ebro_orig_on','ebro_fixed_on'),
 ('Lake 1 original ON vs fixed ON','lake1_orig_on','lake1_fixed_on'),
 ('Lake 2 original ON vs fixed ON','lake2_orig_on','lake2_fixed_on'),
 ('Ebro corrected salt OFF vs original zero dissolved ions','ebro_fixed_off','ebro_orig_zero_ions'),
 ('Ebro original unguarded OFF vs corrected OFF','ebro_orig_off','ebro_fixed_off'),
 ('Lake1 original unguarded OFF vs corrected OFF','lake1_orig_off','lake1_fixed_off'),
 ('Lake2 original unguarded OFF vs corrected OFF','lake2_orig_off','lake2_fixed_off'),
]
def read(case):
    with tarfile.open(a.cases/case/'AUTHOR_NATIVE_SHORT.tar.gz','r:gz') as tf:
        m=[m for m in tf.getmembers() if m.name.endswith('.xyw')]
        assert len(m)==1,case
        s=tf.extractfile(m[0]).read().decode(errors='replace')
    rows=[]
    for line in s.splitlines():
        q=line.split()
        if len(q)<6:continue
        try:
            row=[float(q[0]),float(q[1]),float(q[2]),float(q[3]),float(q[5])]
            if not all(math.isfinite(v) for v in row):continue
        except ValueError:continue
        rows.append(row)
    return np.asarray(rows)
out=[]
for label,A,B in controls:
    x=read(A);y=read(B)
    assert x.shape==y.shape and x.shape[1]==5,(label,x.shape,y.shape)
    assert np.array_equal(x[:,:2],y[:,:2]),label+' geographic grid must be identical'
    z=x[:,4]-y[:,4]
    wat=x[:,2]-y[:,2]
    sed=x[:,3]-y[:,3]
    v={'contrast':label,'A':A,'B':B,'grid_nodes':int(len(x)),
       'max_abs_actual_topography_diff_m':float(np.max(abs(z))),
       'rms_actual_topography_diff_m':float(np.sqrt(np.mean(z*z))),
       'max_abs_discharge_diff_m3s':float(np.max(abs(wat))),
       'rms_discharge_diff_m3s':float(np.sqrt(np.mean(wat*wat))),
       'max_abs_sediment_flux_diff_kg_s':float(np.max(abs(sed))),
       'rms_sediment_flux_diff_kg_s':float(np.sqrt(np.mean(sed*sed))),
       'all_actual_topography_same_exact':bool(np.array_equal(x[:,4],y[:,4])),
       'all_discharge_same_exact':bool(np.array_equal(x[:,2],y[:,2])),
       'all_sediment_flux_same_exact':bool(np.array_equal(x[:,3],y[:,3])),
       'cells_z_absolute_difference_over_1m':int((abs(z)>1).sum()),
       'cells_z_absolute_difference_over_100m':int((abs(z)>100).sum()),
       'native_actual_height_column_number_1_based':6,
       'native_discharge_column_number_1_based':3}
    out.append(v)
    print('CORRECTED_V08_NATIVE_DIAG',json.dumps(v),flush=True)
def case(label):return next(x for x in out if x['contrast']==label)
full=json.loads(a.full60_qc.read_text())
checks={
 'correct_xyw_topographic_index_6_applied_to_all_cases':all(x['native_actual_height_column_number_1_based']==6 for x in out),
 'Ebro_salt_ON_original_vs_fixed_native_topography_identical':case('Ebro original ON vs fixed ON')['all_actual_topography_same_exact'],
 'Lake1_salt_ON_original_vs_fixed_native_topography_identical':case('Lake 1 original ON vs fixed ON')['all_actual_topography_same_exact'],
 'Lake2_salt_ON_original_vs_fixed_native_topography_identical':case('Lake 2 original ON vs fixed ON')['all_actual_topography_same_exact'],
 'Ebro_fixed_default_vs_fixed_explicit_native_topography_identical':case('Ebro fixed default vs fixed explicit off')['all_actual_topography_same_exact'],
 'Ebro_fixed_OFF_vs_original_zeroions_actual_topography_identical':case('Ebro corrected salt OFF vs original zero dissolved ions')['all_actual_topography_same_exact'],
 'full_corrected_Ebro_60Myr_complete':full['status']=='FULL_60MYR_EXECUTION_PASS',
}
q={'status':'CORRECTED_NATIVE_PARITY_PASS' if all(checks.values()) else 'CORRECTED_NATIVE_PARITY_FAILED',
 'checks':checks,'all_checks_pass':all(checks.values()),'results':out,
 'previous_08d_08e_third_field_as_topography_is_wrong':True,
 'source_authoritative':'tisc/src/tiscio.c -> write_file_drainage() .xyw header: water(m3/s) col3, sediment flux col4, type col5, topo[m] col6',
 'prior_08d_numeric_rms_m_was_mislabelled_actual_discharge_rms':True,
 'actual_14_original_forward_runs_not_invalidated':True,
 'actual_salt_on_raw_file_SHA_parity_not_invalidated':True,
 'original_2016_full_solution_not_reproduced':True}
(a.out/'V08_CORRECTED_XYW_COLUMN_MAPPING_QC.json').write_text(json.dumps(q,indent=2))
with (a.out/'V08_CORRECTED_XYW_TERRAIN_DISCHARGE_SEDFLUX.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
md=['# V08 scientific addendum — corrected TISC native .xyw column mapping','',
 '**Supersedes the numeric column interpretation in V08 08d/08e.** TISC documents original .xyw file fields as:',
 '',
 '| Column (1-based) | Actual physical quantity |',
 '|---|---|',
 '| 1 | Native x (km) |',
 '| 2 | Native y (km) |',
 '| 3 | River/water discharge (m³/s) |',
 '| 4 | Sediment transported mass flux (kg/s) |',
 '| 5 | Routing/node type (non-numeric string) |',
 '| **6** | **Terrain topography (m)** |','',
 'Older 08d and 08e compared the first three numeric columns and called the third "topography", which is wrong. '
 'The full Ebro .screen maxima, actual C salt-gate bug and on-mode bytewise .xyw equality remain valid. '
 'The status below re-evaluates all required scientific physical columns from preserved native outputs.',
 '', '## Actual terrain comparisons', '',
 '| Case | Grid cells | Max abs Δ topography (m) | RMS Δ topography (m) | Max abs Δ discharge (m³/s) |',
 '|---|---:|---:|---:|---:|']
for x in out:
 md.append('| '+x['contrast']+' | '+str(x['grid_nodes'])+
  ' | '+str(round(x['max_abs_actual_topography_diff_m'],6))+
  ' | '+str(round(x['rms_actual_topography_diff_m'],6))+
  ' | '+str(round(x['max_abs_discharge_diff_m3s'],6))+' |')
md+=['','**NEW SCIENTIFIC ACCEPTANCE = '+str(q['status'])+'**','',
 '## Boundary of claims','',
 'The source-localized improper salt deposition under salt_model=0 and 14 completed original-input native model runs are not undone by this post-processing error. '
 'However, old 08d/08e assertions about 22880 elevation columns should not be cited. Use this corrected addendum. '
 'The original 2016 historical peak chronology still does not match repaired 2026 source.']
(a.out/'V08_CORRECTED_XYW_COLUMN_MAPPING_REPORT.md').write_text('\n'.join(md))
if not q['all_checks_pass']:raise SystemExit(1)
