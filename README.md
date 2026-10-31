# App Scout

Finds small, buildable iOS app ideas by mining **proven, repeated pain** in apps that are already charting — then writes evidence-backed briefs ready for `/app-factory idea`.

**Latest:** 2026-10-31 — no ideas today (updated after second collector run; 1 on watchlist: SCRL free-tier cuts) — [report](reports/2026-10-31.md)

## How it works

```
00:23 UTC  GitHub Actions: collect.yml          (free Apple feeds, ≤ 26 min, self-throttling)
           ├─ top free / paid / grossing charts, all ~175 storefronts
           ├─ per-category charts for 8 rotating storefronts a day (+ US, GB daily)
           ├─ iTunes Lookup metadata (genre, ratings, price, last update) — cached
           ├─ drop games / medical / finance; keep "proven" apps (≥500 ratings or ≥3 storefronts)
           ├─ most-recent + most-helpful reviews from up to 6 storefronts for the top apps not scanned in 4 days
           │   (skips mega-apps > 1.5M ratings; favours mid-sized apps that make money)
           └─ low-star reviews → `data` branch (single commit, rewritten daily) + digest.md

06:44 Dubai  Claude scheduled task: follows SCOUT.md
           ├─ triage the 7-day digest, read the real reviews behind each cluster
           ├─ validate: spread across apps/storefronts, recency, Reddit/web via search, kill check
           ├─ Gate A (pain is real) + Gate B (fits app-factory: Expo/Supabase/RevenueCat, 14 days)
           ├─ score; ≥3.6 → idea (max 3/day, zero is fine), else watchlist / rejected
           └─ commit reports/, briefs/, ideas/ledger.json → push notification
```

## Where things are

| Path | What |
| --- | --- |
| `reports/YYYY-MM-DD.md` | Daily report: ideas, watchlist, rejections, data health |
| `briefs/YYYY-MM-DD-slug.md` | One per idea — hand to `/app-factory idea` |
| `ideas/ledger.json` | Memory across days: proposed, watchlist, rejected (no repeats) |
| `SCOUT.md` | The analysis playbook (gates, scoring, outputs) |
| `collector/` | Data collector + `config.json` knobs |
| `scout/` | `digest.py` (triage digest), `reviews.py` (query CLI), `themes.py` (keywords) |
| `data` branch | Latest snapshot: `latest/run.json`, `latest/candidates.json`, `latest/digest.md`, `reviews/<appId>.json` |

## Running by hand

```bash
python collector/collect.py --out ../data --storefronts us,gb --max-apps 10   # small test pull
python scout/digest.py --data ../data --out /tmp/digest.md
python scout/reviews.py --data ../data search "subscription"
```

Actions → **collect** → *Run workflow* triggers a pull on demand.

## Limits (by design)

- Free sources only: Apple's public review feed currently serves ~50 reviews per sort order per storefront, so evidence builds up across storefronts and repeated scans over days; Reddit is reached only through web search (its API closed to new developers on 31 Oct 2026).
- GitHub Actions minutes: a private repo on the free plan gets 2,000 min/month; this job uses ≤ 27 min/day (~800 min/month). Lower `apps_to_scan_per_day` if needed.
