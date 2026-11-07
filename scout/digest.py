#!/usr/bin/env python3
"""Build a compact triage digest (Markdown) from the data branch.

Covers every app scanned in the last --window days (the collector rotates ~150 apps/day,
so a 7-day window covers ~1000 apps). Ranks apps by an "opportunity pain" signal, shows
cross-app themes per genre, abandoned-but-charting apps, and sample low-star reviews.
The daily Claude run reads this first, then digs into raw reviews with reviews.py.
"""
import argparse
import datetime as dt
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from themes import NOISE, OPPORTUNITY, is_mostly_latin, themes_of


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
    ap.add_argument("--out", required=True)
    ap.add_argument("--window", type=int, default=7, help="days of scans to include")
    ap.add_argument("--recent", type=int, default=90, help="count low-star reviews from the last N days")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--ledger", help="optional ideas/ledger.json to mark apps already used")
    args = ap.parse_args()

    data = Path(args.data)
    run = load(data / "latest/run.json", {})
    cands = {c["id"]: c for c in load(data / "latest/candidates.json", [])}
    ledger = load(args.ledger, {}) if args.ledger else {}
    used = set()
    for item in ledger.get("ideas", []) + ledger.get("rejected", []):
        used.update(str(i) for i in item.get("incumbents", []))

    today = dt.date.fromisoformat(run["date"]) if run.get("date") else dt.date.today()
    win_cut = (today - dt.timedelta(days=args.window)).isoformat()
    rec_cut = (today - dt.timedelta(days=args.recent)).isoformat()

    apps = []
    genre_theme = defaultdict(lambda: defaultdict(list))  # genre -> theme -> [(app, hits)]
    for p in sorted((data / "reviews").glob("*.json")) if (data / "reviews").exists() else []:
        doc = load(p, None)
        if not doc or doc.get("last_scanned", "") < win_cut:
            continue
        meta = {**(doc.get("app") or {}), **({k: v for k, v in cands.get(doc["id"], {}).items() if v is not None})}
        recent = [r for r in doc.get("reviews", []) if r["date"] >= rec_cut]
        if not recent:
            continue
        theme_counts = Counter()
        tagged = []
        non_latin = 0
        for r in recent:
            th = themes_of(r["title"] + " " + r["text"])
            theme_counts.update(th)
            tagged.append((r, th))
            if not is_mostly_latin(r["text"]):
                non_latin += 1
        opp = sum(theme_counts[k] for k in OPPORTUNITY)
        noise = sum(theme_counts[k] for k in NOISE)
        fetched = sum(s.get("fetched", 0) for s in (doc.get("stats") or {}).values())
        low_all = sum(s["hist"]["1"] + s["hist"]["2"] for s in (doc.get("stats") or {}).values() if "hist" in s)
        ratings = meta.get("ratings") or 0
        updated = meta.get("updated") or ""
        stale_days = (today - dt.date.fromisoformat(updated)).days if len(updated) == 10 else None
        signal = (opp + 0.25 * len(recent) + 0.3 * non_latin) * (1 + math.log10(ratings + 1) / 6)
        if stale_days and stale_days > 365:
            signal *= 1.3
        apps.append({"id": doc["id"], "meta": meta, "recent": len(recent), "opp": opp, "noise": noise,
                     "themes": theme_counts, "tagged": tagged, "non_latin": non_latin, "fetched": fetched,
                     "low_share": round(low_all / fetched, 2) if fetched else None, "stale_days": stale_days,
                     "signal": round(signal, 1), "used": doc["id"] in used})
        for k in OPPORTUNITY:
            if theme_counts[k] >= 3:
                genre_theme[meta.get("genre") or "?"][k].append((meta.get("name"), theme_counts[k]))

    apps.sort(key=lambda a: a["signal"], reverse=True)
    L = []
    L.append(f"# App Scout digest — data of {run.get('date', '?')}\n")
    L.append(f"Collector: {run.get('minutes')} min, partial={run.get('partial')}, chart apps {run.get('unique_chart_apps')}, "
             f"eligible {run.get('eligible_candidates')}, scanned today {run.get('apps_scanned')}, "
             f"reviews fetched {run.get('reviews_fetched')}, low-star kept {run.get('low_star_kept')}, "
             f"failures {run.get('failures')}/{run.get('requests')} requests.")
    L.append(f"Window: apps scanned in the last {args.window} days ({len(apps)} with low-star reviews in the last {args.recent} days). "
             "Theme counts are English keyword hits only; non-latin reviews are counted separately and must be read.\n")

    # early surges: pain that started in the last 14 days, before clones exist
    L.append("## Early surges (low-star reviews in the last 14 days vs the app's own earlier rate)\n")
    L.append("Mid-sized apps only (2k-300k ratings), services and platforms excluded. A surge is the best moment to "
             "build: refugees are looking for an alternative and fast followers haven't shipped yet.\n")
    skip_g = {"Social Networking", "Entertainment", "Shopping", "News", "Music", "Magazines & Newspapers", "Food & Drink", "Travel"}
    d14 = (today - dt.timedelta(days=14)).isoformat()
    surges = []
    for a in apps:
        m = a["meta"]
        rc = m.get("ratings") or 0
        if not (2000 <= rc <= 300000) or m.get("genre") in skip_g:
            continue
        r14 = sum(1 for r, _ in a["tagged"] if r["date"] >= d14)
        r_before = a["recent"] - r14
        base = r_before / max(1, args.recent - 14) * 14
        spike = r14 / (base + 1)
        if r14 >= 10 and spike >= 3:
            surges.append((r14 * min(spike, 10), r14, round(spike, 1), a))
    surges.sort(key=lambda x: -x[0])
    if surges:
        L.append("| app | id | genre | ratings | last 14 d | spike | storefronts |\n|---|---|---|---|---|---|---|")
        for _, r14, spike, a in surges[:15]:
            m = a["meta"]
            ccs = sorted({r["cc"] for r, _ in a["tagged"] if r["date"] >= d14})
            L.append(f"| {clip(m.get('name'), 34)}{' [used]' if a['used'] else ''} | {a['id']} | {m.get('genre')} | {m.get('ratings')} | {r14} | x{spike} | {', '.join(ccs[:6])} |")
    else:
        L.append("_no surges in mid-sized tool apps today_")
    L.append("")

    L.append("## Cross-app themes by genre (same complaint in several apps = stronger evidence)\n")
    rows = []
    for g, tm in genre_theme.items():
        for k, lst in tm.items():
            if len(lst) >= 2:
                rows.append((len(lst), sum(h for _, h in lst), g, k, lst))
    rows.sort(reverse=True)
    if rows:
        L.append("| genre | theme | apps | hits | apps (hits) |\n|---|---|---|---|---|")
        for n, hits, g, k, lst in rows[:25]:
            names = ", ".join(f"{clip(nm, 28)} ({h})" for nm, h in sorted(lst, key=lambda x: -x[1])[:6])
            L.append(f"| {g} | {k} | {n} | {hits} | {names} |")
    else:
        L.append("_none yet (needs a few days of scans)_")

    L.append("\n## Abandoned but still charting (no update > 12 months)\n")
    stale = sorted([c for c in cands.values() if c.get("updated") and len(c["updated"]) == 10
                    and (today - dt.date.fromisoformat(c["updated"])).days > 365
                    and (c.get("storefronts", 0) >= 3 or c.get("ratings", 0) >= 5000)],
                   key=lambda c: -c.get("priority", 0))[:15]
    for c in stale:
        L.append(f"- {c['name']} ({c.get('genre')}) id {c['id']} — last update {c['updated']}, "
                 f"{c.get('ratings')} ratings ★{round(c.get('rating') or 0, 1)}, charts in {c.get('storefronts')} storefronts, {c.get('price')}")
    if not stale:
        L.append("_none_")

    L.append(f"\n## Top {args.top} apps by opportunity-pain signal\n")
    for a in apps[: args.top]:
        m = a["meta"]
        th = ", ".join(f"{k} {v}" for k, v in a["themes"].most_common() if v)
        flag = " **[already used in ledger]**" if a["used"] else ""
        L.append(f"### {m.get('name')} — id {a['id']}{flag}")
        L.append(f"{m.get('genre')} · ★{round(m.get('rating') or 0, 1)} from {m.get('ratings')} ratings ({m.get('ratings_cc')}) · {m.get('price')} · "
                 f"charts in {m.get('storefronts')} storefronts (grossing in {m.get('grossing_storefronts')}) · "
                 f"updated {m.get('updated')} · seller {clip(m.get('seller'), 40)}")
        L.append(f"Low-star last {args.recent}d: {a['recent']} (non-latin {a['non_latin']}) · low-star share of recent sample {a['low_share']} · "
                 f"signal {a['signal']} · themes: {th or 'none matched'}")
        picks = sorted(a["tagged"], key=lambda rt: (any(t in OPPORTUNITY for t in rt[1]), rt[0]["helpful"], len(rt[0]["text"])), reverse=True)[:6]
        for r, t in picks:
            L.append(f"- {r['stars']}★ {r['cc']} {r['date']} v{r.get('version')} [{', '.join(t) or '-'}] "
                     f"**{clip(r['title'], 60)}** — {clip(r['text'], 260)}")
        L.append("")

    # focus segments (keyword segments that aren't App Store genres, e.g. islamic)
    segs = sorted({sg for a in apps for sg in (a["meta"].get("focus") or [])})
    shown = {a["id"] for a in apps[: args.top]}
    for sg in segs:
        seg_apps = [a for a in apps if sg in (a["meta"].get("focus") or [])]
        L.append(f"\n## Focus segment: {sg} ({len(seg_apps)} apps with recent low-star reviews)\n")
        seg_theme = {}
        for a in seg_apps:
            for k in OPPORTUNITY:
                if a["themes"][k]:
                    seg_theme.setdefault(k, []).append((a["meta"].get("name"), a["themes"][k]))
        for k, lst in sorted(seg_theme.items(), key=lambda kv: -sum(h for _, h in kv[1])):
            names = ", ".join(f"{clip(n, 26)} ({h})" for n, h in sorted(lst, key=lambda x: -x[1])[:6])
            L.append(f"- **{k}**: {len(lst)} apps, {sum(h for _, h in lst)} hits — {names}")
        L.append("")
        for a in seg_apps[:15]:
            m = a["meta"]
            if a["id"] in shown:
                L.append(f"- {m.get('name')} (id {a['id']}) — see main list above")
                continue
            th = ", ".join(f"{k} {v}" for k, v in a["themes"].most_common() if v)
            L.append(f"### {m.get('name')} — id {a['id']}" + (" **[already used in ledger]**" if a["used"] else ""))
            L.append(f"{m.get('genre')} · ★{round(m.get('rating') or 0, 1)} from {m.get('ratings')} ratings ({m.get('ratings_cc')}) · {m.get('price')} · "
                     f"updated {m.get('updated')} · found via search in {', '.join(m.get('search_storefronts') or [])} · charts in {m.get('storefronts')} storefronts")
            L.append(f"Low-star last {args.recent}d: {a['recent']} (non-latin {a['non_latin']}) · signal {a['signal']} · themes: {th or 'none matched'}")
            picks = sorted(a["tagged"], key=lambda rt: (any(t in OPPORTUNITY for t in rt[1]), rt[0]["helpful"], len(rt[0]["text"])), reverse=True)[:5]
            for r, t in picks:
                L.append(f"- {r['stars']}★ {r['cc']} {r['date']} v{r.get('version')} [{', '.join(t) or '-'}] "
                         f"**{clip(r['title'], 60)}** — {clip(r['text'], 240)}")
            L.append("")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(L), encoding="utf-8")
    print(f"digest: {len(apps)} apps in window, wrote {args.out} ({sum(len(x) for x in L)//1024} KB)")


if __name__ == "__main__":
    main()
