#!/usr/bin/env python3
"""Conservative retention-based GitHub Actions Artifact cleanup.

ONLY own repository (GITHUB_REPOSITORY), no source/history/workflow run deletion.
Dry-run default. To apply, the workflow explicitly passes --apply.

Policy:
- Keep all artifacts belonging to a designated milestone run ID.
- Keep newest SUCCESSFUL artifact for every distinct name (even if zip digest differs).
- Delete artifacts associated with failed/cancelled/skipped runs except pinned.
- Delete older same-name successful copies except pinned.
- Keep unique successes and all ambiguous/unmatched outcomes.
- Abort on incomplete API pagination or errors; preserve manifest.
"""
import argparse, collections, datetime, json, os, pathlib, sys, time, urllib.request, urllib.error

PINNED = {
    "lcxstar/tisc-mechanism-lab": {39205727463,38183870409,38178743124,38178558812},
}
def request(endpoint, method="GET"):
    token=os.environ.get("GITHUB_TOKEN","")
    if not token:raise RuntimeError("GITHUB_TOKEN unavailable")
    host="https://api.github.com"
    hdr={"Authorization":"Bearer "+token,
         "Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28",
         "User-Agent":"junggar-artifact-conservative-retention"}
    req=urllib.request.Request(host+endpoint,headers=hdr,method=method)
    for i in range(3):
        try:
            with urllib.request.urlopen(req,timeout=45) as response:
                data=response.read()
                return json.loads(data) if data else {}
        except urllib.error.HTTPError as e:
            if e.code in (429,500,502,503) and i<2:
                time.sleep(3*(i+1));continue
            raise RuntimeError(f"GitHub REST failed {method} {endpoint}: HTTP {e.code}") from e
def list_all(repo,resource,key):
    records=[]; total=None
    for page in range(1,50):
        j=request(f"/repos/{repo}/actions/{resource}?per_page=100&page={page}")
        if total is None:total=int(j["total_count"])
        chunk=j[key]
        records.extend(chunk)
        if len(chunk)<100:break
    if total is None or len(records)!=total:
        raise RuntimeError(f"INCOMPLETE {resource}: listed {len(records)}, API says {total}")
    return records
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    repo=os.environ.get("GITHUB_REPOSITORY")
    if repo not in PINNED:raise RuntimeError(f"Refuse non-approved repository: {repo}")
    artifacts=list_all(repo,"artifacts","artifacts")
    runs=list_all(repo,"runs","workflow_runs")
    by_id={int(x["id"]):x for x in runs}
    protected_runs=PINNED[repo]
    successful=collections.defaultdict(list)
    for x in artifacts:
        run_id=(x.get("workflow_run") or {}).get("id")
        rs=by_id.get(run_id)
        if rs and rs.get("status")=="completed" and rs.get("conclusion")=="success":
            successful[x["name"]].append(x)
    newest_good={}
    for name,items in successful.items():
        newest_good[name]=max(items,key=lambda x:(x.get("created_at") or "",x["id"]))["id"]
    plan=[]
    for x in artifacts:
        rid=(x.get("workflow_run") or {}).get("id")
        run=by_id.get(rid)
        conclusion=run.get("conclusion") if run and run.get("status")=="completed" else "unknown"
        reason="keep_ambiguous"
        if rid in protected_runs:reason="keep_pinned_milestone"
        elif conclusion=="success":
            if newest_good.get(x["name"])==x["id"]:reason="keep_newest_successful_name"
            else:reason="delete_superseded_successful_same_name"
        elif conclusion in ("failure","cancelled","skipped","timed_out","action_required"):
            if x["name"] in newest_good:reason="delete_failed_with_successful_replacement"
            else:reason="delete_failed_or_cancelled_run_artifact"
        else:reason="keep_ambiguous_run_status"
        plan.append({"id":x["id"],"name":x["name"],"bytes":int(x.get("size_in_bytes") or 0),
           "digest":x.get("digest"),"run_id":rid,"run_conclusion":conclusion,
           "created_at":x.get("created_at"),"reason":reason})
    remove=[x for x in plan if x["reason"].startswith("delete_")]
    keep=[x for x in plan if x["reason"].startswith("keep_")]
    counts=collections.Counter(x["reason"] for x in plan)
    remove_counts=collections.Counter(x["reason"] for x in remove)
    report={
      "repo":repo,"time_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "policy":"pinned milestone, newest-successful-per-name, drop failed and superseded successful",
      "mode":"APPLY" if a.apply else "DRY_RUN",
      "total_current":len(plan),"total_current_bytes":sum(x["bytes"] for x in plan),
      "keep_count":len(keep),"keep_bytes":sum(x["bytes"] for x in keep),
      "deletion_candidates":len(remove),"candidate_bytes":sum(x["bytes"] for x in remove),
      "reason_counts":dict(counts),
      "reason_delete_counts":dict(remove_counts),
      "pinned_run_ids":sorted(protected_runs),
      "candidate_list":remove,
      "protected_list":keep,
    }
    out=(pathlib.Path.home()/"junggar"/"results"/"storage_audit"/os.environ.get("GITHUB_RUN_ID","manual")
         if repo.endswith("junggar-tisc-model") else pathlib.Path(os.environ.get("RUNNER_TEMP","/tmp"))/"tisc_artifact_audit")
    out.mkdir(parents=True,exist_ok=True)
    path=out/f"{repo.split('/')[-1]}_ARTIFACT_CLEANUP_{'APPLY' if a.apply else 'PLAN'}.json"
    path.write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(f"Repo {repo}. Current artifacts={len(plan)} bytes={report['total_current_bytes']}")
    print(f"PROTECT={len(keep)} bytes={report['keep_bytes']}")
    print(f"DELETION CANDIDATES={len(remove)} bytes={report['candidate_bytes']}")
    print("Reasons:",dict(counts))
    print("Top candidates:")
    for x in sorted(remove,key=lambda r:r["bytes"],reverse=True)[:32]:
        print(x["id"],round(x["bytes"]/2**20,2),"MiB",x["reason"],"RUN",x["run_id"],x["name"])
    print("Plan:",path,flush=True)
    if not a.apply:
        print("DRY RUN ONLY: zero artifacts deleted.",flush=True)
        return
    if len(plan)<100 or len(remove)==0 or len(remove)>=len(plan):
        raise RuntimeError("ABORT suspicious deletion count or no candidates")
    if not (all(x["run_id"] not in protected_runs for x in remove)
            and all(x["id"] not in {v for v in newest_good.values()} for x in remove)):
        raise RuntimeError("ABORT protected artifact leaked into deletion list")
    success=[]; failures=[]
    for n,x in enumerate(remove,1):
        try:
            request(f"/repos/{repo}/actions/artifacts/{x['id']}",method="DELETE")
            success.append(x)
        except Exception as exc:
            failures.append({"id":x["id"],"error":str(exc)})
        if n%25==0:
            print(f"DELETE PROGRESS {n}/{len(remove)} success={len(success)} failed={len(failures)}",flush=True)
    result={"repo":repo,"attempted":len(remove),"deleted":len(success),"deleted_bytes":sum(x["bytes"] for x in success),
             "delete_errors":failures,"preserved":len(keep),"preserved_bytes":sum(x["bytes"] for x in keep),
             "deleted_ids":[x["id"] for x in success]}
    result_path=out/f"{repo.split('/')[-1]}_ARTIFACT_CLEANUP_RESULT.json"
    result_path.write_text(json.dumps(result,indent=2))
    print("COMPLETED",json.dumps({k:v for k,v in result.items() if k not in ("deleted_ids","delete_errors")}),flush=True)
    print("Delete errors count:",len(failures),"Local result",result_path,flush=True)
    if failures:raise RuntimeError("Some deletion API calls failed; consult local result")
if __name__=="__main__":main()
