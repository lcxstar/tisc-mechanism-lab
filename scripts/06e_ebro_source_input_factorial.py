#!/usr/bin/env python3
"""Factorial separation of historical TISC source vs old/new example input."""
from pathlib import Path
import argparse,subprocess,shutil,os,time,tarfile,hashlib,json,runpy,csv

def sha(f):
    return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser()
    for name in ('old-src','new-src','old-input','new-input','audit-script','out','work'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();a.work.mkdir(parents=True,exist_ok=True);a.out.mkdir(parents=True,exist_ok=True)
    fields=runpy.run_path(str(a.audit_script))['fields']
    hist=fields((a.old_input/'Ebro_evol.screen').read_text(errors='replace'))
    variants=[
      ('OLD2017_SOURCE__OLD2017_INPUT',a.old_src,a.old_input,[]),
      ('OLD2017_SOURCE__NEW2026_INPUT',a.old_src,a.new_input,[]),
      ('NEW2026_SOURCE__OLD2017_INPUT',a.new_src,a.old_input,[]),
      ('NEW2026_SOURCE__NEW2026_INPUT',a.new_src,a.new_input,[]),
      ('NEW2026_SOURCE__OLD2017_INPUT_AS_DEN3250',a.new_src,a.old_input,['-qdensasthen=3250']),
    ]
    report=[]
    for name,source,inp,extra in variants:
        w=a.work/name
        shutil.copytree(inp,w,dirs_exist_ok=True)
        if name.startswith('OLD2017'):exe=source/'bin/tisc'
        else:exe=source/'bin/tisc'
        assert exe.exists()
        command=[str(exe.resolve()),'Ebro_evol','-tf-59','-P0','-V1']+extra
        start=time.monotonic()
        try:
            result=subprocess.run(command,cwd=w,timeout=600,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                    env=os.environ|{'tisc_dir':str(source.resolve())+'/'})
            ec=result.returncode;data=result.stdout.decode(errors='replace')
        except subprocess.TimeoutExpired as e:
            ec=124;data=(e.stdout or b'').decode(errors='replace')+'\nTIMEOUT\n'
        (w/'RUN.log').write_text(data)
        (w/'COMMAND.txt').write_text(' '.join(command)+'\n')
        (w/'EXIT_CODE.txt').write_text(str(ec)+'\n')
        log=fields(data)
        old=hist.get(-59.5,{})
        now=log.get(-59.5,{})
        row={'case':name,
             'source':'old2017' if source==a.old_src else 'new2026',
             'input':'old2017' if inp==a.old_input else 'new2026',
             'source_exact_2016_binary':False,
             'source_no_algorithms_patched':True,
             'source_build_compatibility_only':True,
             'original_data_dir_sha256':{f.name:sha(f) for f in inp.iterdir() if f.suffix in ('.PRM','.UNIT','.ZINI','.SLV')},
             'compiled_executable_sha256':sha(exe),
             'command':command[1:],
             'exit_code':ec,
             'wall_seconds':round(time.monotonic()-start,3),
             'ages':sorted(log),
             'firststep_topography_max_m':now.get('topography_max_m'),
             'firststep_load_max_pa':now.get('load_now_max_pa'),
             'firststep_load_total_N':now.get('load_now_total_N'),
             'firststep_deflection_max_m':now.get('deflection_max_m'),
             'firststep_sediment_volume_km3':now.get('sediment_volume_km3'),
             'historical_2016_topography_max_m':old.get('topography_max_m'),
             'topography_deviation_from_2016_m':
                  now.get('topography_max_m')-old.get('topography_max_m') if now.get('topography_max_m') is not None else None,
             'original_2017_source_is_precise_2016_solver':False,
             'only_first_half_Myr_audited':True,
             'numerical_success':bool(ec==0 and now.get('topography_max_m') is not None)}
        d=a.out/name;d.mkdir(parents=True,exist_ok=True)
        with tarfile.open(d/'NATIVE_SOURCE_INPUT_EARLY.tar.gz','w:gz',compresslevel=3) as z:
            for f in w.iterdir():
                if f.is_file() and (f.name in ('RUN.log','COMMAND.txt','EXIT_CODE.txt') or
                      f.suffix in ('.PRM','.UNIT','.ZINI','.SLV','.hrz','.all','.xyzt','.xyw','.bas','.st','.lak')):
                      z.add(f,arcname=f.name)
        (d/'FACTORIAL_RUN_QC.json').write_text(json.dumps(row,indent=2))
        (d/'RUN.log').write_text(data)
        (d/'ARCHIVE_SHA256.txt').write_text(sha(d/'NATIVE_SOURCE_INPUT_EARLY.tar.gz')+'  NATIVE_SOURCE_INPUT_EARLY.tar.gz\n')
        report.append(row)
        print('EBRO_FACTORIAL_SOURCE_INPUT',name,'code',ec,'topography',row['firststep_topography_max_m'],
              'loadMPa',now.get('load_now_max_pa'),flush=True)
    with (a.out/'FACTORIAL_COMPARISON.csv').open('w',newline='') as f:
        keys=[k for k in report[0] if k not in ('original_data_dir_sha256','command','ages')]
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
        for row in report:writer.writerow({k:row.get(k) for k in keys})
    refs={r['case']:r for r in report}
    def diff(a,b,key='firststep_topography_max_m'):
        x,y=refs[a].get(key),refs[b].get(key)
        return None if x is None or y is None else x-y
    contrasts={
     'version_change_fixed_old_input_m':diff('NEW2026_SOURCE__OLD2017_INPUT','OLD2017_SOURCE__OLD2017_INPUT'),
     'version_change_fixed_new_input_m':diff('NEW2026_SOURCE__NEW2026_INPUT','OLD2017_SOURCE__NEW2026_INPUT'),
     'input_change_fixed_old_solver_m':diff('OLD2017_SOURCE__NEW2026_INPUT','OLD2017_SOURCE__OLD2017_INPUT'),
     'input_change_fixed_new_solver_m':diff('NEW2026_SOURCE__NEW2026_INPUT','NEW2026_SOURCE__OLD2017_INPUT'),
     'asthenosphere_density_default_fixed_2026_source_old_input_m':diff('NEW2026_SOURCE__OLD2017_INPUT_AS_DEN3250','NEW2026_SOURCE__OLD2017_INPUT'),
    }
    summary={'historical_reference':'Ebro_evol.screen TISC_2016-08-30',
       'old_source':'danigeos/tisc@38c63ab5bacf2045530160ba8e41ae0071a04065 2017-04-20',
       'new_source':'danigeos/tisc@d18b7d270f4d671b80223e10dede329ad35cafdd 2026-03',
       'no_real_geological_input_overwrite':True,'tests':report,
       'factorial_topography_contrasts':contrasts,
       'all_success':all(r['numerical_success'] for r in report)}
    (a.out/'FACTORIAL_SUMMARY.json').write_text(json.dumps(summary,indent=2))
    markdown=['# Source-version × input-version factorial first-step audit','',
        'Historic Ebro reference is Nov 2016 TISC screen output. Our archived earliest available runnable solver is April 2017, not identical 2016 binary.',
        '2017 original input is 104×55, dt_eros=0.025 Myr; 2026 input is 208×110, dt_eros=0.05 Myr.',
        '',
        '| Case | -59.5 Ma max topo (m) | max load (MPa) | max deflection (m) | Exit |',
        '|---|---:|---:|---:|---:|']
    for r in report:
        load=r['firststep_load_max_pa']
        markdown.append('| '+r['case']+' | '+str(r['firststep_topography_max_m'])+
              ' | '+(str(round(load/1e6,3)) if load is not None else 'N/A')+
              ' | '+str(r['firststep_deflection_max_m'])+
              ' | '+str(r['exit_code'])+' |')
    markdown+=['','## Controlled contrasts','']
    markdown +=['- '+k+': '+str(v)+' m' for k,v in contrasts.items()]
    markdown+=['','No experimental model was calibrated to the historical 2016 log. Every native first-window model output and original input is archived under its own case.']
    (a.out/'FACTORIAL_SUMMARY.md').write_text('\n'.join(markdown)+'\n')
    if not all(r['numerical_success'] for r in report):raise SystemExit('Some source/input combinations did not complete. See raw logs in permanent results for proof, no inferred PASS.')
if __name__=='__main__':main()
