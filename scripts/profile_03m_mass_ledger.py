#!/usr/bin/env python3
"""03m non-mutating full precision sediment-balance diagnostic.

Inject a single detailed ledger at Surface_Transport output, printing exact
existing accumulator floating values as doubles and the suspended mass held
in the drainage cells. This is an OBSERVABILITY patch, not a repair.
"""
from pathlib import Path
import hashlib,json,difflib,sys
def main(src,out):
 p=Path(src);out=Path(out);b=p.read_bytes();s=b.decode()
 if "tisc_03ja_lake_evap" not in s or "TISC_03K_GUARD" not in s:
  raise RuntimeError("03m requires validated 03g + 03j + labeled 03k correction")
 if "TISC_03M_LEDGER" in s: raise RuntimeError("already instrumented")
 old='\tPRINT_SUMLINE("eros_nosd:'
 if s.count(old)!=1:raise RuntimeError("expected one diagnostic anchor, got "+str(s.count(old)))
 ins=r'''
    /* 03m no-change QC: print internal mass fields at 16+ digits. */
    {
        double tisc03m_suspended_rate=0, tisc03m_neg_rate=0;
        unsigned long long tisc03m_nonzero_nodes=0, tisc03m_nan_nodes=0;
        for(int i=0;i<cfg->Ny;i++) for(int j=0;j<cfg->Nx;j++) {
            double q=(double)drainage[i][j].masstr;
            if (!isfinite(q)) {tisc03m_nan_nodes++; continue;}
            tisc03m_suspended_rate += q;
            if(q<0) tisc03m_neg_rate+=q;
            if(q!=0) tisc03m_nonzero_nodes++;
        }
        const double tisc03m_eros=(double)ctx->total_bedrock_eros_mass;
        const double tisc03m_sed=(double)ctx->total_sed_mass;
        const double tisc03m_out=(double)total_lost_sed_mass;
        const double tisc03m_res=tisc03m_eros-tisc03m_sed-tisc03m_out;
        fprintf(stderr,
          "\nTISC_03M_LEDGER timeMyr=%.6f dtst_s=%.17g erosion_kg=%.17g "
          "deposition_net_kg=%.17g out_kg=%.17g unaccounted_kg=%.17g "
          "suspended_kgps=%.17g suspended_kg_one_substep=%.17g "
          "negative_kgps=%.17g nonzero_nodes=%llu nonfinite_nodes=%llu\n",
          (double)(ctx->Time/Matosec),(double)dt_st,
          tisc03m_eros,tisc03m_sed,tisc03m_out,tisc03m_res,
          tisc03m_suspended_rate,tisc03m_suspended_rate*(double)dt_st,
          tisc03m_neg_rate,tisc03m_nonzero_nodes,tisc03m_nan_nodes);
        fflush(stderr);
    }
'''
 s=s.replace(old,ins+old,1)
 p.write_text(s)
 out.mkdir(parents=True,exist_ok=True)
 (out/"03M_LEDGER_SOURCE_AUDIT.json").write_text(json.dumps({
    "experiment":"03m exact accumulator and residual tracer only",
    "source_before_sha256":hashlib.sha256(b).hexdigest(),
    "source_after_sha256":hashlib.sha256(s.encode()).hexdigest(),
    "physics_modified":False,"diagnostic":"sum suspended masses in existing drainage and print as double",
    "known_error":"accumulators internally float; printf double conversion does not add internal precision",
    "scientific_limit":"suspended stock evaluated at Surface_Transport end, may not close time-integrated budgets alone"
 },indent=2))
 (out/"03M_LEDGER_SOURCE.diff").write_text("".join(difflib.unified_diff(
    b.decode().splitlines(True),s.splitlines(True),
    fromfile="03k-fixed/surf_proc.c",tofile="03m-ledger/surf_proc.c")))
 print("03m non-mutating ledger patch added")
if __name__=="__main__":
 if len(sys.argv)!=3:raise SystemExit("profile_03m_mass_ledger.py SOURCE_C AUDIT_DIR")
 main(sys.argv[1],sys.argv[2])
