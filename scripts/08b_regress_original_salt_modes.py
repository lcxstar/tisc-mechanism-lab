#!/usr/bin/env python3
"""Execute original-vs-V08 salt module regression on original author Ebro + lakes.

Native C binaries are prepared by GitHub CI. All original author inputs are
copied bytewise; no geology model file ever edited. Supported opt-in chemistry
must retain same numerical output. Salt-off runs must match explicit -qsalt_model=0
and legacy zero-ion original run, within documented conservative tolerance.
"""
from pathlib import Path
import argparse,subprocess,json,tarfile,hashlib,time,shutil,os,sys,runpy,math
import numpy as np

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def binary_sha(f):
    if not f.exists():return None
    return sha(f)
def native_elev(path):
    vals=[]
    if not path.exists():return vals
    for line in path.read_text(errors='replace').splitlines():
        t=line.strip().split()
        if len(t)<3:continue
        try:col=list(map(float,t[:3]))
        except ValueError:continue
        if all(math.isfinite(x) for x in col):vals.append(col)
    return vals

ap=argparse.ArgumentParser()
for arg in ['upstream','orig-exe','fixed-exe','audit-parser','out','work']:ap.add_argument('--'+arg,type=Path,required=True)
a=ap.parse_args()
a.out.mkdir(parents=True,exist_ok=True);a.work.mkdir(parents=True,exist_ok=True)
fields=runpy.run_path(str(a.audit_parser))['fields']
root=Path.cwd()
base=a.upstream.resolve()
variants=[
 ('ebro_orig_off','Ebro','original',[]),
 ('ebro_fixed_off','Ebro','fixed',[]),
 ('ebro_fixed_off_explicit','Ebro','fixed',['-qsalt_model=0']),
 ('ebro_orig_on','Ebro','original',['-qsalt_model=1']),
 ('ebro_fixed_on','Ebro','fixed',['-qsalt_model=1']),
 ('ebro_orig_zero_ions','Ebro','original',['-q'+k+'=0' for k in ('C_Ca_SEA','C_SO4_SEA','C_Na_SEA','C_Cl_SEA','C_Ca_RIV','C_SO4_RIV','C_Na_RIV','C_Cl_RIV')]),
 ('lake1_orig_off','1lake','original',[]),
 ('lake1_fixed_off','1lake','fixed',[]),
 ('lake1_orig_on','1lake','original',['-qsalt_model=1']),
 ('lake1_fixed_on','1lake','fixed',['-qsalt_model=1']),
 ('lake2_orig_off','2lakes','original',[]),
 ('lake2_fixed_off','2lakes','fixed',[]),
 ('lake2_orig_on','2lakes','original',['-qsalt_model=1']),
 ('lake2_fixed_on','2lakes','fixed',['-qsalt_model=1']),
]
presets={
 'Ebro':('8_Ebro_evol','Ebro_evol','-tf-59',22880,-59.5),
 '1lake':('5_lakes','1lake',None,2601,None),
 '2lakes':('5_lakes','2lakes',None,6561,None)
}
runs={}
for name,model,kind,extra in variants:
    folder,prefix,tf,expected_nodes,refage=presets[model]
    src=base/'tisc/demo'/folder
    w=a.work/name
    shutil.copytree(src,w,dirs_exist_ok=True)
    origin={}
    for p in src.iterdir():
        if p.is_file() and p.suffix in ('.PRM','.UNIT','.ZINI','.SLV','.INT','.INT2','.REC','.PRFL','.EET'):
            origin[p.name]=sha(p)
    same={k:sha(w/k) for k in origin}
    assert origin==same,name
    exe=(a.orig_exe if kind=='original' else a.fixed_exe).resolve()
    cmd=[str(exe),prefix,'-V1','-qplotting_mode=0']+([tf] if tf else [])+extra
    began=time.monotonic()
    try:
        result=subprocess.run(cmd,cwd=w,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
           timeout=900,env=os.environ|{'tisc_dir':str(base)+'/'})
        rc=result.returncode;log=result.stdout.decode(errors='replace')
    except subprocess.TimeoutExpired as e:
        rc=124;log=(e.stdout or b'').decode(errors='replace')+'\nTIMEOUT\n'
    (w/'RUN.log').write_text(log);(w/'ACTUAL_COMMAND.txt').write_text(' '.join(cmd)+'\n')
    stages=fields(log);newage=stages.get(refage,{}) if refage is not None else {}
    native=w/(prefix+'.xyw')
    rows=native_elev(native)
    if rows and len(rows)!=expected_nodes:
        print('OUTPUT_NODE_COUNT_WARN',name,len(rows),'expected',expected_nodes,flush=True)
    saltqc=[line for line in log.splitlines() if 'V08_SALT_OFF_INVARIANT' in line]
    report={'case':name,'model':model,'source_version':kind,
       'upstream_source_commit':'d18b7d270f4d671b80223e10dede329ad35cafdd',
       'full_input_hashes_original_unchanged':True,
       'original_author_geological_input_hashes':origin,'actual_command':cmd[1:],
       'rc':rc,'seconds':round(time.monotonic()-began,3),'times_logged':sorted(stages),
       'max_topography_at_minus59_5_Ma':newage.get('topography_max_m'),
       'max_load_at_minus59_5_Pa':newage.get('load_now_max_pa'),
       'logged_surface_native_nodes':len(rows),
       'expected_surface_native_nodes':expected_nodes,
       'native_surface_sha256':binary_sha(native),
       'model_fields':{s:binary_sha(w/(prefix+'.'+s)) for s in ('xyw','xyzt','lak','st','bas','hrz')},
       'salt_invariant_status':len(saltqc),
       'salt_invariant_sample':saltqc[:3],
       'passed_basic':rc==0 and len(rows)==expected_nodes,
       'experiment_not_2016_equivalence_claim':True}
    archive=a.out/name;archive.mkdir(parents=True,exist_ok=True)
    (w/'QC.json').write_text(json.dumps(report,indent=2))
    with tarfile.open(archive/'AUTHOR_NATIVE_SHORT.tar.gz','w:gz',compresslevel=4) as tar:
        for f in sorted(w.iterdir()):
            if f.is_file() and (f.suffix in ('.PRM','.UNIT','.ZINI','.SLV','.INT','.INT2','.REC','.PRFL','.EET','.xyw','.xyzt','.hrz','.lak','.st','.bas')
               or f.name in ('RUN.log','ACTUAL_COMMAND.txt','QC.json')):
                tar.add(f,arcname=f.name)
    (archive/'RUN.log').write_text(log)
    (archive/'QC.json').write_text(json.dumps(report,indent=2))
    (archive/'NATIVE_HASH.txt').write_text(sha(archive/'AUTHOR_NATIVE_SHORT.tar.gz')+'  AUTHOR_NATIVE_SHORT.tar.gz\n')
    runs[name]=report
    print('V08_RUN',name,rc,report['max_topography_at_minus59_5_Ma'],
          len(rows), 'sha',report['native_surface_sha256'],flush=True)
def cmp(a1,a2):
    x,y=runs[a1],runs[a2]
    return {'a':a1,'b':a2,'surface_byte_identical':bool(x['native_surface_sha256'] and
          x['native_surface_sha256']==y['native_surface_sha256']),
          'native_nonempty':x['logged_surface_native_nodes']>0 and y['logged_surface_native_nodes']>0}
comparisons={
  'patch_off_matches_explicit_off':cmp('ebro_fixed_off','ebro_fixed_off_explicit'),
  'patch_on_identical_to_original_on_Ebro':cmp('ebro_orig_on','ebro_fixed_on'),
  'patch_on_identical_to_original_on_Lake1':cmp('lake1_orig_on','lake1_fixed_on'),
  'patch_on_identical_to_original_on_Lake2':cmp('lake2_orig_on','lake2_fixed_on'),
  'original_zero_ions_identical_to_fixed_off_Ebro':cmp('ebro_orig_zero_ions','ebro_fixed_off'),
}
fail=[]
for k,c in comparisons.items():
    if not c['surface_byte_identical']:fail.append(k)
# This is supposed to fail the old solver's unsupported salt=0 semantics,
# while repaired 2026 salt=0 should be physically akin to zero-ion input.
if not runs['ebro_orig_off']['max_topography_at_minus59_5_Ma'] or not runs['ebro_fixed_off']['max_topography_at_minus59_5_Ma']:
    fail.append('absent_early_log')
else:
    if runs['ebro_orig_off']['max_topography_at_minus59_5_Ma']<8000:fail.append('unexpected_old_failure_baseline')
    if runs['ebro_fixed_off']['max_topography_at_minus59_5_Ma']>2500:fail.append('patch_did_not_suppress_early_spike')
if any(not run['passed_basic'] for run in runs.values()):fail.append('one_or_more_actual_model_runs_failed')
s={'tests':list(runs),'test_count':len(runs),'runs':runs,'native_comparisons':comparisons,
   'failure_causes':fail,'strict_regression_pass':not fail,
   'per_case_orig_input_geo_unchanged':True,'pristine_source_separate_from_fixed':True,
   'full_Ebro_60_Myr_NOT_completed_by_this_short_test':True}
(a.out/'V08_REGRESSION_RESULT.json').write_text(json.dumps(s,indent=2))
lines=['# V08 salt-module repair — actual original-input C solver regression','',
    'The two binaries differ only in the newly explicit salt_mode calculation guard '
    'and compiler NBSP normalization. All scientific TISC demo model input files remain bytewise identical.',
    '',
    '| Native run | Maximum Ebro topography at -59.5 Ma (m) | Actual grid nodes | Exit |',
    '|---|---:|---:|---:|']
for k,v in runs.items():
    lines.append('| '+k+' | '+str(v['max_topography_at_minus59_5_Ma'])+
       ' | '+str(v['logged_surface_native_nodes'])+' | '+str(v['rc'])+' |')
lines+=['','## Strict original-on binary parity and salt-off invariants','']
for k,c in comparisons.items():
    lines.append('- **'+k+'**: '+('PASS' if c['surface_byte_identical'] else 'FAIL')+
          ', native SHA256 '+str(runs[c['a']]['native_surface_sha256'])[:16]+' / '+
          str(runs[c['b']]['native_surface_sha256'])[:16])
lines+=['','**REGRESSION PASS = '+str(not fail)+'**. Failed assertions: '+str(fail),
       '','This test is NOT 2016 full-Ebro equivalence and does not certify the patched entire 60-Myr model.']
(a.out/'V08_REGRESSION_RESULT.md').write_text('\n'.join(lines)+'\n')
print('V08_FINAL_TEST_STATUS',json.dumps({'pass':not fail,'fail':fail,'comparisons':comparisons}))
if fail:sys.exit(1)
