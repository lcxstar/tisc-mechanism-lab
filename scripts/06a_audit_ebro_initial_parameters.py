#!/usr/bin/env python3
"""Audit Ebro baseline 2016-v-current checkpoint and exact inherited parameters.

No model runs, no PRM edits, no historical-equivalence claims. Original logs are
read from the author source repo and the immutable v04 archived native tarball.
"""
from pathlib import Path
import argparse,tarfile,re,json,csv,hashlib

TIME=re.compile(r'(?m)^\s*T=\s*([-+]?\d+(?:\.\d+)?)\s*My')
NUM=r'([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)'
def fields(text):
    breaks=list(TIME.finditer(text))
    d={}
    for ix,m in enumerate(breaks):
        age=float(m.group(1))
        part=text[m.end():breaks[ix+1].start() if ix+1<len(breaks) else len(text)]
        d[age]={}
        for name,regex in {
          'topography_max_m':r'topogr\.\s*:\s*max=\s*'+NUM,
          'topography_min_m':r'topogr\.\s*:\s*max=\s*'+NUM+r'\s*m\s*min=\s*'+NUM,
          'load_now_max_pa':r'load\s+now:\s*max\s*=\s*'+NUM,
          'load_now_min_pa':r'load\s+now:\s*max\s*=\s*'+NUM+r'\s*N/m2\s*min\s*=\s*'+NUM,
          'load_now_total_N':r'load\s+now:.*?Total:\s*'+NUM,
          'deflection_max_m':r'deflect\.\s*:\s*max=\s*'+NUM,
          'deflection_min_m':r'deflect\.\s*:\s*max=\s*'+NUM+r'\s*m\s*min=\s*'+NUM,
          'rain_integrated':r'precipit\.\s*:\s*.*?integr=\s*'+NUM,
          'sediment_volume_km3':r'sediment_vol:\s*'+NUM,
          'erosion_without_sediment_N':r'eros_nosd:\s*'+NUM,
          'sediment_increment_N':r'sedim_inc:\s*'+NUM,
          'export_sediment_N':r'outp_seds:\s*'+NUM,
        }.items():
            f=re.search(regex,part)
            if name in ['topography_min_m','load_now_min_pa','deflection_min_m']:
                d[age][name]=float(f.group(2)) if f else None
            else:d[age][name]=float(f.group(1)) if f else None
    return d

def prm(text):
    obj={}
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line[0] in '#*>':continue
        w=line.split()
        if len(w)>1:obj[w[0]]=w[1]
    return obj

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--author-screen',type=Path,required=True)
    p.add_argument('--current-raw',type=Path,required=True)
    p.add_argument('--upstream-input-dir',type=Path,required=True)
    p.add_argument('--default-prm',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    historical=a.author_screen.read_text(errors='replace')
    with tarfile.open(a.current_raw,'r:gz') as t:
        current=t.extractfile('RUN.log').read().decode(errors='replace')
    h=fields(historical);c=fields(current)
    values=['topography_max_m','topography_min_m','load_now_max_pa','load_now_min_pa',
    'load_now_total_N','deflection_max_m','deflection_min_m','rain_integrated',
    'sediment_volume_km3','erosion_without_sediment_N','sediment_increment_N',
    'export_sediment_N']
    rows=[]
    for time in [-60.,-59.5,-59.,-58.5,-58.]:
        row={'age_Ma':time}
        for v in values:
            old=h.get(time,{}).get(v);new=c.get(time,{}).get(v)
            row[f'2016_{v}']=old;row[f'2026_{v}']=new
            row[f'2026_minus_2016_{v}']=(new-old if old is not None and new is not None else None)
        rows.append(row)
    with (a.out/'FIRST_FIVE_TIMES_STEPWISE_2016_VS_2026.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    user=prm((a.upstream_input_dir/'Ebro_evol.PRM').read_text())
    defaults=prm(a.default_prm.read_text())
    keys=['version','Nx','Ny','Timeini','Timefinal','dt','dt_eros','random_topo',
      'isost_model','Te','densmantle','densasthen','denscrust','denssedim',
      'rain','Krain','CXrain','CYrain','hydro_model','evaporation','erosed_model',
      'K_river_cap','erodability','erodibility','erodability_sed','erodibility_sed','l_fluv_sedim']
    params=[]
    for k in keys:
        k_effective={'erodability':'erodibility','erodability_sed':'erodibility_sed'}.get(k,k)
        source_val=user.get(k)
        is_legacy_alias=k in ['erodability','erodability_sed']
        params.append({
        'key':k,'value_in_author_demo_prm':source_val,
        '2026_template_default':defaults.get(k_effective),
        'effective_2026_value_source':('explicit demo PRM (legacy alias)' if is_legacy_alias else 'explicit demo PRM') if source_val is not None else 'inherited current source template',
        'effective_2026_value':source_val if source_val is not None else defaults.get(k_effective),
        'explicit_or_default':source_val is not None,
        })
    for n in range(1,6):
        f=a.upstream_input_dir/f'Ebro_evol{n}.UNIT'
        unit=prm(f.read_text())
        params.append({'key':f'UNIT_{n}','value_in_author_demo_prm':json.dumps({k:unit.get(k) for k in ('time_load','time_stop','vel_x','vel_y','fault_load','cut_all','dens_load')}),
        '2026_template_default':None,'effective_2026_value_source':f.name,'effective_2026_value':None,'explicit_or_default':True})
    with (a.out/'EFFECTIVE_INPUT_AND_DEFAULTS.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(params[0]));w.writeheader();w.writerows(params)
    no_eet=not any(a.upstream_input_dir.glob('Ebro_evol.EET'))
    audit={'author_old_version':'TISC_2016-08-30',
      'current_template_version':defaults.get('version'),
      'current_demo_Prm_version':user.get('version'),
      'grid':str(user.get('Nx'))+'x'+str(user.get('Ny')),
      'historical_log_times':len(h),'current_run_times':len(c),
      'author_zini_sha256':hashlib.sha256((a.upstream_input_dir/'Ebro_evol.ZINI').read_bytes()).hexdigest(),
      'no_EET_file_in_source':no_eet,
      'Te_in_Ebro_PRM':user.get('Te'),'current_inherited_Te_m':defaults.get('Te') if no_eet else None,
      'densmantle_explicit':user.get('densmantle'),
      'densasthen_explicit':user.get('densasthen'),
      'densasthen_inherited_default':defaults.get('densasthen'),
      'first_timestep_historic_load_N':h.get(-59.5,{}).get('load_now_total_N'),
      'first_timestep_modern_load_N':c.get(-59.5,{}).get('load_now_total_N'),
      'first_timestep_historic_deflection_max_m':h.get(-59.5,{}).get('deflection_max_m'),
      'first_timestep_modern_deflection_max_m':c.get(-59.5,{}).get('deflection_max_m'),
      'first_timestep_historic_topography_max_m':h.get(-59.5,{}).get('topography_max_m'),
      'first_timestep_modern_topography_max_m':c.get(-59.5,{}).get('topography_max_m'),
      'version_or_input_caused_firststep_divergence_proven':False,
      'report_sources':['Ebro_evol.screen historical version',
                        'v04/08_ebro/08_ebro_NATIVE_RAW.tar.gz / RUN.log',
                        'original GitHub Ebro PRM UNIT ZINI','2026 template.PRM']}
    (a.out/'INITIAL_CONDITION_DIAGNOSTICS.json').write_text(json.dumps(audit,indent=2))
    narrative=[
     '# Ebro original author screen versus pinned 2026 code — forensic early-time audit','',
     'The full -60 to 0 Myr original-input experiment was already completed in v04. '
     'This independent read-only audit extracts the TISC native load, flexure, '
     'sediment and topography outputs rather than comparing only global maximum topography.',
     '',
     '| TISC diagnostic | Author 2016 at -59.5 Ma | Pinned 2026 at -59.5 Ma |']
    for k in ['topography_max_m','load_now_max_pa','load_now_total_N','deflection_max_m',
         'deflection_min_m','rain_integrated','sediment_volume_km3']:
        narrative.append('| '+k+' | '+str(h.get(-59.5,{}).get(k))+
          ' | '+str(c.get(-59.5,{}).get(k))+' |')
    narrative+=['','## Inherited 2026 defaults and source flags','',
      '- Model PRM version header is '+str(user.get('version'))+'; current template is '+str(defaults.get('version'))+'.',
      '- The demo contains no Te line and '+('no EET input' if no_eet else 'an EET file')+'. The current template defaults to '+str(defaults.get('Te'))+' m.',
      '- densmantle='+str(user.get('densmantle'))+' is distinct from densasthen; current inherited densasthen='+str(defaults.get('densasthen'))+' kg/m³.',
      '- The input parameter matrix distinguishes explicitly provided values from inherited current-template defaults. It is not a reconstruction of the original unavailable 2016 template.',
      '- Because the 2016 binary and exact runtime default file are not archived, input versus solver version causation cannot be inferred without controlled interventions.',
      '','## Evidence','',
      '- FIRST_FIVE_TIMES_STEPWISE_2016_VS_2026.csv — 12 source-calculated physical diagnostics at first five ages.',
      '- EFFECTIVE_INPUT_AND_DEFAULTS.csv — frozen PRM, 2026 template defaults, five original kinematic UNIT parameter heads.',
      '- INITIAL_CONDITION_DIAGNOSTICS.json — specific observed first-step difference without any claim of proof of mechanism.',
      '']
    (a.out/'INITIAL_CONDITION_AND_VERSION_AUDIT.md').write_text('\n'.join(narrative))
    print(json.dumps(audit,indent=2))
    assert len(h)==121 and len(c)==121
if __name__=='__main__':main()
