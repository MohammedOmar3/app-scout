# SCOUT.md — the daily analysis run

You are the analysis half of App Scout. A GitHub Actions job has already pulled today's Apple chart and low-star review data into the `data` branch. Your job: turn proven, repeated user pain in trending iOS apps into **0–3 small app ideas** that fit the app-factory pipeline, with evidence, and write them to this repo.

**Zero ideas is a good outcome.** Never pad. A weak idea costs the user two weeks.

## Hard rules

- **Free sources only.** Apple data in the `data` branch, plus WebSearch / WebFetch of public pages. Never sign up for, or recommend paying for, a data tool. If a page is paywalled or blocked, skip it and move on.
- **iOS only, all storefronts.** Reviews come in many languages: read and translate them yourself. A complaint repeated across storefronts is stronger evidence.
- **Excluded categories:** games, medical, finance (and anything that is really one of these under another genre: symptom tracking, diagnosis, budgeting with bank links, trading, crypto, lending). The collector removes them by genre; you catch the disguised ones.
- **Must fit app-factory** (see Gate B). If it can't ship as an Expo + Supabase + RevenueCat app in 14 days, it is not an idea.
- **No repeats.** Read `ideas/ledger.json` first. Don't propose anything already in `ideas` or `rejected`. Items in `watchlist` can be promoted when new evidence arrives.
- **Evidence, not vibes.** Every claim in a brief points at a review (store, date, stars) or a URL.
- Short review quotes are fine (≤ 25 words each, max 6 per brief). Paraphrase web articles; never copy them.

## Steps

### 0. Set up and check the data

```bash
git fetch --depth 1 origin data && git worktree add ../data FETCH_HEAD   # or: git -C ../data pull
cat ../data/latest/run.json | head -60
```

If `run.json` is missing, or its `date` is more than 1 day old, or `apps_scanned` is 0: write a short report that says the collector didn't produce data (include `error_samples`), commit it, and stop. Do not invent ideas from web search alone.

If `partial` is true or failures are high, continue but say so in the report.

### 1. Triage

Rebuild the digest with the ledger so used apps are flagged:

```bash
python scout/digest.py --data ../data --out /tmp/digest.md --ledger ideas/ledger.json && cat /tmp/digest.md
```

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

### 2. Validate (top 3–6 clusters)

For each cluster, gather:

1. **Volume and spread** — how many low-star reviews in the last 90 days, how many storefronts, how many *different* apps share it.
2. **Persistence** — first and latest dates; does it span several versions?
3. **Proven demand** — incumbent ratings count, charts presence, grossing presence, price. Big, paying user bases with a shared frustration are the best signal.
4. **Willingness to pay** — "I'd pay", "I paid for", complaints about price (people already pay for this category), paid-chart presence.
5. **Off-store corroboration** — 2–4 WebSearch queries, e.g. `<app name> alternative reddit`, `<app name> <complaint> reddit`, `"<app name>" removed <feature>`, `best <category> app without subscription`. Reddit is only reachable through search results; fetch a result page if it loads, otherwise use the snippet. Record URLs.
6. **Existing fix (kill check)** — does an app already solve this well? Use `reviews.py competitors` plus WebSearch (`<category> app no subscription`, `<category> app one time purchase`, `<feature> app ios`). If a well-rated (★4.5+, thousands of ratings), cheap or free app already does exactly this, the cluster is dead: put it in `rejected` with the app name.

### 3. Gate A — is the pain real? (all must pass)

- ≥ 15 relevant low-star reviews in the last 90 days, **or** ≥ 8 across ≥ 2 different apps
- seen in ≥ 2 storefronts, or in ≥ 2 apps
- at least one review in the last 30 days
- the incumbent has ≥ 1,000 ratings or charts in ≥ 3 storefronts
- not just a bug the incumbent will ship a fix for next week

### 4. Gate B — does it fit app-factory? (all must pass)

- Stack: Expo (React Native) + Expo Router + TypeScript, Supabase (Postgres/RLS, Auth, Storage, Edge Functions), RevenueCat with one `pro` entitlement, Sentry. iOS first.
- 14 days to App Store submission for one developer.
- One core loop a new user completes in under 60 seconds.
- At most 5 screens beyond onboarding, paywall and settings.
- One paid tier (`pro`), and the free tier is genuinely useful.
- No social features, chat, feeds, maps, AI features or admin panel **unless they are the core loop** (and then flag the cost).
- No hardware or Apple-only APIs Expo can't reach well: watchOS apps, CarPlay, keyboard extensions, Screen Time / FamilyControls, Safari extensions, deep HealthKit work, always-on background location. Home-screen widgets and Live Activities need native extension work: allowed only if not the core, and flag them.
- No licensed content or data you can't get (music catalogs, sports data, live TV, bank feeds), no marketplace that needs two sides, no regulated domain (the excluded categories).
- Guideline 4.3 (spam / copycat) risk is acceptable: the differentiator must be visible on the first screen, not "the same app but cheaper" in a crowded template category (flashlight, QR scanner, generic habit tracker) unless the evidence is overwhelming.

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
| Weak competition (kill-check margin) | 15% | no good alternative found |
| Build fit (how comfortably it fits 14 days) | 10% | 3 screens, no native extensions, simple data |

Weighted score ≥ **3.6** → idea (max 3 per day, highest first). 3.0–3.6 → `watchlist` with what evidence would promote it. Below 3.0 or failed a gate → `rejected` with the one-line reason (only for clusters you seriously looked at).

### 6. Write the outputs

- `reports/YYYY-MM-DD.md` from `templates/report.md` — always, even on a zero-idea day.
- `briefs/YYYY-MM-DD-<slug>.md` from `templates/brief.md` — one per idea. It must be ready to hand to `/app-factory idea` (Phase 1): who, painful moment, what they do today, competitors with complaints and links, core loop, screens, `pro` split, kill criteria already checked, 4.3 risk.
- `ideas/ledger.json` — append ideas (status `proposed`), update `watchlist` (bump `last_seen`, `evidence`), append `rejected`. Keep `key` short and stable: `<pain-type>:<incumbent-or-category>:<feature>`, e.g. `paywall:streaks:lifetime-unlock`.
- Update `README.md`'s "Latest" line with today's date and idea titles (or "no ideas today").

Then:

```bash
git add reports briefs ideas README.md && git commit -m "scout: YYYY-MM-DD — N ideas" && git push origin HEAD:main
```

If push fails, retry once after `git pull --rebase origin main`. Finally, send one short push notification if the tool is available: "App Scout: N ideas today — <titles>" or "App Scout: nothing strong today".

## Quality bar (read before writing an idea)

- Would a sceptical indie developer read the evidence and agree the pain is real and recurring? If not, it's watchlist.
- Is the idea a **fix for a known pain**, not a new invention? "Like X but without Y" or "X's old feature Z, done well" is the right shape.
- Is there a reason these users would switch (and pay) on day one?
- Is it small? If the core loop needs more than one sentence, cut it down or drop it.
