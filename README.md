# App Scout

Finds small, buildable iOS app ideas by mining **proven, repeated pain** in apps that are already charting — then writes evidence-backed briefs ready for `/app-factory idea`.

**Latest:** 2026-11-12 — hunt in progress (round 1: no idea yet; teleprompters 3.50 on watchlist) — [report](reports/2026-11-12.md)

## How it works

```
06:44 Dubai  Claude scheduled task = orchestrator + analyst (SCOUT.md)
  step 0     collector_ctl.py ensure-fresh: use fresh healthy data, or start the GitHub
             `collect` workflow and wait; retry wider if it FAILS; health.py go/no-go
             └─ collect.yml (free Apple feeds)
                plan  (1 runner)  charts all ~175 storefronts + category charts + islamic
                                  search + lookup -> candidates + queue (mega-apps skipped,
                                  mid-sized grossing / abandoned apps first)
                scan  (3 runners) reviews only, one shard per fresh runner IP, gentle rate,
                                  circuit breaker on Apple 403s (stop fast, never burn the run)
                merge (1 runner)  data branch + run.json with a health verdict + digest
  steps 1-5  triage -> validate (cross-app, Reddit/web, kill check) -> Gate A/A2 + Gate B -> score
  step 7     no idea yet? hunt loop: targeted scans of the best leads + competitors (<=2/day),
             off-store evidence, re-score; repeat until one passes or budget is spent;
             unfinished hunts carry over in ideas/hunt.json
  step 6     report, briefs, ledger, hunt.json -> push after every round -> notification
```

The gates never move: the hunt makes the evidence stronger, it doesn't lower the bar.

## Where things are

| Path | What |
| --- | --- |
| `reports/YYYY-MM-DD.md` | Daily report: ideas, watchlist, rejections, data health |
| `briefs/YYYY-MM-DD-slug.md` | One per idea — hand to `/app-factory idea` |
| `ideas/ledger.json` | Memory across days: proposed, watchlist, rejected (no repeats) |
| `ideas/hunt.json` | Open hunt targets and exactly what evidence each still needs |
| `SCOUT.md` | The analysis playbook (gates, scoring, outputs) |
| `collector/` | Data collector + `config.json` knobs |
| `scout/` | `collector_ctl.py` (start/wait/targeted runs), `health.py` (go/no-go), `digest.py`, `reviews.py`, `themes.py` |
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
- GitHub Actions minutes: a private repo on the free plan gets 2,000 min/month; daily ≈ 45 runner-min (plan + 3 shards + merge) plus ≤ 2 targeted runs ≈ 10 min each → ~1,900 min/month, right at the limit. Moving the collector to a public repo makes Actions minutes free. Lower `apps_to_scan_per_day` if needed.
