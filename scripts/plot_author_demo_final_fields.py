#!/usr/bin/env python3
"""Generate scientific topography figure from unchanged original TISC demo .xyw.

This is modern reproducible plotting, NOT a re-execution of the author's
legacy GMT -Pc command. No interpolation is used; only native model points.
"""
from pathlib import Path
import argparse,tarfile,json,io,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

CASES={
 '04_river':('conic_island','conic_island.PRM'),
 '05_lake_one':('1lake','1lake.PRM'),
 '05_lakes_two':('2lakes','2lakes.PRM'),
 '06_tectonic':('demo','demo.PRM'),
 '07_climate':('sinusoidal','sinusoidal.PRM'),
 '08_ebro':('Ebro_evol','Ebro_evol.PRM'),
 '09_iberia':('Iberia_present','Iberia_present.PRM')
}

def read_params(src):
    p={}
    for line in src.decode(errors='replace').splitlines():
        w=line.strip().split()
        if len(w)>1 and not line.lstrip().startswith(('#','*')):
            p.setdefault(w[0],w[1])
    return p

def load_case(case,base):
    prefix,prm=CASES[case]
    src=base/case/(case+'_NATIVE_RAW.tar.gz')
    assert src.exists(),src
    with tarfile.open(src,'r:gz') as t:
        f=t.extractfile(prefix+'.xyw')
        assert f is not None
        data=np.loadtxt(io.BytesIO(f.read()),comments='#',usecols=(0,1,5))
        f=t.extractfile(prm)
        prmvalues=read_params(f.read())
    nx=int(prmvalues['Nx']);ny=int(prmvalues['Ny'])
    assert data.shape==(nx*ny,3),f'{case} native grid mismatch'
    assert np.isfinite(data).all(),f'{case} nonfinite original surface'
    x=np.unique(data[:,0]);y=np.unique(data[:,1])
    assert len(x)==nx and len(y)==ny,(case,len(x),len(y),nx,ny)
    # Grid cell positions are original TISC native model x/y. No invented DEM.
    ix=np.searchsorted(x,data[:,0]);iy=np.searchsorted(y,data[:,1])
    z=np.full((ny,nx),np.nan)
    z[iy,ix]=data[:,2]
    assert np.isfinite(z).all()
    return x,y,z,prmvalues,src

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    result=[]
    for case in CASES:
        x,y,z,p,src=load_case(case,args.input)
        fig,ax=plt.subplots(figsize=(9,6.6),layout='constrained')
        lo=float(np.min(z));hi=float(np.max(z))
        norm=TwoSlopeNorm(vmin=lo,vcenter=0,vmax=hi) if lo<0<hi else None
        im=ax.imshow(z,origin='lower',extent=(x[0],x[-1],y[0],y[-1]),
             cmap='terrain',norm=norm,aspect='auto')
        ax.set(title=f"Original author demo: {case} | final native TISC topography",
               xlabel="TISC model x (km)",ylabel="TISC model y (km)")
        c=fig.colorbar(im,ax=ax,shrink=.8);c.set_label('Final topographic elevation (m)')
        fig.text(.11,.015,
          "Original author model grids / modern plot (NOT author GMT -Pc). "
          "Source variant and full input hashes: original archive.",fontsize=8)
        fig.savefig(args.out/(case+'_FINAL_TOPOGRAPHY.png'),dpi=170)
        fig.savefig(args.out/(case+'_FINAL_TOPOGRAPHY.pdf'))
        plt.close(fig)
        row={'case':case,'grid_Nx':z.shape[1],'grid_Ny':z.shape[0],
             'native_topography_min_m':lo,'native_topography_max_m':hi,
             'native_grid_cells':int(z.size),'native_archive':src.name,
             'rendered_from_native_xyw':True,
             'not_upstream_legacy_GMT':True}
        result.append(row)
        print('AUTHOR_PLOT_QC',json.dumps(row))
    with (args.out/'FIGURE_SOURCE_AND_LIMITS.json').open('w') as f:
        json.dump(result,f,indent=2)
    with (args.out/'FIGURE_CONTENTS.md').open('w') as f:
        f.write("# Original author demonstration — final native topography figures\n\n"
          "All 7 panels are generated from original author TISC .xyw output, without modifying "
          "geophysical inputs or running TISC again. These are **modern Matplotlib visualizations**, "
          "not the historical GMT -Pc output. The seven distinct model extents must not be treated as "
          "geographically co-located, nor should the model-specific min/max be used as a common scale.\n\n"
          "Each figure has both PNG and vector PDF versions and a native-grid QC JSON. "
          "This is strictly the final landscape, not time-slice drainage, geological isopach or full history.\n")
if __name__=='__main__':main()
