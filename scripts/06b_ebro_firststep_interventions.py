#!/usr/bin/env python3
"""Run exact pinned Ebro first 0.5 Myr with 9 isolated cause interventions.

Historical author's original input folder is copied exactly per variant before
optional explicit intervention. Baseline is never changed. All current runs use
ONLY NBSP compile normalization, not 03t slope/transport/precision patches.
"""
from pathlib import Path
import argparse,subprocess,json,hashlib,re,tarfile,csv,shutil,time,sys,runpy

CASES={
 "00_clean_source_baseline": {"opts":[]},
 "01_Te_25km": {"opts":["-qTe=25000"]},
 "02_asthenosphere_3250": {"opts":["-qdensasthen=3250"]},
 "03_Te25_rho3250": {"opts":["-qTe=25000","-qdensasthen=3250"]},
 "04_hydrology_erosion_off": {"opts":["-qhydro_model=0","-qerosed_model=0"]},
 "05_unit1_initial_velocity_zero": {"opts":[],"unit1_edit":("vel_y\t-3.2","vel_y\t0")},
 "06_defer_unit1_load_to_minus58": {"opts":[],"unit1_edit":("time_load\t-60","time_load\t-58")},
 "07_delay_all_tectonic_units": {"opts":[],"delay_all":True},
 "08_dt_005": {"opts":["-td0.05"]},
 "09_unit1_initial_ramp_thickness_1000m": {"opts":[],"unit1_edit":("10000\tn","1000\tn")}
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def original_hashes(d):
    return {f.name:sha(f) for f in d.iterdir() if f.is_file() and f.suffix in ('.PRM','.UNIT','.ZINI','.SLV','.INT','.REC','.PRFL','.INT2')}
def exact_replace(path,old,new):
    src=path.read_text()
    assert src.count(old)==1,(path.name,old,src.count(old))
    path.write_text(src.replace(old,new,1))
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--upstream-input',type=Path,required=True)
    ap.add_argument('--tisc-executable',type=Path,required=True)
    ap.add_argument('--tisc-root',type=Path,required=True)
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--script-audit',type=Path,required=True)
    a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);a.work.mkdir(parents=True,exist_ok=True)
    assert a.tisc_executable.exists()
    original=original_hashes(a.upstream_input)
    parsers=runpy.run_path(str(a.script_audit));read_fields=parsers['fields']
    ref=read_fields((a.upstream_input/'Ebro_evol.screen').read_text(errors='replace'))
    records=[]
    for name,control in CASES.items():
        w=a.work/name;shutil.copytree(a.upstream_input,w,dirs_exist_ok=True)
        assert original_hashes(w)==original,'Upstream source differed before intervention'
        if 'unit1_edit' in control:
            f=w/'Ebro_evol1.UNIT'
            exact_replace(f,*control['unit1_edit'])
        if control.get('delay_all'):
            for n in range(1,6):
                f=w/f'Ebro_evol{n}.UNIT'
                src=f.read_text()
                src,nchanges=re.subn(r'(?m)^(time_load\s+)(-?\d+(?:\.\d+)?)',r'\g<1>-57',src,count=1)
                assert nchanges==1
                f.write_text(src)
        after=original_hashes(w)
        changed_files=[k for k in original if after[k]!=original[k]]
        cmd=[str(a.tisc_executable.resolve()),'Ebro_evol','-tf-59','-V1','-qplotting_mode=0']+control['opts']
        (w/'ACTUAL_COMMAND.txt').write_text(' '.join(cmd)+'\n')
        start=time.monotonic()
        try:
            proc=subprocess.run(cmd,cwd=w,timeout=360,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                env=__import__('os').environ|{'tisc_dir':str(a.tisc_root.resolve())+'/'})
            rc=proc.returncode;output=proc.stdout.decode('utf-8',errors='replace')
        except subprocess.TimeoutExpired as e:
            rc=124;output=(e.stdout or b'').decode(errors='replace')+'\nTIMEOUT\n'
        (w/'RUN.log').write_text(output)
        age=read_fields(output)
        at=age.get(-59.5,{})
        init=age.get(-60,{})
        result={'case':name,'correctly_pristine_source_except_nbsp':True,
                'original_input_sha256':original,
                'changed_original_input_names':changed_files,
                'changed_original_input_before_after_sha256':{k:[original[k],after[k]] for k in changed_files},
                'CLI':cmd[1:],
                'exit_code':rc,'wall_seconds':round(time.monotonic()-start,2),
                'ages_recorded':sorted(age),
                'initial_topography_max_m':init.get('topography_max_m'),
                'firststep_topography_max_m':at.get('topography_max_m'),
                'firststep_topography_max_difference_vs_2016_m':at.get('topography_max_m')-ref[-59.5]['topography_max_m'] if at.get('topography_max_m') is not None else None,
                'firststep_load_max_pa':at.get('load_now_max_pa'),
                'firststep_load_total_N':at.get('load_now_total_N'),
                'firststep_deflection_max_m':at.get('deflection_max_m'),
                'firststep_sediment_vol_km3':at.get('sediment_volume_km3'),
                'historical_2016_topography_max_m':ref[-59.5]['topography_max_m'],
                'historical_2016_load_max_pa':ref[-59.5]['load_now_max_pa'],
                'historical_2016_deflection_max_m':ref[-59.5]['deflection_max_m'],
                'full_window_final_60Myr_not_executed':True}
        result['numerical_pass']=bool(rc==0 and -59.5 in age and
              at.get('topography_max_m') is not None)
        (w/'FIRSTSTEP_QC.json').write_text(json.dumps(result,indent=2))
        od=a.out/name;od.mkdir(parents=True,exist_ok=True)
        with tarfile.open(od/'NATIVE_SHORT_TISC.tar.gz','w:gz',compresslevel=3) as t:
            for f in sorted(w.iterdir()):
                if f.is_file() and (f.name in ('ACTUAL_COMMAND.txt','RUN.log','FIRSTSTEP_QC.json') or
                f.suffix in ('.PRM','.UNIT','.ZINI','.SLV','.INT','.INT2','.REC','.PRFL','.xyzt','.xyw','.hrz','.all','.bas','.lak','.st')):
                    t.add(f,arcname=f.name)
        (od/'FIRSTSTEP_QC.json').write_text(json.dumps(result,indent=2))
        (od/'RUN.log').write_text(output)
        (od/'NATIVE_SHORT_SHA256.txt').write_text(sha(od/'NATIVE_SHORT_TISC.tar.gz')+'  NATIVE_SHORT_TISC.tar.gz\n')
        records.append({k:v for k,v in result.items() if k not in ('original_input_sha256','changed_original_input_before_after_sha256')})
        print("INTERVENTION_RESULT",name,rc,at.get('topography_max_m'),at.get('load_now_max_pa'),
              at.get('load_now_total_N'),at.get('deflection_max_m'),flush=True)
    fields=list(records[0])
    with (a.out/'INTERVENTION_FIRSTSTEP_COMPARISON.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(records)
    summary={'upstream':'danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd',
             'source':'compiler NBSP normalized only, *NO 03t changes*',
             'run_time_window':'-60 to -59 Ma, output at -60 and -59.5 Ma',
             'original_author_demo_inputs_unmodified_on_baseline':True,
             'author_2016_firststep_max_m':ref[-59.5]['topography_max_m'],
             'runs':records,'all_numerical_pass':all(x['numerical_pass'] for x in records),
             'causality':'An intervention can show dependency, not reproduce unknown historical 2016 source implementation.'}
    (a.out/'INTERVENTION_SUMMARY.json').write_text(json.dumps(summary,indent=2))
    readme=['# First-step controlled intervention, original current TISC source only','',
        'This suite establishes what can directly change the first half-Myr Ebro response. '
        'Original demo inputs remain intact in the baseline. Every intervention receives its own copy; '
        'all edits and SHA256 changes are declared, without altering original repository examples.',
        '',
        '| Intervention | Final -59.5 Ma max topo (m) | 2016 difference (m) | load max (MPa) | max flexure (m) | PASS |',
        '|---|---:|---:|---:|---:|---|']
    for d in records:
        mx=d['firststep_load_max_pa']
        readme.append('| '+d['case']+' | '+str(d['firststep_topography_max_m'])+
          ' | '+str(d['firststep_topography_max_difference_vs_2016_m'])+
          ' | '+(str(round(mx/1e6,3)) if mx is not None else 'N/A')+
          ' | '+str(d['firststep_deflection_max_m'])+
          ' | '+str(d['numerical_pass'])+' |')
    readme+=['',
      'The recorded native log output is authoritative. Completion does NOT prove historical 2016 numerical equality.',
      'Controlling an input only identifies a sensitivity; matching 2016 needs its actual executable/source or matching diagnosed algorithmic path.',
      'Original source physics has NOT been modified beyond non-breaking space compiler normalization; not the 03t optimized baseline.',
      '']
    (a.out/'INTERVENTION_SUMMARY.md').write_text('\n'.join(readme))
    if not summary['all_numerical_pass']:sys.exit(1)
if __name__=='__main__':main()
