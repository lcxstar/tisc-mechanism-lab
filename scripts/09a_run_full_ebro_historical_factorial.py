#!/usr/bin/env python3
"""Run one complete -60--0 Ma historic/Ebro source x input combination.

One GitHub job per case. Each job archives precisely the original author files,
native TISC grids, complete stdout and the actual compiled source SHA256.
No geological parameter updates and no geological model tuning.
"""
from pathlib import Path
import argparse,csv,hashlib,json,math,os,subprocess,tarfile,time,sys,shutil,runpy

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

ap=argparse.ArgumentParser()
ap.add_argument('--source',choices=['old2017','new2026'],required=True)
ap.add_argument('--input',choices=['old2017','new2026'],required=True)
ap.add_argument('--old-root',type=Path,required=True)
ap.add_argument('--new-root',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
ap.add_argument('--work',type=Path,required=True)
ap.add_argument('--parser',type=Path,required=True)
ap.add_argument('--timeout-seconds',type=int,default=4900)
a=ap.parse_args()
a.out.mkdir(parents=True,exist_ok=True)
src=(a.old_root if a.source=='old2017' else a.new_root).resolve()
inp=(a.old_root/'demo/8_Ebro_evol' if a.input=='old2017' else a.new_root/'tisc/demo/8_Ebro_evol').resolve()
exe=(src/'bin/tisc').resolve()
assert exe.exists() and inp.exists()
if a.work.exists():shutil.rmtree(a.work)
shutil.copytree(inp,a.work)
fileexts={'.PRM','.UNIT','.ZINI','.SLV','.INT','.INT2','.PRFL','.REC','.EET'}
input_checksums={f.name:sha(f) for f in inp.iterdir() if f.is_file() and f.suffix in fileexts}
assert input_checksums and input_checksums=={f.name:sha(f) for f in a.work.iterdir() if f.is_file() and f.suffix in fileexts}
args=['-P0','-V1'] if a.source=='old2017' else ['-V1','-qplotting_mode=0']
cmd=[str(exe),'Ebro_evol']+args
(a.work/'ACTUAL_COMMAND.txt').write_text(' '.join(cmd)+'\n')
beg=time.monotonic()
try:
    s=subprocess.run(cmd,cwd=a.work,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
       timeout=a.timeout_seconds,env=os.environ|{'tisc_dir':str(src)+'/'})
    rc=s.returncode;output=s.stdout.decode(errors='replace')
except subprocess.TimeoutExpired as e:
    rc=124;output=(e.stdout or b'').decode(errors='replace')+'\nEXPLICIT_TIMEOUT\n'
(a.work/'RUN.log').write_text(output)
(a.work/'EXIT_CODE.txt').write_text(str(rc)+'\n')
(a.work/'WALL_SECONDS.txt').write_text(str(round(time.monotonic()-beg,3))+'\n')
fields=runpy.run_path(str(a.parser))['fields']
stages=fields(output)
ages=sorted(stages)
native=a.work/'Ebro_evol.xyw'
points=0;zranges=[float('inf'),-float('inf')]
if native.exists():
    for line in native.read_text(errors='replace').splitlines():
        q=line.split()
        if len(q)<3:continue
        try:x,y,z=map(float,q[:3])
        except ValueError:continue
        if all(map(math.isfinite,(x,y,z))):
            points+=1;zranges[0]=min(z,zranges[0]);zranges[1]=max(z,zranges[1])
parameters={}
for line in (a.work/'Ebro_evol.PRM').read_text().splitlines():
    line=line.strip()
    if line.startswith('#') or not line:continue
    q=line.split()
    if len(q)>1:parameters[q[0]]=q[1]
expected=int(parameters['Nx'])*int(parameters['Ny'])
qc={
 'case':a.source+'__'+a.input,
 'source_version':'original 2017 C, git-pinned run-specific' if a.source=='old2017' else 'current 2026 C + V08 salt mode minimal guard',
 'source_commit':subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip(),
 'source_03t_optimized':False,
 'source_original_filename':'src/surf_proc.c' if a.source=='old2017' else 'tisc/src/surf_proc.c',
 'input_version':a.input,'original_demo_input_folder':str(inp),
 'original_demo_file_hashes':input_checksums,
 'original_author_model_files_changed':False,
 'actual_command':cmd,
 'binary_sha256':sha(exe),
 'process_exit_code':rc,
 'full_times':ages,
 'printed_time_count':len(ages),
 'printed_time_min':min(ages) if ages else None,
 'printed_time_max':max(ages) if ages else None,
 'input_Nx':int(parameters['Nx']),'input_Ny':int(parameters['Ny']),
 'input_dt_eros':parameters['dt_eros'],
 'native_output_nodes':points,'expected_nodes':expected,
 'native_z_minmax_m':zranges if points else None,
 'native_xyw_sha256':sha(native) if native.exists() else None,
 'key_log_values':{str(age):stages.get(age,{}) for age in [-60.,-59.5,-50.,-35.,-30.,-20.,-10.,-0.5]},
 'full_pass':bool(rc==0 and len(ages)>=120 and ages[0]==-60 and
       any(abs(t)<1e-6 for t in ages) and points==expected),
 'historical_2016_numerical_equality_claimed':False}
archive=a.out/'EBRO_FULL60_ORIGINAL_NATIVE.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=4) as tf:
 for f in sorted(a.work.iterdir()):
  if f.is_file() and (f.suffix in fileexts.union({'.xyw','.xyzt','.bas','.lak','.st','.hrz','.pfl'})
          or f.name in {'RUN.log','ACTUAL_COMMAND.txt','EXIT_CODE.txt','WALL_SECONDS.txt'}):
   tf.add(f,arcname=f.name)
qc['native_tar_sha256']=sha(archive)
qc['native_tar_size_bytes']=archive.stat().st_size
(a.out/'FULL_RUN_QC.json').write_text(json.dumps(qc,indent=2))
(a.out/'RUN.log').write_text(output)
(a.out/'INPUT_SHA256.json').write_text(json.dumps(input_checksums,indent=2))
(a.out/'SAVED_NATIVE_SHA256.txt').write_text(qc['native_tar_sha256']+'  EBRO_FULL60_ORIGINAL_NATIVE.tar.gz\n')
with (a.out/'FULL60_EACH_AGE_PHYSICAL_METRICS.csv').open('w',newline='') as f:
 fieldnames=['age_Ma','topography_max_m','topography_min_m','load_now_max_pa','load_now_total_N','deflection_max_m','deflection_min_m','sediment_volume_km3','erosion_without_sediment_N','sediment_increment_N','export_sediment_N']
 w=csv.DictWriter(f,fieldnames=fieldnames);w.writeheader()
 for age in ages:
  raw=stages[age]
  w.writerow({'age_Ma':age,**{k:raw.get(k) for k in fieldnames if k!='age_Ma'}})
print('V09_FULL_CASE_QC',json.dumps({k:qc[k] for k in
 ('case','source_version','process_exit_code','printed_time_count','native_output_nodes','native_tar_size_bytes','full_pass','key_log_values')})[:5500])
if not qc['full_pass']:sys.exit(1)
