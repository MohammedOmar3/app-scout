#!/usr/bin/env python3
"""Drive the GitHub `collect` workflow from the analysis session.

  python scout/collector_ctl.py status
  python scout/collector_ctl.py ensure-fresh [--max-age-hours 14] [--timeout-min 75]
      use the latest data if it is fresh and healthy; otherwise wait for a running
      collection, or start one and wait. Retries once (smaller) if the run comes back FAILED.
  python scout/collector_ctl.py targeted --app-ids 123,456 [--terms "a,b"] [--storefronts-per-app 8]
      targeted scan for the hunt loop (capped per day by config max_targeted_runs_per_day)

Talks to the GitHub REST API through curl (the session's proxy adds credentials for the
attached repo). Prints one JSON line on success; exits non-zero with a reason on failure,
so the caller can write it into the report instead of guessing.
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = "collect.yml"


def repo_slug():
    url = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
    slug = url.split("github.com/")[-1].removesuffix(".git").strip("/")
    return slug or "MohammedOmar3/app-scout"


def api(method, path, body=None):
    cmd = ["curl", "-sS", "-m", "30", "-w", "\n%{http_code}", "-X", method, "-H", "Accept: application/vnd.github+json",
           f"https://api.github.com/repos/{repo_slug()}{path}"]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    for attempt in range(3):
        r = subprocess.run(cmd, capture_output=True, text=True)
        out, _, code = r.stdout.rpartition("\n")
        if code.isdigit() and int(code) < 500:
            try:
                return int(code), (json.loads(out) if out.strip() else {})
            except json.JSONDecodeError:
                return int(code), {"raw": out[:300]}
        time.sleep(5 * (attempt + 1))
    return 0, {"error": (r.stderr or r.stdout)[:300]}


def cfg():
    return json.loads((ROOT / "collector/config.json").read_text())


def runs(limit=10):
    code, d = api("GET", f"/actions/workflows/{WORKFLOW}/runs?per_page={limit}")
    if code != 200:
        die(f"cannot list workflow runs (HTTP {code}): {d}")
    return d.get("workflow_runs", [])


def data_run_json():
    subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "--depth", "1", "origin", "data"], capture_output=True)
    r = subprocess.run(["git", "-C", str(ROOT), "show", "FETCH_HEAD:latest/run.json"], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def age_hours(run):
    ts = (run or {}).get("finished")
    if not ts:
        return 1e9
    t = dt.datetime.fromisoformat(ts)
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return (dt.datetime.now(dt.timezone.utc) - t).total_seconds() / 3600


def die(msg, code=2):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


def dispatch(inputs):
    t = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=10)
    code, d = api("POST", f"/actions/workflows/{WORKFLOW}/dispatches", {"ref": "main", "inputs": inputs})
    if code != 204:
        die(f"dispatch refused (HTTP {code}): {d}")
    for _ in range(24):  # find the run we just started
        time.sleep(5)
        for r in runs(5):
            if r["event"] == "workflow_dispatch" and dt.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")) >= t:
                return r["id"]
    die("dispatched, but the run never appeared in the list")


def wait(run_id, timeout_min):
    end = time.time() + timeout_min * 60
    while time.time() < end:
        code, r = api("GET", f"/actions/runs/{run_id}")
        if code == 200 and r.get("status") == "completed":
            return r.get("conclusion")
        time.sleep(30)
    die(f"run {run_id} still not finished after {timeout_min} min")


def active_run():
    for r in runs(10):
        if r["status"] in ("queued", "in_progress", "waiting", "pending"):
            return r
    return None


def summary(run, extra=None):
    h = (run or {}).get("health", {})
    out = {"ok": h.get("level") in ("OK", "DEGRADED"), "health": h.get("level"), "reasons": h.get("reasons", []),
           "finished": (run or {}).get("finished"), "age_hours": round(age_hours(run), 1),
           "apps_scanned": (run or {}).get("apps_scanned"), "low_star_kept": (run or {}).get("low_star_kept")}
    out.update(extra or {})
    return out


def ensure_fresh(a):
    run = data_run_json()
    h = (run or {}).get("health", {}).get("level")
    if run and age_hours(run) <= a.max_age_hours and h in ("OK", "DEGRADED"):
        print(json.dumps(summary(run, {"action": "used existing data"})))
        return
    act = active_run()
    if act:
        concl = wait(act["id"], a.timeout_min)
        run = data_run_json()
        if run and age_hours(run) <= a.max_age_hours and run.get("health", {}).get("level") in ("OK", "DEGRADED"):
            print(json.dumps(summary(run, {"action": f"waited for running collection {act['id']} ({concl})"})))
            return
    attempts = [{"mode": "daily"}, {"mode": "daily", "shards": "4"}]  # retry wider: more fresh runner IPs
    last = None
    for i, inputs in enumerate(attempts):
        rid = dispatch(inputs)
        concl = wait(rid, a.timeout_min)
        run = data_run_json()
        last = summary(run, {"action": f"started collection {rid} ({concl}), attempt {i + 1}"})
        if run and age_hours(run) <= 2 and last["ok"]:
            print(json.dumps(last))
            return
        time.sleep(120)
    print(json.dumps(last or {"ok": False, "error": "no run.json"}))
    sys.exit(1)


def targeted(a):
    c = cfg()
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    used = [r for r in runs(30) if r.get("name") == "collect targeted" and r["created_at"].startswith(today)]
    if len(used) >= c.get("max_targeted_runs_per_day", 2):
        die(f"targeted-run cap reached for today ({len(used)}); continue with the data you have", code=3)
    act = active_run()
    if act:
        wait(act["id"], a.timeout_min)
    inputs = {"mode": "targeted", "app_ids": a.app_ids, "terms": a.terms or ""}
    if a.storefronts_per_app:
        inputs["storefronts_per_app"] = str(a.storefronts_per_app)
    rid = dispatch(inputs)
    concl = wait(rid, a.timeout_min)
    subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "--depth", "1", "origin", "data"], capture_output=True)
    r = subprocess.run(["git", "-C", str(ROOT), "show", "FETCH_HEAD:latest/targeted_run.json"], capture_output=True, text=True)
    try:
        run = json.loads(r.stdout)
    except json.JSONDecodeError:
        die(f"targeted run {rid} ({concl}) left no targeted_run.json")
    print(json.dumps(summary(run, {"action": f"targeted run {rid} ({concl})", "targets": run.get("targets"),
                                   "remaining_today": c.get("max_targeted_runs_per_day", 2) - len(used) - 1})))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    e = sub.add_parser("ensure-fresh")
    e.add_argument("--max-age-hours", type=float, default=14)
    e.add_argument("--timeout-min", type=int, default=75)
    t = sub.add_parser("targeted")
    t.add_argument("--app-ids", required=True)
    t.add_argument("--terms", default="")
    t.add_argument("--storefronts-per-app", type=int, default=0)
    t.add_argument("--timeout-min", type=int, default=45)
    a = ap.parse_args()
    if a.cmd == "status":
        run = data_run_json()
        print(json.dumps({"data": summary(run), "runs": [{k: r[k] for k in ("id", "name", "event", "status", "conclusion", "created_at")} for r in runs(5)]}, indent=1))
    elif a.cmd == "ensure-fresh":
        ensure_fresh(a)
    else:
        targeted(a)


if __name__ == "__main__":
    main()
