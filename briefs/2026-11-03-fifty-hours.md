# Fifty Hours (working name) — a teen driving log for parents who just need the hours saved, without logins, ads or lost drives

- **Date:** 2026-11-03 · **Score:** 3.7 / 5 · **Ledger key:** `removed:roadready:teen-driving-log`
- **Pain type:** removed (regressed rewrite) + forced account + ads
- **Hand-off:** start a new app repo and run `/app-factory idea` with this file as the input.

## 1. The pain (Phase 1 §2)

- **Who:** US parents of 15–17-year-olds on a learner's permit, and the teens themselves. Most states require a set number of supervised hours before the licence test (e.g. [CA 50, TX 30, PA 65 per a competitor's guide](https://modadriving.com/blog/switching-from-roadready); all states in the [IIHS table](https://www.iihs.org/research-areas/teenagers/graduated-licensing-laws-table)).
- **Painful moment:** two. Getting into the car and being forced through a login, an ad and an update before the drive can start. And, worse, opening the app before the road test and finding hours gone.
- **What they do today:** put up with RoadReady because their DMV recommends it, keep a paper or Notes backup alongside it (20 of the 87 reviews mention paper, notes or manual logging), or give up on the app.
- **Severity:** 5/5 — logging is compulsory, runs for 6–12 months, and a lost log can mean redoing hours right before the test.
- **Why now:** RoadReady's June 2026 rewrite ([MassDOT announced the "enhanced" app on 2026-06-18](https://www.mass.gov/news/massdot-rmv-announces-enhanced-roadreadyr-app)) added driver scoring, and reviewers report ads and new logins alongside it. Low-star reviews are rising every month: Jun 19, Jul 21, Aug 14, Sep 31, Oct 42.

## 2. Evidence

| Source | Count / signal | Window | Storefronts |
| --- | --- | --- | --- |
| RoadReady (Safe Roads Alliance), all low-star reviews | 87 in 90 days, 128 since May, across 17 versions (3.4.x) | 2026-05-18 → 2026-10-30 | us (US-only app) |
| Same 87, by theme (keyword counts, a review can hit several) | login / account 51, lost hours 27, telematics scoring wrong 20, paper or manual fallback 20, ads 14, "just want it simple" 13, repeat families on a 2nd–5th child 9 | | us |
| RoadReady Ohio (same vendor, separate listing, 1.6k ratings) | 6 in 90 days, 25 since 2025-11, same login and lost-drive complaints | 2025-11-11 → 2026-10-04 | us |
| Aceable Drivers Ed (106k ratings, another vendor) | 2 reviews on its built-in driving log, one saying an update "killed previously logged night hours" | 2026-10-16 → 2026-10-20 | us |
| RoadReady rating | ★2.9 from 19,012 ratings. A [listing snapshot from before the rewrite](https://apps.appfollow.io/ios/roadready/699534935?country=us) (last updated 2026-03-25) shows 2.1★, so low ratings aren't new | | us |
| Google Play | ★4.0, ~4k reviews, 500k+ downloads; latest shown reviews (Sept 2026) report lost hours and drives after the update | 2026-09 | [link](https://play.google.com/store/apps/details?id=com.saferoadsalliance.roadready&hl=en_US) |
| Off-store threads | No independent Reddit or forum threads found (search rarely reaches Reddit). The only write-up of the failure is a competitor's. Gate A passes on reviews, so A2 isn't needed | | |

Representative reviews (≤ 25 words each):

- 1★ us 2026-10-14 v3.4.15 — "When the app logged us out, we log back in, all 6 months for drivers logs are gone"
- 1★ us 2026-09-24 v3.4.14 — "And why login at all? It's pointless. I just need to log a drive."
- 1★ us 2026-09-20 v3.4.13 — "we're just about ready for his driver's test, and it just dumped about 10 of his night hours"
- 1★ us 2026-10-15 v3.4.15 — "It interrupts entering of every drive with ads which transfer you to another website."
- 2★ us 2026-09-29 v3.4.14 — "I have used this app for 3 children now to log their driving hours. It has been a huge pain each time."
- 1★ us 2026-09-08 v1.0.11 (RoadReady Ohio) — "crashing and losing entire drive info on long road trips"

Off-store links:

- [Your RoadReady App Stopped Working](https://modadriving.com/blog/switching-from-roadready) — Moda's blog, 2026-06-29 (a competitor, so not independent)
- [RoadReady on Google Play](https://play.google.com/store/apps/details?id=com.saferoadsalliance.roadready&hl=en_US)
- [r/Denver thread (mirror)](https://reddit.sentinel-team.org/posts/1rq2ayb/snapshots/2026-03-14T00%3A48%3A46.9923Z) — from 2025: transcribing short drives onto the paper form is "a huge pain"; the app's printout was accepted at one DMV visit

## 3. Incumbents and competitors (Phase 1 §4)

| App | Rating · ratings | Price | Charts | What reviewers complain about | Link |
| --- | --- | --- | --- | --- | --- |
| RoadReady | ★2.9 · 19k | Free with ads | 1 storefront (us) | Logouts, lost hours, ads, wrong telematics, 15-minute entry | [App Store](https://apps.apple.com/us/app/roadready/id699534935) |
| RoadReady Ohio | ★4.7 · 1.6k | Free | no | Same logout and lost-drive issues | [listing data](https://apps.appfollow.io/ios/roadready-ohio/6748363429?country=us) |
| Moda | 4 reviews (3 are 5★) | [$4.99 one-time](https://modadriving.com/blog/switching-from-roadready) | no | "Only one supervisor": can't link the second one as advertised | [blog](https://modadriving.com/blog/switching-from-roadready) |
| LaneUp | none yet | Free | no | Family account, GPS routes, state PDFs, curfew alerts | [App Store](https://apps.apple.com/us/app/laneup/id6760084574) |
| DriveClock Log | none yet | R$24.90 one-time (about $5) | no | Timer, 50 states, PDF with signature blocks, iCloud | [App Store](https://apps.apple.com/br/app/driveclock-log/id6759814686) |
| Dryves | 2 ratings | Free (tips) | no | No account, RoadReady import, Siri, CarPlay; last update 2026-02 | [App Store](https://apps.apple.com/jp/app/dryves/id6759067319) |
| Student Driving Log | 16 reviews | Free | no | "Only goes in 5 minute intervals" | [App Store](https://apps.apple.com/ca/app/student-driving-log/id6472604271) |
| Teen Driving Log | ★4.3 · 159 | $1.99 | no | Last updated 2020 | [App Store](https://apps.apple.com/app/id385816093) |
| New Drive | ★2.4 · 7 | $0.99 | no | Last updated 2024 | [App Store](https://apps.apple.com/app/id1058675322) |
| Teen Driving Log. GUIDE2Safeti | ★3.7 · 6 | $14.99/mo | no | Coaching platform, not a log | [App Store](https://apps.apple.com/us/app/guide2safeti/id6479383022) |

**Kill check:** searched "teen driving log", "permit hours log", "student driver log", "RoadReady alternative", and scanned 13 logging apps plus term competitors in the targeted run (5 more returned no review data: LaneUp, DriveClock, iLog, Teen Driver, Licence Ready). **No log app has thousands of ratings**, or even more than 159 outside RoadReady's own listings, so the kill rule doesn't fire. But the field isn't empty: about 15 small apps exist, and Moda, LaneUp and Dryves already pitch at RoadReady's users. That's why competition scores only 3. Aceable's log is tied to its paid course.

**State acceptance:** in the states checked, RoadReady is recommended, not mandatory. Ohio: [paper logs are fine](https://www.wvxu.org/2025-09-29/as-a-new-law-takes-effect-ohio-rolls-out-a-new-app-to-help-teens-learn-good-driving-habits), though RoadReady Ohio can sync to the BMV. Massachusetts: [the parent certifies the hours on test day](https://centralmasafety.com/how-to-use-the-roadready-app-for-massachusetts-teen-drivers/). Maryland: [app export is signed and presented](https://mva.maryland.gov/Pages/NewsDetails2.aspx?NR=2019149). Official forms are public ([MA](https://www.mass.gov/doc/supervised-driving-log/download), [NC](https://www.ncdot.gov:443/dmv/downloads/Documents/adult-driving-log.pdf), [MI](https://www.michigan.gov/documents/sos/Michigan_supervised_driving_log_572744_7.pdf)). Check each state before claiming "accepted" in marketing, and never imply state endorsement.

## 4. The idea (Phase 1 §3, §5)

- **Positioning (one sentence):** RoadReady's old simple log, without the login, the ads or the risk of losing your hours.
- **Differentiator visible on the first screen:** the app opens straight to one big **Start Drive** button and your hours so far. No account, no sign-in, ever. A line under it: "Saved on this phone. Nothing to log into."
- **Core loop (< 60 s):** open, tap Start (or add a past drive to the exact minute), tap Stop, confirm the supervisor. Day and night hours split automatically.
- **Screens (≤ 5, excluding onboarding / paywall / settings):**
  1. Home: Start Drive, hours rings (total and night) against the state's requirement
  2. Active drive: running timer, Stop
  3. Log: all drives, add or edit to the minute
  4. Export: signed PDF log and CSV
  5. Family: join with a short code so a second parent can log on their phone
- **Cut from v1 (goes to LATER.md):** GPS routes, telematics and scoring, weather, CarPlay, widgets, Live Activity, lessons or curriculum, Android.

## 5. Money (Phase 1 §6)

- **Free:** unlimited logging for one learner, day/night totals, state requirement tracker, plain PDF log. Genuinely enough to finish a permit. No ads, ever.
- **`pro`:** second supervisor sync, more learners (siblings), official state-form PDFs, CSV backup, RoadReady history import · price anchors from incumbents: $0.99 New Drive, $1.99 Teen Driving Log, $4.99 Moda, about $5 DriveClock, $14.99/mo GUIDE2Safeti · suggested: **$4.99 one-time** for the family through RevenueCat (non-consumable on the `pro` entitlement). No subscription: this is a 6–12 month job, and a sub would invite the reviews RoadReady is getting.
- **Willingness-to-pay evidence:** indirect. Paid log apps exist at $0.99–$4.99 and Teen Driving Log has sold at $1.99 for years. No reviewer in the set offers to pay, and the incumbent is free. This is the weakest part of the case (scored 2.75).

## 6. Stack fit (app-factory contract)

- **Supabase use:** local SQLite is the source of truth, so a sync failure can never lose a drive. Supabase anonymous auth plus `families`, `learners`, `drives` tables with RLS for second-parent sync and restore. No email or phone required. No edge functions needed for v1.
- **Native risk:** none. The timer is computed from a saved start timestamp, so it survives the app being killed and needs no background execution. Sunset times come from a sun-position library (e.g. suncalc, MIT) using the state or one coarse location read, no tracking. PDFs through expo-print.
- **Data collected (seed for DATA.md):** learner's first name, state, permit date, drive start/stop times, day/night, supervisor's name, optional notes. No email, no location history, no analytics beyond Sentry crash reports. Teens are users, so keep to no ads and minimal data, and have the parent be the one who sets it up.
- **State data:** requirements for 50 states + DC from the IIHS table, shipped in the app and easy to update. Plain log for all states, official forms for about 5 at launch.
- **Estimated fit in 14 days:** comfortable — simple data, no extensions. State-form PDFs are the only part that can sprawl, so cap the launch list.
- **Guideline 4.3 risk:** medium. There are about 15 small log apps, though not a mass clone category. The first screen's no-account promise is the difference to show. Avoid "official", "DMV-approved" and RoadReady's name in the title.
- **Risks to weigh before starting:**
  - **Distribution:** families reach RoadReady through DMV pages, not App Store search. Moda has only a handful of reviews after months of targeting the same users, so plan App Store keywords and content for parents searching "RoadReady not working".
  - **Timing:** several apps got here first, and RoadReady could stabilise. A fix wouldn't remove the ads or the logins.
  - **Evidence caveat:** the second app that clears Gate A is the same vendor's Ohio listing. Aceable is the independent one, with only 2 reviews. It's a US-only pain with one storefront.
