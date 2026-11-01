#!/usr/bin/env python3
"""Go/no-go check on the collected data.

  python scout/health.py --data ../data [--max-age-hours 14]

Prints a JSON verdict and exits 0 (OK), 1 (DEGRADED: usable, say so in the report),
2 (FAILED: no usable new data), 3 (STALE: older than --max-age-hours).
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--max-age-hours", type=float, default=14)
    a = ap.parse_args()
    p = Path(a.data) / "latest/run.json"
    if not p.exists():
        print(json.dumps({"level": "FAILED", "reasons": ["no latest/run.json on the data branch"]}))
        sys.exit(2)
    run = json.loads(p.read_text())
    h = run.get("health") or {"level": "OK" if run.get("apps_scanned") else "FAILED", "reasons": ["(old-format run.json)"]}
    fin = run.get("finished")
    age = None
    if fin:
        t = dt.datetime.fromisoformat(fin)
        t = t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
        age = round((dt.datetime.now(dt.timezone.utc) - t).total_seconds() / 3600, 1)
    out = {"level": h["level"], "reasons": list(h.get("reasons", [])), "finished": fin, "age_hours": age,
           "apps_scanned": run.get("apps_scanned"), "low_star_kept": run.get("low_star_kept"),
           "shards": run.get("shards_detail"), "targeted_runs": len(run.get("targeted_runs", []))}
    if age is None or age > a.max_age_hours:
        out["reasons"].append(f"data is {age} h old (> {a.max_age_hours} h)")
        out["level"] = "STALE" if out["level"] != "FAILED" else "FAILED"
    print(json.dumps(out, ensure_ascii=False))
    sys.exit({"OK": 0, "DEGRADED": 1, "FAILED": 2, "STALE": 3}[out["level"]])


if __name__ == "__main__":
    main()
