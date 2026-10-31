#!/usr/bin/env python3
"""Query the collected data for the daily analysis.

  python scout/reviews.py --data ../data app <appId> [--stars 1,2] [--since YYYY-MM-DD] [--grep word] [--cc us] [--limit 80]
      print one app's low-star reviews
  python scout/reviews.py --data ../data search "<phrase>" [--since ...] [--limit 40]
      count a phrase across ALL apps' reviews (cross-app evidence), with sample lines
  python scout/reviews.py --data ../data competitors "<keyword>" [--limit 25]
      find charting, eligible apps whose name/description mention the keyword (competitor check)
  python scout/reviews.py --data ../data meta <appId>
      candidate metadata for one app
"""
import argparse
import json
from pathlib import Path

from themes import themes_of


def load(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def clip(s, n):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("app"); a.add_argument("id")
    a.add_argument("--stars", default="1,2"); a.add_argument("--since", default="")
    a.add_argument("--grep", default=""); a.add_argument("--cc", default=""); a.add_argument("--limit", type=int, default=80)
    s = sub.add_parser("search"); s.add_argument("phrase"); s.add_argument("--since", default=""); s.add_argument("--limit", type=int, default=40)
    c = sub.add_parser("competitors"); c.add_argument("keyword"); c.add_argument("--limit", type=int, default=25)
    m = sub.add_parser("meta"); m.add_argument("id")
    args = ap.parse_args()
    data = Path(args.data)

    if args.cmd == "app":
        doc = load(data / f"reviews/{args.id}.json", None)
        if not doc:
            print("no review file for", args.id); return
        stars = {int(x) for x in args.stars.split(",") if x}
        print(json.dumps(doc.get("app"), ensure_ascii=False))
        print("stats:", json.dumps(doc.get("stats"), ensure_ascii=False))
        n = 0
        for r in doc["reviews"]:
            if r["stars"] not in stars or r["date"] < args.since:
                continue
            if args.cc and r["cc"] != args.cc:
                continue
            blob = (r["title"] + " " + r["text"]).lower()
            if args.grep and args.grep.lower() not in blob:
                continue
            print(f"- {r['stars']}★ {r['cc']} {r['date']} v{r.get('version')} +{r['helpful']} [{', '.join(themes_of(blob))}] "
                  f"{clip(r['title'], 80)} — {clip(r['text'], 700)}")
            n += 1
            if n >= args.limit:
                break
        print(f"({n} shown of {len(doc['reviews'])} stored)")

    elif args.cmd == "search":
        phrase = args.phrase.lower()
        hits = []
        for p in (data / "reviews").glob("*.json"):
            doc = load(p, None)
            if not doc:
                continue
            rs = [r for r in doc["reviews"] if r["date"] >= args.since and phrase in (r["title"] + " " + r["text"]).lower()]
            if rs:
                hits.append((len(rs), doc, rs))
        hits.sort(key=lambda x: -x[0])
        total = sum(h[0] for h in hits)
        print(f"'{args.phrase}': {total} reviews across {len(hits)} apps")
        shown = 0
        for n, doc, rs in hits:
            app = doc.get("app") or {}
            print(f"\n## {app.get('name')} (id {doc['id']}, {app.get('genre')}, ★{app.get('rating')}, {app.get('ratings')} ratings): {n}")
            for r in rs[:3]:
                print(f"- {r['stars']}★ {r['cc']} {r['date']} — {clip(r['text'], 300)}")
            shown += 1
            if shown >= args.limit:
                break

    elif args.cmd == "competitors":
        kw = args.keyword.lower()
        cands = load(data / "latest/candidates.json", [])
        rows = [c for c in cands if kw in (c.get("name") or "").lower() or kw in (c.get("description") or "").lower()]
        rows.sort(key=lambda c: -(c.get("ratings") or 0))
        print(f"{len(rows)} charting eligible apps mention '{args.keyword}' (top {args.limit} by ratings):")
        for c in rows[: args.limit]:
            print(f"- {c['name']} (id {c['id']}, {c.get('genre')}) ★{c.get('rating')} {c.get('ratings')} ratings, "
                  f"{c.get('price')}, {c.get('storefronts')} storefronts, updated {c.get('updated')} — {clip(c.get('description'), 140)}")
        print("Note: only apps currently in a chart are here. Also check the App Store with WebSearch.")

    elif args.cmd == "meta":
        for c in load(data / "latest/candidates.json", []):
            if c["id"] == args.id:
                print(json.dumps(c, ensure_ascii=False, indent=1)); return
        print("not in today's candidates")


if __name__ == "__main__":
    main()
