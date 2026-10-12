#!/usr/bin/env python3
"""Compare native .xyw physically not bytewise from already archived 14 V08 runs."""
from pathlib import Path
import numpy as np
import tarfile,json,csv,argparse,math
p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def load(name):
    folder=a.input/name
    with tarfile.open(folder/'AUTHOR_NATIVE_SHORT.tar.gz','r:gz') as tf:
        z=[m for m in tf.getmembers() if m.name.endswith('.xyw')]
        assert len(z)==1,(name,len(z))
        lines=tf.extractfile(z[0]).read().decode(errors='replace').splitlines()
        data=[]
        for line in lines:
            try:
                tok=list(map(float,line.strip().split()[:3]))
                if len(tok)==3 and all(math.isfinite(v) for v in tok):data.append(tok)
            except ValueError:continue
        return np.asarray(data)
cases=[
 ('fixed default vs fixed explicit off','ebro_fixed_off','ebro_fixed_off_explicit'),
 ('fixed OFF vs original zero ion','ebro_fixed_off','ebro_orig_zero_ions'),
 ('fixed salt ON vs original ON Ebro','ebro_fixed_on','ebro_orig_on'),
 ('fixed salt ON vs original ON lake1','lake1_fixed_on','lake1_orig_on'),
 ('fixed salt ON vs original ON lake2','lake2_fixed_on','lake2_orig_on'),
 ('original salt OFF vs fixed OFF Ebro','ebro_orig_off','ebro_fixed_off'),
 ('original salt OFF vs fixed OFF lake1','lake1_orig_off','lake1_fixed_off'),
 ('original salt OFF vs fixed OFF lake2','lake2_orig_off','lake2_fixed_off')
]
res=[]
for label,ac,bc in cases:
    x,y=load(ac),load(bc)
    assert x.shape==y.shape,(ac,x.shape,bc,y.shape)
    e=x-y
    for c in range(3):
      assert np.isfinite(e[:,c]).all()
    m={'comparison':label,'case_A':ac,'case_B':bc,'nodes':len(x),
       'numpy_array_bitwise_equal':bool(np.array_equal(x,y)),
       'max_abs_first_coordinate_diff':float(np.max(np.abs(e[:,0]))),
       'max_abs_second_coordinate_diff':float(np.max(np.abs(e[:,1]))),
       'max_abs_third_column_diff':float(np.max(np.abs(e[:,2]))),
       'third_col_rms_diff':float(np.sqrt(np.mean(e[:,2]**2))),
       'third_col_median_absolute_diff':float(np.median(abs(e[:,2]))),
       'third_col_changed_cells_over_0_001':int((np.abs(e[:,2])>0.001).sum()),
       'third_col_changed_cells_over_1':int((np.abs(e[:,2])>1).sum()),
       'third_col_changed_cells_over_50':int((np.abs(e[:,2])>50).sum())}
    res.append(m)
    print('V08_NUMERICAL_ARRAY_DIFF',json.dumps(m))
with (a.out/'NUMERIC_NATIVE_GRID_COMPARISON.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(res[0]));w.writeheader();w.writerows(res)
(a.out/'NUMERIC_NATIVE_GRID_COMPARISON.json').write_text(json.dumps(res,indent=2))
(a.out/'NUMERIC_NATIVE_GRID_COMPARISON.md').write_text('# V08 independent native 14-run difference analysis\n\n'
  'The 3rd column of the original native author Ebro and lake .xyw is compared, not log maxima. '
  'This audit separates bytewise differences from numeric grid-field differences.\n\n'
  '| Contrast | Native points | Max abs difference col3 | RMS difference col3 | Different >1m |\n'
  '|---|---:|---:|---:|---:|\n'+''.join(
     '| '+v['comparison']+' | '+str(v['nodes'])+' | '+str(v['max_abs_third_column_diff'])+
     ' | '+str(v['third_col_rms_diff'])+' | '+str(v['third_col_changed_cells_over_1'])+' |\n'
     for v in res))
