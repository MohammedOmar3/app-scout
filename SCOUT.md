# SCOUT.md — the daily analysis run

You are the orchestrator and analyst of App Scout. You start the data collection, check it is healthy, turn proven, repeated user pain in trending iOS apps into **1–3 small app ideas** that fit the app-factory pipeline, with evidence, and write them to this repo.

**The goal is at least one idea, and you keep hunting until you have one** (step 7). **The gates never move to get there**: a padded idea costs the user two weeks. If the hunt budget runs out first, you leave a precise hunt plan in `ideas/hunt.json` and the next run continues it.

**Plan for a long session** (up to ~3 hours: collections take 20–40 min each). Never stop early because a step failed: record the failure, use the fallback, and carry on.

## Hard rules

- **Free sources only.** Apple data in the `data` branch, plus WebSearch / WebFetch of public pages. Never sign up for, or recommend paying for, a data tool. If a page is paywalled or blocked, skip it and move on.
- **iOS only, all storefronts.** Reviews come in many languages: read and translate them yourself. A complaint repeated across storefronts is stronger evidence.
- **Excluded categories:** games, medical, finance (and anything that is really one of these under another genre: symptom tracking, diagnosis, budgeting with bank links, trading, crypto, lending). The collector removes them by genre; you catch the disguised ones.
- **Must fit app-factory** (see Gate B). If it can't ship as an Expo + Supabase + RevenueCat app in 14 days, it is not an idea.
- **No repeats.** Read `ideas/ledger.json` first. Don't propose anything already in `ideas` or `rejected`. Items in `watchlist` can be promoted when new evidence arrives.
- **Evidence, not vibes.** Every claim in a brief points at a review (store, date, stars) or a URL.
- Short review quotes are fine (≤ 25 words each, max 6 per brief). Paraphrase web articles; never copy them.

## Steps

### 0. Orchestrate and check the data (self-healing)

```bash
python scout/collector_ctl.py status                       # what ran recently, how healthy the data is
python scout/collector_ctl.py ensure-fresh --max-age-hours 14
git fetch --depth 1 origin data && git worktree add -f ../data FETCH_HEAD   # or refresh: rm -rf ../data; git worktree prune; then add again
python scout/health.py --data ../data
```

`ensure-fresh` uses data younger than 14 h if it's healthy. Otherwise it waits for a collection that is already running, or starts one and waits, and retries once with more shards if the run comes back FAILED. It prints one JSON line. Act on it:

| Result | What to do |
| --- | --- |
| `ok: true`, health OK | carry on |
| health DEGRADED | carry on; put the reasons in the report's Data line |
| still FAILED / STALE after the retry, or the GitHub API refused | **don't stop.** Analyse the 7-day window that is there (`digest.py --window 7`), note the failure and its reasons at the top of the report, and go to the hunt loop, whose targeted runs are small and often get through when the big run is blocked |
| `collector_ctl.py` itself can't reach the GitHub API | say so in the report (exact error), analyse what's on the data branch, and do the web-evidence path of the hunt (step 7, H4) |

Catch problems **early**: read `health.reasons` and `shards_detail` before triage. A shard that's `blocked` means Apple 403'd that runner, and the data is thinner than usual. That's fine, but the report must say so in its first lines.

### 1. Triage

Rebuild the digest with the ledger so used apps are flagged:

```bash
python scout/digest.py --data ../data --out /tmp/digest.md --ledger ideas/ledger.json && cat /tmp/digest.md
```

Read the digest's **Early surges** table first. A surge (a pain that started in the last 14 days in a mid-sized app) is the highest-value lead, because fast followers haven't shipped yet. Always put the top 1–2 non-platform surges on the shortlist, and check how many alternatives already have the wedge: few or small ones means the window is open.

From the digest, shortlist **8–12 pain clusters**. A cluster is one specific frustration ("lifetime unlock removed, now subscription only"; "can't export to CSV"; "forced account just to log water"), not an app. Look for:

| Opportunity type | What it looks like | Typical idea shape |
| --- | --- | --- |
| Paywall / price | everything moved behind a subscription, price hikes, "used to be free" | cheaper or one-time-purchase focused alternative |
| Removed / regressed | a loved feature removed, redesign made it worse | the old workflow, done well |
| Missing feature | the same request in many reviews, ignored for months | focused app built around that feature |
| Bloat | "I just want X", app grew into a platform | single-purpose, fast app |
| Forced account / privacy | sign-up walls, tracking, permissions for no reason | local-first, no-account version |
| Ads | ad after every action | paid / clean version |
| Locale gap | no Arabic / RTL, wrong calendar, not in my country, wrong units or currency | the same tool, done right for that market |
| Abandoned | still charting but no update in 12+ months, bugs piling up | modern replacement |

**Focus segments.** The digest has a section per focus segment (keyword segments that aren't App Store genres, defined in `collector/config.json` → `focus_segments`; currently **islamic**: Quran, prayer times, qibla, adhkar/dua, hadith, Ramadan). Always review each segment section and put its best 1–2 clusters on the shortlist when they exist. They pass the same gates as everything else; say in the report how the segment did even when nothing qualifies.

**Not opportunities** on their own: crashes and bugs (unless chronic for 6+ months across versions), refunds and support disputes, account bans, outages, content complaints, "I hate the new logo". Note them only as context.

Use the CLI to read the real reviews behind each cluster:

```bash
python scout/reviews.py --data ../data app <appId> --since <90 days ago>        # one app
python scout/reviews.py --data ../data search "lifetime"                        # same complaint across apps
python scout/reviews.py --data ../data competitors "habit"                      # who else charts in this space
```

### 1b. Re-open queue (do this before new clusters)

`ideas/reopen.json` lists clusters rejected under the old rule ("an alternative exists, so drop it") with strong evidence. They didn't fail on pain or build fit. Each day, re-evaluate the **top 4 still open** (highest `evidence_reviews` first) with the current rules: wedge, alternative's own reviews, hard-kill test, gates, score. Refresh their evidence with `reviews.py` if they're in the 7-day window, and add them to a targeted run's ids if not. Mark each `reopened: <date>` with the outcome. One that scores ≥ 3.6 is an idea; remove it from `rejected` in the ledger and add it to `ideas`.

### 1c. Self-audit (catch a broken rule early)

Count `ideas/ledger.json` → `rejected` by `reason_type` for the **last 3 days**. If there were 0 ideas in those 3 days and one reason type accounts for more than half of the rejections, add a **Calibration warning** at the top of the report: the rule, the count, and 2 examples where it may be wrong. A single rule killing most clusters is a sign the rule is miscalibrated, not that pain is absent. Every new `rejected` entry must carry a `reason_type`, one of `evidence` (Gate A), `build` (Gate B), `excluded`, `ios-builtin`, `dominant-free-alternative` (hard kill b), `no-wedge`, `score`, `other`.

### 2. Validate (top 3–6 clusters)

For each cluster, gather:

1. **Volume and spread** — how many low-star reviews in the last 90 days, how many storefronts, how many *different* apps share it.
2. **Persistence** — first and latest dates; does it span several versions?
3. **Proven demand** — incumbent ratings count, charts presence, grossing presence, price. Big, paying user bases with a shared frustration are the best signal.
4. **Willingness to pay** — "I'd pay", "I paid for", complaints about price (people already pay for this category), paid-chart presence.
5. **Off-store corroboration** — 2–4 WebSearch queries, e.g. `<app name> alternative reddit`, `<app name> <complaint> reddit`, `"<app name>" removed <feature>`, `best <category> app without subscription`. Reddit is only reachable through search results; fetch a result page if it loads, otherwise use the snippet. Record URLs.
6. **Competition and wedge** (scored, not a kill): find the best 2–3 alternatives (`reviews.py competitors` plus WebSearch: `<category> app no subscription`, `<category> app one time purchase`, `<feature> app ios`, `<incumbent> alternative reddit`). In a proven category an alternative almost always exists. That's normal and isn't a reason to drop the cluster. Instead:
   - **Name the wedge**: one concrete thing the idea does that *both* the incumbent and the best alternative don't (one-time purchase where they're subscription-only, no account, imports the incumbent's export, works offline, Arabic/RTL done right, a niche workflow they ignore, no AI, the old feature back). If you can't name a wedge in one sentence, that's a real reason to reject.
   - **Check the alternative's own reviews** (`reviews.py app <id>` if it's in the data, otherwise its App Store page via WebSearch). An alternative with its own paywall or ad complaints is weak competition.
   - **Hard kill only when**: (a) iOS itself does it free (AirPrint, Photos, Files, built-in Passwords/2FA, Apple Podcasts…), or (b) the alternative is free, no ads, no account, ★4.6+ with 20k+ ratings, has the exact thing users ask for, *and* its own low-star reviews don't share the complaint. Write which of (a)/(b) applied. "Alternatives exist" on its own is never the reason.

### 3. Gate A — is the pain real? (all must pass)

- ≥ 15 relevant low-star reviews in the last 90 days, **or** ≥ 8 across ≥ 2 different apps
- seen in ≥ 2 storefronts, or in ≥ 2 apps
- at least one review in the last 30 days
- the incumbent has ≥ 1,000 ratings or charts in ≥ 3 storefronts
- not just a bug the incumbent will ship a fix for next week

**A2 — alternative evidence path** (same strength, different sources; use it only when reviews alone fall short): ≥ 8 relevant low-star reviews across ≥ 2 storefronts **plus** ≥ 3 independent off-store threads from the last 12 months (Reddit, forums, Apple Community, Product Hunt comments) describing the same pain in their own words. Link every thread in the brief. Two posts by one person, or a vendor's blog, don't count.

### 4. Gate B — does it fit app-factory? (all must pass)

- Stack: Expo (React Native) + Expo Router + TypeScript, Supabase (Postgres/RLS, Auth, Storage, Edge Functions), RevenueCat with one `pro` entitlement, Sentry. iOS first.
- 14 days to App Store submission for one developer.
- One core loop a new user completes in under 60 seconds.
- At most 5 screens beyond onboarding, paywall and settings.
- One paid tier (`pro`), and the free tier is genuinely useful.
- No social features, chat, feeds, maps, AI features or admin panel **unless they are the core loop** (and then flag the cost).
- No hardware or Apple-only APIs Expo can't reach well: watchOS apps, CarPlay, keyboard extensions, Screen Time / FamilyControls, Safari extensions, deep HealthKit work, always-on background location. Home-screen widgets and Live Activities need native extension work: allowed only if not the core, and flag them.
- No licensed content or data you can't get (music catalogs, sports data, live TV, bank feeds), no marketplace that needs two sides, no regulated domain (the excluded categories).
- Guideline 4.3 (spam / copycat): Apple rejects templated clones, near-duplicates and fleeceware, not good alternatives. Risk is **high** only for an undifferentiated clone in a template category (flashlight, QR scanner, generic tracker) with no visible wedge. A quality app whose wedge shows on the first screen is acceptable even in a crowded category. Note the risk in the brief; don't use it as a blanket rejection.

#### Extra checks for the islamic segment

- **Correctness is the product.** Prayer times must come from a proven calculation library (e.g. adhan-js, MIT) with selectable calculation method, Asr madhab and high-latitude rule; a wrong time is an instant 1★. Qibla needs location plus the compass (expo-location, expo-sensors) and calibration guidance.
- **Content rights.** Quran Arabic text from a verified source used unmodified with attribution (e.g. Tanzil); translations and tafsir carry their own licences; recitation audio is copyrighted per reciter. If the idea depends on content you can't clearly license, it fails Gate B.
- **Notifications.** Adhan alerts are scheduled local notifications; iOS caps pending notifications at 64, so the app must reschedule on a rolling window. Custom adhan sounds must be ≤ 30 s. Flag it in Stack fit.
- **Excluded inside the segment:** zakat calculators, Islamic banking/investing (finance), religious Q&A that needs scholars, and halal scanners that need a product database you can't get.
- **Timing.** Demand peaks in Ramadan (next one starts around early-to-mid February 2027; confirm the date with a search). An idea that can ship before then gets a "why now" bonus; say so in the brief.
- **Tone.** Reviewers are often devout users: complaints about ads during recitation, inappropriate ads, paywalled basic worship features, or tracking are strong, specific signals. Treat them with care and quote them respectfully.

### 5. Score what passed both gates (1–5 each)

| Criterion | Weight | 5 looks like |
| --- | --- | --- |
| Evidence strength (volume × spread × recency) | 25% | 50+ recent reviews, several apps and storefronts |
| Proven demand (incumbent size, grossing, paid) | 20% | 100k+ ratings or top-grossing in many storefronts |
| Willingness to pay | 15% | people explicitly paying or asking to pay |
| Gap clarity (one clear thing to do better) | 15% | the fix fits in one sentence |
| Competition and wedge | 15% | 5: no good alternative; 4: alternatives have their own complaints and a clear wedge; 3: a strong alternative exists but the wedge is clear and visible; 2: weak wedge; 1: no wedge |
| Build fit (how comfortably it fits 14 days) | 10% | 3 screens, no native extensions, simple data |

Weighted score ≥ **3.6** → idea (max 3 per day, highest first). 3.0–3.6 → `watchlist` with what evidence would promote it. Below 3.0 or failed a gate → `rejected` with the one-line reason (only for clusters you seriously looked at).

If you have **at least one idea now**, go to step 6. If not, go to step 7 (hunt). Don't write the report yet.

### 7. Hunt loop: keep digging until one idea passes

Run rounds until an idea passes Gates A (or A2) and B with a score ≥ 3.6, or the budget runs out: **at most 3 targeted collector runs per day** (the tool enforces this, and waits for a 30-minute cool-off after the previous collection, because Apple soft-blocks runner IPs that come back too soon) and about **3 hours** of session time.

**H1. Pick up to 3 targets for the round**, in this order:
1. open targets in `ideas/hunt.json` (yesterday's unfinished hunt)
2. `watchlist` entries (they already have partial evidence)
3. today's near-misses: score 3.0–3.6, or failed only on Gate A volume or spread
4. discovery when there's nothing above: cross-app themes from the digest, "abandoned but still charting" apps, paid apps rated < ★4.4, focus segments (islamic). Use WebSearch for fresh pain too: `"looking for an app" <category> iphone reddit`, `<app> alternative reddit 2026`, `<app> removed feature reddit`. Turn what you find into app ids or search terms.
Skip anything in `rejected`.

**H2. Collect targeted evidence.** For each target, list the incumbent app ids plus 2–4 competitor search terms (`reviews.py competitors <kw>` gives charting competitors' ids). Combine all of the round's targets into one run:

```bash
python scout/collector_ctl.py targeted --app-ids <id,id,...> --terms "<term>,<term>" --storefronts-per-app 8
git -C ../data fetch -q --depth 1 origin data && git -C ../data checkout -q --detach FETCH_HEAD
```

That scans the incumbents and up to ~40 competitors across 8 storefronts with both sort orders, so complaints shared across competitors (the strongest signal) show up. If the cap is reached (exit code 3), continue with H4 only.

If the targeted run comes back FAILED with `soft-blocked` (Apple served empty pages to that runner; the canary check catches it in seconds), **don't conclude the apps have no complaints.** Do H4 for the same targets, then try the targeted run once more (the tool waits out the cool-off). Note both attempts in the report.

**H3. Re-validate** the targets with the new data: re-run the digest and `reviews.py`, then the step 2 checks, the gates and the score. Competitors with the same complaint count toward "≥ 2 different apps".

**H4. Off-store evidence** (every round, and the only route left when collection is blocked): search Reddit and forums for each target's pain and count independent threads for Gate A2. A target the store data can't settle is often settled here.

**H5. After each round:** if an idea passed, go to step 6. If not, update `ideas/hunt.json` with what each target has now and exactly what's still missing (e.g. "needs 3 more reviews in a second storefront" or "needs a second app with the same complaint"), drop targets that died (move them to `rejected`), and start the next round if budget remains.

**H6. Budget out with no idea:** write the report with a **Hunt status** section: the best 1–3 near-misses, their scores, the exact evidence gap for each, and the plan for tomorrow (which ids and terms go first). Save that plan in `ideas/hunt.json` so the next run starts there. Say plainly that no idea passed. Never relabel a near-miss as an idea.

`ideas/hunt.json` shape:

```json
{"updated": "YYYY-MM-DD", "open_targets": [{"key": "...", "incumbents": ["id"], "terms": ["..."], "why": "...",
  "evidence": "...", "missing": "...", "rounds": 1, "last_round": "YYYY-MM-DD"}], "closed": [{"key": "...", "outcome": "idea|rejected", "date": "..."}]}
```

### 6. Write the outputs

- `reports/YYYY-MM-DD.md` from `templates/report.md` — always, even on a zero-idea day.
- `briefs/YYYY-MM-DD-<slug>.md` from `templates/brief.md` — one per idea. It must be ready to hand to `/app-factory idea` (Phase 1): who, painful moment, what they do today, competitors with complaints and links, core loop, screens, `pro` split, kill criteria already checked, 4.3 risk.
- `ideas/hunt.json` — open and closed hunt targets (see step 7).
- `ideas/ledger.json` — append ideas (status `proposed`), update `watchlist` (bump `last_seen`, `evidence`), append `rejected`. Keep `key` short and stable: `<pain-type>:<incumbent-or-category>:<feature>`, e.g. `paywall:streaks:lifetime-unlock`.
- Update `README.md`'s "Latest" line with today's date and idea titles (or "no ideas today").

Then:

```bash
git add reports briefs ideas README.md && git commit -m "scout: YYYY-MM-DD — N ideas [skip ci]" && git push origin HEAD:main
```

If push fails, retry once after `git pull --rebase origin main`. Commit and push **after every hunt round** too (report so far, ledger, hunt.json), so a session that dies mid-hunt loses nothing. Finally, end with one line: "App Scout: N ideas — <titles>", or "App Scout: no idea passed after N hunt rounds — best lead <key>, needs <gap>". Put any collector failure first in that line.

## Quality bar (read before writing an idea)

- Would a sceptical indie developer read the evidence and agree the pain is real and recurring? If not, it's watchlist.
- Is the idea a **fix for a known pain**, not a new invention? "Like X but without Y" or "X's old feature Z, done well" is the right shape.
- Is there a reason these users would switch (and pay) on day one?
- Is it small? If the core loop needs more than one sentence, cut it down or drop it.
