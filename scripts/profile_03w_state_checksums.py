#!/usr/bin/env python3
"""03w only-observational checksum of raw float state after each erosion substep.

Unlike rounded .xyw, hashes detect the FIRST bit-level change of native float
terrain, sediment top Block, deflection and drainage graph.  Both executables
get the exact SAME observer; local dh_sed type is the only code difference.
"""
from pathlib import Path
import hashlib,json,difflib,sys
def once(s,old,new,tag):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"03w source anchor {tag} count={n}")
    return s.replace(old,new,1)
HELPER=r'''
/* 03w read-only FNV-1a state hash; exact bytes on SAME Linux toolchain. */
static unsigned long long tisc03w_bytes(unsigned long long h, const void *ptr, unsigned long n) {
    const unsigned char *x=(const unsigned char*)ptr;
    for(unsigned long i=0;i<n;i++) {
        h ^= (unsigned long long)x[i];
        h *= 1099511628211ULL;
    }
    return h;
}
static void tisc03w_snapshot(ModelConfig *cfg, ModelContext *ctx,
                             int surface_substep, double substep_Myr) {
    unsigned long long h_topo=14695981039346656037ULL;
    unsigned long long h_block=14695981039346656037ULL;
    unsigned long long h_flex=14695981039346656037ULL;
    unsigned long long h_drain=14695981039346656037ULL;
    for(int i=0;i<cfg->Ny;i++) for(int j=0;j<cfg->Nx;j++) {
        h_topo=tisc03w_bytes(h_topo,&ctx->topo[i][j],sizeof(float));
        h_flex=tisc03w_bytes(h_flex,&w[i][j],sizeof(float));
        if(ctx->numBlocks>0)
            h_block=tisc03w_bytes(h_block,&Blocks[ctx->numBlocks-1].thick[i][j],sizeof(float));
        h_drain=tisc03w_bytes(h_drain,&drainage[i][j].type,sizeof(drainage[i][j].type));
        h_drain=tisc03w_bytes(h_drain,&drainage[i][j].lake,sizeof(drainage[i][j].lake));
        h_drain=tisc03w_bytes(h_drain,&drainage[i][j].dr_row,sizeof(drainage[i][j].dr_row));
        h_drain=tisc03w_bytes(h_drain,&drainage[i][j].dr_col,sizeof(drainage[i][j].dr_col));
    }
    fprintf(stderr,"\nTISC_03W_SHADOW elapsedMyr=%.8f mainMyr=%.8f substep=%d "
        "nblocks=%d topo_crc=%016llx block_crc=%016llx flex_crc=%016llx hydro_crc=%016llx\n",
        substep_Myr, (double)(ctx->Time/Matosec),surface_substep,
        ctx->numBlocks,h_topo,h_block,h_flex,h_drain);
    fflush(stderr);
}
'''
def main(src,out):
    p=Path(src);out=Path(out);b=p.read_bytes();s=b.decode()
    if "TISC_03T_CORRECTED_BALANCE" not in s:raise RuntimeError("Compile on 03t fixed reference before optional 03u1 patch")
    if "TISC_03W_SHADOW" in s:raise RuntimeError("Observer already present")
    s=once(s,"int Surface_Transport (ModelConfig *cfg",HELPER+"\nint Surface_Transport (ModelConfig *cfg","helper")
    a=s.index("int Surface_Transport (ModelConfig *cfg");z=s.index("int Calculate_Discharge (struct GRIDNODE *sortcell",a)
    frag=s[a:z]
    key="\t\tIce_EroSed(cfg, ctx, ice_velx_sl, ice_vely_sl, dt_st, &total_ice_eros, &total_ice_sedim);"
    frag=once(frag,key,key+"\n"
      "\t\ttisc03w_snapshot(cfg, ctx, iter, (double)(ctx->Time/Matosec)+\n"
      "\t\t\t(double)(iter+1)*(double)dt_st/(double)Matosec);",
      "end of hydrological substep")
    s=s[:a]+frag+s[z:]
    p.write_text(s);out.mkdir(parents=True,exist_ok=True)
    (out/"03W_STATE_HASH_AUDIT.json").write_text(json.dumps({
      "upstream_sha":"d18b7d270f4d671b80223e10dede329ad35cafdd",
      "source_before_sha256":hashlib.sha256(b).hexdigest(),
      "source_after_sha256":hashlib.sha256(s.encode()).hexdigest(),
      "physical_changes":False,"state_changes":False,
      "sample":"end each erosion hydrological substep, before next erosion substep",
      "scientific_caveat":"bitwise local hash differences may occur earlier than 0.1m printed output; no proof of dynamically relevant perturbation",
      "expected_pair":"compile same 03w tracer into both 03t and 03u1 binaries"
    },indent=2))
    (out/"03W_SOURCE.diff").write_text("".join(difflib.unified_diff(b.decode().splitlines(True),s.splitlines(True),fromfile="03t/surf_proc.c",tofile="03w/observer/surf_proc.c")))
    print("03w state hashes added after each physical hydrological substep")
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("profile_03w_state_checksums.py C_SRC AUDIT")
    main(sys.argv[1],sys.argv[2])
