# Plain Kcal (working name) — a calorie diary for people in Germany, Austria, France, Italy and the Netherlands who just want to log food, without ads after every entry, a 20-question interrogation or streak animations

- **Date:** 2026-11-08 · **Score:** 3.9 / 5 · **Ledger key:** `paywall:yazio:ads-and-extras` (re-opened key kept)
- **Pain type:** bloat + ads (an ad after every logged food, popup coaching and streaks you can't turn off, a long questionnaire on first launch and again after a few days away), plus paywall (planning ahead and copying foods moved to Pro)
- **Scoring:** evidence 4.5 · demand 5 · willingness to pay 3 · gap clarity 4 · competition 3 · build fit 3 = **3.9** (see §8; an independent check agreed: 3.93, and about 3.7 with stricter evidence and competition scores)
- **Origin:** re-opened from `paywall:yazio:ads-and-extras` (rejected 2026-11-07 in the run *before* the rule change, as "crowded category, needs a food database"). Under the current rules a crowded category is scored, not a kill, and the food data turns out to be free (§6). The cluster has also grown: 123 → 289 low-star reviews in 90 days, now that a targeted rescan on 2026-11-08 added at, be and us.
- **Hand-off:** start a new app repo and run `/app-factory idea` with this file as the input.

## 1. The pain (Phase 1 §2)

- **Who:** adults in German-, French-, Italian- and Dutch-speaking Europe who count calories daily, often for years, and log 4–10 foods a day. Many have used Yazio for a long time; some pay for Pro.
- **Painful moment:** right after logging a food. In the free tier an unskippable ad plays after each entry (several reviewers say they have to close and reopen the app to get past it). Paying users still get the streak, "morning box / evening box" and coaching animations, which can't be turned off. After a few days away, the app makes you redo a goals questionnaire before you can log again.
- **What they do today:** put up with it, pay for Pro (and still get the animations), or delete it and look for "something simpler". A few go back to paper.
- **Severity:** 4/5. Logging is a many-times-a-day habit, so friction on every entry adds up. Reviewers say the friction made them stop tracking.
- **Why now:** the complaints are persistent and still coming on the newest builds (v26.41 → v26.44.1, 2026-11-02). In the storefronts the feed covers for the whole period (at, fr, nl, fi, be, gb, us), relevant low-star reviews ran 13–16 a month from May to July and 20–24 a month from August to October. The October jump in the raw totals is partly coverage: the de feed only reaches back to 10-15. The new-year diet season starts in about 7 weeks, and a 14-day build ships before it.

## 2. Evidence

All counts are from the App Scout data branch (daily run plus targeted run 42442300015 on 2026-11-08, 8 storefronts per app), low-star = 1–2★. The de feed only reaches back to 2026-10-15 (feed cap), so de is undercounted.

| Source | Count / signal | Window | Storefronts |
| --- | --- | --- | --- |
| Yazio, all low-star reviews | 289 | 2026-08-10 → 2026-11-06 | de, fr, it, at, nl, us, fi, gb, be |
| Yazio, about ads / questionnaire / popups-streaks-gamification | **140** (82 in the last 30 days); an independent hand read of the first 213 found 116, matching the keyword count | same | de 48, fr 33, it 22, at 17, nl 9, us 6, gb 2, fi 2, be 1 |
| …ads (mostly "after every entry") | ~66 | same | |
| …popups, animations, streaks, gamification | ~52 | same | |
| …onboarding or repeat questionnaire | ~37 | same | |
| …reviewer says they pay for Pro | ~13 (hand count of the first 116) | same | |
| Lifesum (151k ratings), premium popups, bloat, questionnaire | ~9 of 76 low-star (most others are v24 lag and bugs) | same | se, no, dk, us |
| MyNetDiary (172k), upgrade popups and nags | ~5 of 22 | same | us, gb |
| Cronometer (100k ratings), ads / streak notifications | 8 of 28 | same | us 7, gb 1 |
| Yazio charts | top-grossing in **11 storefronts** (de, at, ch, fr, be, nl, lu, fi, hu, gr, by), best rank 18; ★4.7 from 51.7k US ratings | 2026-11-08 | |
| Off-store | 1 thread ([r/Switzerland, ~Oct 2025](https://reddit.sentinel-team.org/posts/1sqlkop/snapshots/2026-04-20T23%3A32%3A12.999426Z): free version "got completely enshittified with the new update"). Several vendor write-ups target Yazio refugees (below). Gate A passes on reviews alone, so A2 isn't needed | | |

Representative reviews (≤ 25 words, translated):

- 2★ de 2026-11-04 v26.44.1 — "Using it for years, and it's worse than ever. An ad after every food added. No planning ahead or copying foods without Premium."
- 1★ fr 2026-11-05 v26.44.1 — "50 questions, only for it to insist you pay in the end. Avoid."
- 2★ de 2026-10-29 v26.43.2 — "When can we finally switch off all this gamification, streak freezes and so on? Even with a Premium subscription it can't be disabled."
- 1★ it 2026-10-25 v26.42.0 — "Every time you log a meal they slip in an ad you can't skip or close; you have to close the app and reopen it."
- 1★ de 2026-10-18 v26.41.2 — "I pay for this app and just want to track things, without constantly going through this questionnaire circus."
- 1★ gb 2026-10-30 v26.43.2 — "The onboarding flow was so long, tedious and unnecessary that I had to delete half way through and switched to something simpler."

Off-store links (vendor posts aimed at Yazio refugees; they show the market is being courted, they don't count as independent evidence):

- Nutrola, "Kostenlose Alternativen zu Yazio 2026" — https://nutrola.app/de/blog/free-alternatives-to-yazio-2026
- Fitia, "Best Yazio alternatives 2026" — https://fitia.app/learn/article/best-yazio-alternatives-2026/
- AlternativeTo, Yazio alternatives — https://alternativeto.net/software/yazio/

## 3. Incumbents and competitors (Phase 1 §4)

| App | Rating · ratings | Price | Charts | What reviewers complain about | Link |
| --- | --- | --- | --- | --- | --- |
| Yazio (incumbent) | ★4.7 · 51.7k (us) | free + Pro (reviewers cite €47–60/yr) | grossing in 11 EU storefronts | ads after every entry, questionnaire, unskippable gamification, planning/copying paywalled, no offline | https://apps.apple.com/de/app/id946099227 |
| Lifesum | ★4.6 · 151k | free + Premium | 3 storefronts | v24 redesign laggy, long questionnaire (se, no, dk) | https://apps.apple.com/app/id286906691 |
| Fddb | DE leader (US listing ★4.6 · 28 ratings; it claims 11,500+ reviews) | free; **its listing says the free tier has no ads**; Premium ~€40/yr; account likely (the privacy label links email and user ID) | — | now pitching AI ("KI Kalorienzähler"); not in the review feed (0 reviews returned) | https://apps.apple.com/us/app/fddb-ai-calorie-counter-diet/id1105332761 |
| MyFitnessPal, Lose It, FatSecret, Cronometer (free tiers) | large | free with ads | many | ads (per Nutrola's comparison; Cronometer's own low-star reviews: "spammed with an ad I have to watch through") | — |
| MyNetDiary | ★4.8 · 172k (us); ★4.7 · 426 (de) | free + Premium; listing says "no ads, no account required" | 2 | upgrade popups mid-entry; English-only; a DE reviewer says German foods are missing | https://apps.apple.com/de/app/id287529757 |
| FatSecret | ★4.7 · 8.7k (de) | free | — | 3 of 79 low-star on these themes | https://apps.apple.com/DE/app/id347184248 |
| Calories Minute Access (fr) | ★4.4 · 206 | free, no ads, no account | — | tiny | https://apps.apple.com/fr/app/id832556415 |
| OpenNutriTracker | ★4.3 · 15 ratings | free, open source, no ads, no IAP | — | ~a third of foods missing or fail to scan, no HealthKit, clunky custom foods | https://apps.apple.com/app/id6451490901 |
| Mahlzait, Murmli, Swipe Calories, Kcalc and similar | small (under 5k ratings) | freemium | — | small; most are AI-photo or US-data apps | — |

**Kill check:**
- (a) iOS built-in: no. Health stores nutrition samples but has no food diary or food search.
- (b) dominant free alternative: no app found that is free, ad-free, account-free, ★4.6+ with 20k+ ratings **and** has good local food data for de/fr/it/nl. MyNetDiary is the closest (no ads, no account, ★4.8, 172k in the US), but it's English-only with US food data (426 ratings in de), and its own low-star reviews complain about upgrade popups mid-entry. **Fddb is the real competitor in Germany**: a free tier with no ads (per its listing) and a big German database. It likely needs an account, is far under 20k ratings on iOS, and is moving to AI, so (b) doesn't apply. But in de/at the wedge rests on no questionnaire, no gamification, offline and no account, not on "no ads". In fr, it and nl no strong ad-free local option was found (Calories Minute Access has 206 ratings). OpenNutriTracker has the right values, but only 15 ratings and gaps in its data.
- Searches run: "Yazio Alternative ohne Werbung", "yazio too many ads popups alternative reddit", "compteur calories sans pub sans abonnement", "OpenNutriTracker", "Mahlzait", "Murmli", "FDDB", plus an independent reviewer's own searches. The space is crowded with AI-photo trackers and US-data apps. Nobody visible combines "no ads, no questionnaire, no gamification, offline" with **national food tables** for Germany and France.

## 4. The idea (Phase 1 §3, §5)

- **Positioning (one sentence):** Yazio as it was years ago: open the app, search your country's foods, log, done. No ads, no questionnaire, no streaks, and it works offline.
- **Differentiator visible on the first screen:** first launch goes straight to today's diary with a search field. The only setup is one optional daily calorie number (with a "help me estimate" link, never forced). No ads anywhere, and no animations.
- **Core loop (< 60 s):** tap Breakfast → type "Haferflocken" or scan a barcode → pick a portion (g, piece, cup) → back to today's total. A second food takes about 5 s ("recent" and "copy yesterday's breakfast" are one tap).
- **Screens (≤ 5, excluding onboarding / paywall / settings):**
  1. **Today:** meals with totals, kcal left, a date strip, copy a meal to another day
  2. **Add food:** search (bundled national table plus recents and my foods, offline first), barcode scan through Open Food Facts, quick-add kcal
  3. **Food and portion:** amount, unit, macros per portion
  4. **Trends:** daily kcal and weight over 7 / 30 / 90 days (weight entered by hand)
  5. **My foods and meals:** custom foods, saved meal combos
- **Cut from v1 (goes to LATER.md):** AI photo logging, fasting timer, recipes from URLs, micronutrient dashboards, Apple Watch, widgets, social and coaching, exercise tracking beyond reading Health's active energy.

## 5. Money (Phase 1 §6)

- **Free:** unlimited logging, food search, barcode scan, custom foods, a daily calorie goal and macros, **planning ahead and copying meals** (both are Pro-only in Yazio, and reviewers named them), 30 days of trends. No ads, ever.
- **`pro`:** saved meals and recipes with per-portion totals, full trend history and weight goal line, per-meal targets, CSV export, sync across devices (Supabase), writing nutrition to Apple Health. Price anchors: Yazio Pro €47–60/yr (reviewers), Fddb Premium ~€40/yr (often discounted to €10–15). Suggested: €2.99/month, €17.99/year, €39.99 lifetime.
- **Willingness-to-pay evidence:** about 13 of the first 116 relevant reviewers say they pay for Yazio Pro and still hit the friction ("Ich zahle Geld für diese App…"). Yazio is top-grossing in 11 storefronts. One reviewer says the ads lost them as a repeat Pro buyer. Against that: many free-tier reviewers want it free ("let me laugh for free"). So the free tier must carry the core loop, and `pro` sells convenience, not removing pain.

## 6. Stack fit (app-factory contract)

- **Food data (the key risk, checked):**
  - **Germany:** Bundeslebensmittelschlüssel BLS 4.0, 7,140 generic foods and dishes, **CC BY 4.0** with the Max Rubner-Institut credited as publisher ([blsdb.de/download](https://blsdb.de/download); [heise](https://heise.de/-11123877)). Bundling in a paid app is allowed.
  - **France:** ANSES-CIQUAL, 3,484 foods, Licence Ouverte / Etalab (commercial reuse with attribution; [data.gouv.fr](https://www.data.gouv.fr/datasets/table-de-composition-nutritionnelle-des-aliments-ciqual-2020/informations), [ANSES](https://www.anses.fr/en/content/anses-ciqual-food-composition-table)). Confirm the 2025 release keeps the same licence.
  - **Branded products:** Open Food Facts (ODbL: attribution plus share-alike for the database, a custom User-Agent and per-endpoint rate limits; [conditions](https://support.openfoodfacts.org/help/en-gb/12-api-data-reuse/94-are-there-conditions-to-use-the-api)). Call it from the device for barcode lookups and cache the results locally. Don't merge OFF rows into the bundled BLS/CIQUAL file, so the share-alike rule doesn't spread to it.
  - **Italy and the Netherlands:** start with Open Food Facts plus a translated CIQUAL/BLS name index. Check the licences of Italy's CREA tables and the Dutch NEVO table (NEVO has use conditions) in Phase 1.
- **Supabase use:** optional account only for `pro` sync (Auth + one `entries` table with RLS) and a `foods_custom` table. Everything works local-first (SQLite through expo-sqlite, with the national table bundled as a read-only DB of about 5–10 MB). No edge functions needed in v1.
- **Native risk:** low. Barcode scanning uses expo-camera. Writing nutrition to Health is a pro extra, not the core (use an Expo HealthKit module, kept out of the core loop). No widgets in v1.
- **Data collected (seed for DATA.md):** food entries, weight entries, an optional calorie goal. No age, sex or body questionnaire required (an optional estimator stays on the device).
- **Estimated fit in 14 days:** tight but fits. 5 screens with simple data. The work is the food import (BLS/CIQUAL to SQLite with FTS search, synonyms and portion units) and search quality. Budget 3 days for it.

## 7. Risks and kill criteria (Phase 1 §8–9)

- **Guideline 4.3 risk:** medium. Calorie counters are a crowded template category (75 charting apps mention "calorie"). The wedge (local national food table, no ads, no questionnaire) has to be obvious in screenshots and on first launch. Don't ship a generic US-data clone.
- **Sensitive use:** calorie tracking can feed disordered eating. Don't allow goals below a safe floor without a warning, keep weight optional, and leave out "streak shame" (it's also the wedge).
- **Kill criteria:**
  1. *Search quality:* if, on day 2, typing 20 common German and French foods (Haferflocken, Vollkornbrot, Apfel, Gouda, baguette, yaourt nature…) doesn't return a sensible top-3 match from BLS/CIQUAL, stop. Data quality is the product. **Not yet checked.**
  2. *Licence:* if BLS or CIQUAL forbade bundling in a paid app, the local-data wedge would fall. **Checked:** BLS 4.0 is CC BY 4.0, and CIQUAL is Licence Ouverte (both need attribution).
  3. *Yazio reverses course:* an "ad-light" setting or a gamification toggle in the next release would weaken the wedge. Re-read Yazio's newest reviews before starting.
- **Open questions for Phase 1:** can users import Yazio history (via Yazio's GDPR data export) to make switching painless? Which storefront launches first? de/at is the biggest cluster, but Fddb is strongest there, and France (CIQUAL, 33 relevant reviews, no strong local ad-free app found) may be the easier first market. Should Italian or Dutch localisation make v1, or wait for v1.1?

## 8. Scoring notes

- **Evidence 4.5:** 140 relevant low-star reviews in 90 days (82 in the last 30) across 9 storefronts, persistent since at least May, plus smaller echoes in Lifesum (~9), Cronometer (8) and MyNetDiary (~5). Not a full 5, because it's mostly one app.
- **Demand 5:** grossing in 11 storefronts, and the category leaders have hundreds of thousands to millions of ratings.
- **Willingness to pay 3:** paying users complain (about 13), but free-tier users mostly want it free.
- **Gap clarity 4:** "just log, nothing else, with your country's foods" fits in one sentence. It isn't 5, because "simple and no ads" is a value proposition shared by many small apps.
- **Competition 3:** most big alternatives have ads or popups. Fddb (no ads in Germany) and MyNetDiary (no ads, US data) cover part of the wedge, and the small apps with the same values are tiny and weak on European data. The wedge is clear but not unique.
- **Independent check (sub-agent, 2026-11-08):** re-read all 213 then-stored Yazio low-star reviews by hand. It confirmed the quotes and translations, corrected the payer count and the trend claim, found Fddb's "no ads" free tier and MyNetDiary's "no account", and confirmed both licences. Its score was 3.93, or about 3.7 under stricter scoring.
- **Build fit 3:** a 5-screen app with simple data, but the food import and search quality take real time.
