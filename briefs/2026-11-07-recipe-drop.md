# Recipe Drop (working name) — save recipes from TikTok, Instagram, YouTube and any website, free to use, without a trial wall or a weekly import cap

- **Date:** 2026-11-07 · **Score:** 3.8 / 5 (conditional on the day-1 Instagram test, see §7) · **Ledger key:** `paywall:recime:forced-trial`
- **Pain type:** paywall (forced trial before first use, free tier capped at 5 imports a week), plus missing (the one-time incumbent, Paprika, can't import from social video)
- **Scoring:** evidence 4 (heavy, but mostly one app) · demand 5 · willingness to pay 3 · gap clarity 4 · competition 3 · build fit 3 = 3.8. An independent check of the counts, quotes and competitors agreed on 3.8; my first pass gave 4.2.
- **Origin:** re-opened from the 2026-11-02 rejection (SCOUT.md step 1b). It was rejected only because alternatives existed; Mela and Paprika are paid, so hard kill (b) never applied.
- **Hand-off:** start a new app repo and run `/app-factory idea` with this file as the input.

## 1. The pain (Phase 1 §2)

- **Who:** home cooks, mostly in the US, UK, Canada and Australia, who find recipes in TikTok, Instagram and Facebook reels and YouTube videos and want them saved as a usable recipe (ingredients and steps), not as a bookmark to a video.
- **Painful moment:** two moments. On first launch, after a 20-question onboarding, the "free" app shows a 7-day trial screen with no visible way to skip it. Later, on a free account, the sixth import of the week hits a paywall.
- **What they do today:** delete ReciMe and go back to screenshots, Notes or Pinterest boards. Or they use Paprika, which can't read Instagram, Facebook or YouTube (6 low-star Paprika reviews since June say so).
- **Severity:** 4/5. Nobody is harmed, but saving recipes is the whole reason to install, and the block comes before first use. 42 of the 168 low-star reviews also mention charges, refunds or cancelling.
- **Why now:** "not free" complaints go back to at least May 2026 (au, v5.2.x) and are still rising outside the US: gb, ca and au together had 21 in August, 40 in September and 46 in October. The US feed only reaches back to October, so the US jump that month is partly how much feed we can see, not proof of a change. Reviews on the latest version (v8.2.2, 2026-11-05) still describe the trial wall.

## 2. Evidence

| Source | Count / signal | Window | Storefronts |
| --- | --- | --- | --- |
| ReciMe, all low-star reviews | 168 in 90 days, across versions v6.1.4 → v8.2.2 (the US feed only covers October onward) | 2026-08-09 → 2026-11-05 | us 58, gb 56, ca 35, au 17, nz 1, mt 1 |
| ReciMe, about trial / paywall / price / limits | 134 (82 in the last 30 days) | same | us 49, gb 42, ca 29, au 13 |
| …of which forced trial before use | 58 | same | us 22, gb 21, ca 13, au 2 |
| …"says free but isn't" | 46 | same | us, gb, ca, au |
| …imports fail, or the weekly import cap | 22 fail, 14 cap | same | us, gb, ca, au |
| Paprika 3 (the main one-time alternative): can't import from Instagram, Facebook or YouTube | 6 | 2026-06-05 → 2026-10-15 | us, ca |
| ReciMe charts | grossing in 3 storefronts (us, gb, nz), best rank 1; ★4.8 from 328k ratings | collector run 2026-11-07 | |
| Off-store | No independent Reddit or forum threads found (2 searches). Three vendor write-ups describe the same cap and trial (below). Gate A passes on reviews alone, so A2 isn't needed | | |

Representative reviews (≤ 25 words each):

- 1★ us 2026-11-01 v8.2.0 — "Literally says 'ReciMe is free' but there's no exit button or way to get past this free trial screen."
- 1★ gb 2026-10-28 v8.2.0 — "I just want the free plan and if I like it then I'll get the paid plan."
- 1★ us 2026-11-01 v8.2.0 — "It let me upload 4 recipes then said I had to pay. Instant delete."
- 1★ ca 2026-10-24 v8.2.0 — "it presents a page where they'd like to offer you the first 7 days for free, and then you will have to pay"
- 1★ us 2026-10-13 v3.8.5 (Paprika) — "You cannot download recipes that you saved on Facebook and instagram"
- 1★ ca 2026-07-28 v3.8.5 (Paprika) — "If you get most of your recipes off YouTube, as I do, Paprika is useless."

Off-store links (all written by competitors, so not independent):

- [ReciMe App Review: Pros and Cons](https://www.plantoeat.com/blog/2025/01/recime-app-review-pros-and-cons/): Plan to Eat, 2025-01, updated 2026-06. Calls the 5-imports-a-week free plan a "bait and switch", and notes the trial asks for payment details upfront.
- [Recipe Apps Compared: Pricing Models for 2026](https://mymealticket.pages.dev/blog/recipe-apps-compared/): MyMealTicket, 2026-04. Covers ReciMe's cap, Paprika's lack of social import, and its own one-time model.
- [App to Save TikTok Recipes: 6 Compared](https://aldentekitchen.com/blog/best-recipe-apps-saving-tiktok-instagram-2026/): Aldenté, updated 2026-11-01. Compares free-tier import limits across 6 apps.

## 3. Incumbents and competitors (Phase 1 §4)

| App | Rating · ratings | Price | Charts | What reviewers complain about | Link |
| --- | --- | --- | --- | --- | --- |
| ReciMe | ★4.8 · 328k | Free, then Plus $39.99/yr after a 7-day trial ([Plan to Eat](https://www.plantoeat.com/blog/2025/01/recime-app-review-pros-and-cons/); Aldenté quotes $49.99/yr) | grossing us, gb, nz | Forced trial before first use, 5 imports a week, social imports failing, charges and refunds | [App Store](https://apps.apple.com/us/app/recime-recipes-meal-planner/id1593779280) |
| Paprika Recipe Manager 3 | ★4.9 · 54k | $4.99 one-time | grossing us, gb | Can't import from Instagram, Facebook or YouTube; messy web imports; Siri broken on iOS 27 | [App Store](https://apps.apple.com/us/app/paprika-recipe-manager-3/id1303222868) |
| Mela | ★4.7 · 2.1k ([appgoblin](https://appgoblin.info/apps/1548466041)) | Free download, one-time unlock ($4.99 per [MacStories](https://www.macstories.net/reviews/mela-1-6-adds-web-search-engine-and-recipe-import-from-youtube-instagram-and-tiktok-videos/), $6.99 per Aldenté) | no | Small. Last store update June 2025 (appgoblin). Reads video descriptions; MacStories reports about 7 in 10 imports work and doesn't say whether AI is used. Aldenté's blog says its store page doesn't list social import | [App Store](https://apps.apple.com/app/id1548466041) |
| Mr. Cook | 4.7 claimed, "145k users" | €7.99/mo or €39.99/yr, 7-day trial | no | Same pricing model as ReciMe, with AI recipe generation ([its comparison page](https://www.mrcook.app/en/compare/recime-alternative)) | |
| Pestle | ★4.7 · 1.8k | $2.99/mo, $24.99/yr, lifetime $39.99–49.99 | no | Imports Instagram, TikTok, Facebook and YouTube; Pro needed for the full app | [App Store](https://apps.apple.com/us/app/id1574776971) |
| Aldenté | rating count not reachable (store page blocked) | Unlimited free saving including social, Premium $47.99/yr | no | Small. Already ships the free-unlimited-social-saves wedge. Uses transcription for spoken recipes | [blog](https://aldentekitchen.com/blog/best-recipe-apps-saving-tiktok-instagram-2026/) |
| Copy Me That | ★4.6 · 1.2k | Free tier capped at 40 recipes | no | Imports Instagram | [App Store](https://apps.apple.com/US/app/id956800243) |
| Recipe Keeper – Taste | 156 ratings | No ads, no sign-up | no | Imports TikTok | [App Store](https://apps.apple.com/app/id1621869968) |

**Kill check:** hard kill (a): iOS has no recipe saver (Notes and Safari Reading List save links, not structured recipes). Hard kill (b): no app found that is free, ad-free, account-free, ★4.6+ with 20k+ ratings, *and* imports social video. Paprika is big but paid and can't read social video. Mela has the right model but is small and hasn't been updated since mid-2025. Samsung Food needs an account, and Pinterest saves pins, not recipes. **Wedge against the incumbent:** ReciMe's social import with no trial wall and no weekly cap. Paprika, the big one-time alternative, also lacks it: it can't import social video. Aldenté already offers the whole thing for free (unlimited saves, including social), and Pestle, Copy Me That, MyMealTicket and Mela offer parts of it. All of them are small (under 5k ratings), so the market is still open, but it is crowded. What this app adds over them is a one-time `pro` instead of a subscription, no AI, and Paprika import. Those are thin, which is why competition scores 3. Searches run: `ReciMe alternative free reddit…`, `reddit app to save recipes from instagram reels tiktok without subscription`, `reddit ReciMe free trial forced subscription`, `Mela … import Instagram TikTok`, `Crouton … import from Instagram TikTok`, `ReciMe export recipes`.

## 4. The idea (Phase 1 §3, §5)

- **Positioning (one sentence):** paste or share any recipe link (TikTok, Instagram, YouTube or a website) and get a clean, editable recipe. Free and unlimited, with no trial screen and no account.
- **Differentiator visible on the first screen:** the first screen is a paste-a-link box and your recipe library. There's no trial page and no sign-up, and the store listing says "unlimited free saves". Settings can import a Paprika export (`.paprikarecipes`), so Paprika users who want social import can switch without retyping.
- **Core loop (< 60 s):** copy a reel or recipe link, then open the app. It offers the link from the clipboard, you tap Save, check the parsed ingredients and steps, and the recipe is in the library.
- **Screens (≤ 5, excluding onboarding / paywall / settings):**
  1. Library: grid, search, collections filter
  2. Add: paste box with clipboard detection, parse preview, "paste caption instead" fallback
  3. Recipe: ingredients and steps, cook mode (screen stays awake), serving scaler
  4. Edit recipe
  5. Grocery list (`pro`): built from chosen recipes, same items combined
- **Cut from v1 (goes to LATER.md):** share extension (v1.1), meal planner, photo/OCR import of handwritten cards, nutrition and calories, Facebook reels (best effort only), Android, any AI.

## 5. Money (Phase 1 §6)

- **Free:** unlimited saves from websites, TikTok, YouTube and Instagram; library, search, cook mode; Paprika import.
- **`pro`:** grocery list, serving scaling with unit conversion, collections, cloud backup and sync across devices (Sign in with Apple, opt-in), export. Price anchors: ReciMe $39.99/yr, Pestle $24.99/yr or lifetime, Paprika $4.99, Mela $4.99–6.99, MyMealTicket $4.99. Suggested: $9.99/yr or $19.99 lifetime (no AI, so running costs are near zero), with no trial wall.
- **Willingness-to-pay evidence:** ReciMe grosses in 3 storefronts with a best rank of 1, and Paprika grosses in 2 at $4.99. Reviewers object to being forced to pay before trying, not to paying: "if I like it then I'll get the paid plan" (gb 2026-10-28). Some were already paying: "I will not be renewing" (us 2026-11-04), "pay the 2$ trial" (us 2026-11-04).

## 6. Stack fit (app-factory contract)

- **Supabase use:**
  - Edge Function `parse-url`:
    - websites: fetch the page and read the schema.org `Recipe` JSON-LD, falling back to microdata
    - TikTok: the public [oEmbed endpoint](https://developers.tiktok.com/doc/embed-videos) returns the caption as `title`
    - YouTube: Data API `videos.list` description (free quota)
    - Instagram: try an on-device fetch of the public post's metadata first, then the Edge Function, then the "paste caption" fallback
  - A shared TypeScript parser turns caption text into ingredients and steps by rule (quantity and unit lines, numbered steps, "Ingredients" and "Method" headings), using an MIT ingredient-parser library. No AI.
  - Postgres tables `recipes` and `grocery_items` with RLS, plus Storage for recipe images, both only for `pro` sync.
  - Auth: none for free users, who stay local in expo-sqlite. Sign in with Apple only when turning on sync.
- **Native risk:** low for v1 (clipboard plus paste). The share extension (expo-share-intent config plugin) is native extension work, so it's deferred to v1.1 and flagged.
- **Data collected (seed for DATA.md):** the URLs and recipe content the user saves, and an Apple ID relay email only if they turn on sync. No analytics beyond Sentry crash reports, no tracking.
- **Estimated fit in 14 days:** tight but fits. JSON-LD and TikTok/YouTube parsing are routine. Instagram is the uncertain day (see kill criteria). The other screens are plain CRUD.

## 7. Risks and kill criteria (Phase 1 §8–9)

- **Guideline 4.3 risk:** medium. Social recipe savers are crowded in 2026 (ReciMe, Mr. Cook, Aldenté, Pestle, Flavorish, MyMealTicket, SousChef AI, Recipe Hero…), and many look alike. The wedge has to show on the first screen and in the screenshots: no trial, unlimited free saves, Paprika import, no AI.
- **Kill criteria:**
  1. Day-1 spike: if public Instagram reel captions can't be read on-device or server-side for at least 8 of 10 test reels, Instagram drops to paste-caption only. Re-score before building, because Instagram is the biggest source. *Not checked yet.* What is known: Meta's 2025 oEmbed changes removed thumbnails and author fields ([Meta](https://developers.facebook.com/blog/post/2025/04/08/oembed-updates/)), and server-side fetching from Supabase is likely blocked (paid scraping services exist because of it). An on-device fetch, or a hidden WebView, plus rule-based parsing is plausible when the recipe is written in the caption. It fails on spoken recipes and "comment RECIPE" posts. **If the test fails, gap clarity and build fit drop and the score falls to about 3.5 (watchlist): don't build.**
  2. ReciMe removes the forced trial and the weekly cap before you start. *Checked 2026-11-05:* still there on v8.2.2 (8 low-star reviews on that version).
  3. A big free, ad-free, account-free social importer turns up (hard kill b). *Checked:* none found in this run.
- **Open questions for Phase 1:**
  - Is Instagram import better as on-device fetch or server-side?
  - Is a public ReciMe recipe share link parseable (a second switching path)?
  - Should Paprika import be free (drives switching) or `pro`?
  - Should the store listing lead with "no AI"?
