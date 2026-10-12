#!/usr/bin/env python3
"""Compare native Ebro -60 to 0 Ma model with author's no-surface option."""
import tarfile,json,csv,re,argparse,math
from pathlib import Path

def read_tar_text(path,name):
    with tarfile.open(path,'r:gz') as t:
        f=t.extractfile(name)
        assert f is not None
        return f.read().decode(errors='replace')

def snapshots(text):
    found=list(re.finditer(r"(?m)^\s*T=\s*([-+0-9.eE]+)\s*My",text))
    rec={}
    for i,m in enumerate(found):
        age=round(float(m.group(1)),6)
        fragment=text[m.end():(found[i+1].start() if i+1<len(found) else len(text))]
        p={}
        for k,r in {
            "surface_max_m":r"topogr\.\s*:\s*max=\s*([-+0-9.eE]+)",
            "surface_min_m":r"topogr\.\s*:\s*max=\s*[-+0-9.eE]+\s*m\s*min=\s*([-+0-9.eE]+)",
            "sediment_vol_km3":r"sediment_vol:\s*([-+0-9.eE]+)",
            "main_lake_vol_km3":r"lake\s+\d+/\d+\s*:\s*([-+0-9.eE]+)\s*km3",
        }.items():
            g=re.search(r,fragment);p[k]=float(g.group(1)) if g else None
        rec[age]=p
    return rec

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--baseline',type=Path,required=True)
    ap.add_argument('--no-surface',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    baseline=snapshots(read_tar_text(a.baseline,'RUN.log'))
    reduced=snapshots(read_tar_text(a.no_surface,'RUN.log'))
    ages=sorted(set(baseline)&set(reduced))
    assert len(ages)==121 and ages[0]==-60 and ages[-1]==0
    fields=('surface_max_m','surface_min_m','sediment_vol_km3','main_lake_vol_km3')
    rows=[]
    for age in ages:
        r={'age_Ma':age}
        for k in fields:
            x=baseline[age][k];y=reduced[age][k]
            r['full_'+k]=x;r['no_surface_'+k]=y
            r['difference_'+k]=y-x if x is not None and y is not None else None
        rows.append(r)
    with (a.out/'EBRO_WITH_VS_WITHOUT_SURFACE.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    report={'original_author_option':'-qerosed_model=0 -qhydro_model=0',
            'full_source':'author input 208x110 original -60--0Ma, audited 03t executable',
            'reduced_source':'identical original file inputs and executable, CLI disables hydrology and surface transport',
            'time_matched':len(ages),'original_age_Ma':ages[0],'end_age_Ma':ages[-1],
            'no_claim_of_historical_2016_agreement':True,
            'field_comparisons':{}}
    for k in fields:
        deviations=[r['difference_'+k] for r in rows if r['difference_'+k] is not None]
        report['field_comparisons'][k]={
            'matched':len(deviations),
            'mean_difference':sum(deviations)/len(deviations) if deviations else None,
            'maximum_abs_difference':max(map(abs,deviations)) if deviations else None,
            'last_comparable_full':next((r['full_'+k] for r in reversed(rows) if r['full_'+k] is not None),None),
            'last_comparable_no_surface':next((r['no_surface_'+k] for r in reversed(rows) if r['no_surface_'+k] is not None),None)}
    (a.out/'EBRO_SURFACE_OPTION_QC.json').write_text(json.dumps(report,indent=2))
    note=[
      '# Author Ebro demonstration: controlled hydrology/surface-off option',
      '',
      'Author-requested CLI option: -qerosed_model=0 -qhydro_model=0, all PRM/ZINI/UNIT unchanged.',
      'Original source variant is declared 03t audited; this is a same-source, same-geometry '
      'mechanism isolation, not an original 2016 historical geologic equality test.',
      '',
      '| Quantity | Full author-input model | With surface processes disabled | Max absolute paired change |',
      '|---|---:|---:|---:|']
    for k,x in report['field_comparisons'].items():
        note.append('| '+k+' | '+str(x['last_comparable_full'])+' | '+
                    str(x['last_comparable_no_surface'])+' | '+str(x['maximum_abs_difference'])+' |')
    note.extend(['','Full 121-stage data saved in EBRO_WITH_VS_WITHOUT_SURFACE.csv.','',''])
    (a.out/'EBRO_SURFACE_OPTION_QC.md').write_text('\n'.join(note))
    print('AUTHOR_EBRO_SURFACE_SWITCH_QC',json.dumps(report))
if __name__=='__main__':main()
