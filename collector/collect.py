#!/usr/bin/env python3
"""App Scout daily collector (free sources only, Python stdlib only).

1. Charts: top free / top paid (all storefronts) + top grossing (all storefronts),
   plus per-category free/grossing charts for a rotating slice of storefronts.
2. Lookup: metadata (genre, ratings, price, last update) via the iTunes Lookup API, cached.
3. Filter: drop excluded genres (games, medical, finance...), keep "proven" apps.
4. Reviews: for the top-priority apps not scanned recently, pull the most recent
   reviews (public customer-reviews RSS) from the storefronts where they chart,
   keep the low-star ones, merge into a rolling per-app file.

Writes into --out (the checked-out `data` branch):
  latest/run.json, latest/candidates.json, latest/scanned.json
  reviews/<appId>.json, state/history.json, state/lookup_cache.json
"""
import argparse
import datetime as dt
import json
import math
import os
import random
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
V2 = os.environ.get("APPLE_RSS_V2_BASE", "https://rss.marketingtools.apple.com/api/v2")
IT = os.environ.get("ITUNES_BASE", "https://itunes.apple.com")
UA = "app-scout/1.0 (personal research; github.com/MohammedOmar3/app-scout)"
GAME_GENRE = 6014


def now():
    return dt.datetime.now(dt.timezone.utc)


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, obj, compact=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) if compact else json.dumps(obj, ensure_ascii=False, indent=1)
    path.write_text(text, encoding="utf-8")


class Fetcher:
    """Polite JSON fetcher: global spacing, adaptive slow-down on 429/403, hard deadline.

    Retries only on 429 / 5xx / network errors (never on 400/403/404), and gives up
    immediately once the deadline has passed, so a throttled run still finishes and
    publishes what it has.
    """

    def __init__(self, timeout, spacing=0.12, lookup_spacing=2.5, deadline=None, jitter=0.0,
                 breaker=0, cooldown_s=90, max_cooldowns=1):
        self.timeout = timeout
        self.jitter = jitter
        # circuit breaker: after `breaker` consecutive 403s, pause `cooldown_s`; after the
        # last allowed cooldown, mark blocked and stop making requests (fail fast, not slow)
        self.breaker = breaker
        self.cooldown_s = cooldown_s
        self.max_cooldowns = max_cooldowns
        self.cooldowns = 0
        self.consec_403 = 0
        self.blocked = False
        self._paused_until = 0.0
        self.spacing = spacing
        self.lookup_spacing = lookup_spacing
        self.deadline = deadline
        self._lock = threading.Lock()
        self._lookup_lock = threading.Lock()
        self._next = 0.0
        self._next_lookup = 0.0
        self._pushback = 0
        self.requests = 0
        self.failures = 0
        self.errors = []
        self.status = {}  # "<kind> <code>" -> count

    def past_deadline(self):
        return self.blocked or (self.deadline is not None and time.monotonic() > self.deadline)

    def _on_403(self):
        if not self.breaker:
            return
        with self._lock:
            self.consec_403 += 1
            if self.consec_403 < self.breaker:
                return
            self.consec_403 = 0
            if self.cooldowns < self.max_cooldowns:
                self.cooldowns += 1
                self._paused_until = time.monotonic() + self.cooldown_s
                self._count("breaker", f"cooldown-{self.cooldowns}")
            else:
                self.blocked = True
                self._count("breaker", "blocked")

    def _count(self, kind, code):
        k = f"{kind} {code}"
        self.status[k] = self.status.get(k, 0) + 1

    def _slow_down(self, lookup):
        with self._lock:
            self._pushback += 1
            if self._pushback % 10 == 0:  # sustained pushback -> double spacing (cap 3s / 10s)
                self.spacing = min(3.0, self.spacing * 2)
                self.lookup_spacing = min(10.0, self.lookup_spacing * 2)

    def _wait(self, lookup):
        pause = self._paused_until - time.monotonic()
        if pause > 0:
            time.sleep(pause)
        lock = self._lookup_lock if lookup else self._lock
        with lock:
            t = time.monotonic()
            nxt = self._next_lookup if lookup else self._next
            if nxt > t:
                time.sleep(nxt - t)
            gap = self.lookup_spacing if lookup else self.spacing
            if self.jitter:
                gap += random.uniform(0, self.jitter)
            stamp = time.monotonic() + gap
            if lookup:
                self._next_lookup = stamp
            else:
                self._next = stamp

    def get(self, url, lookup=False, retries=2, kind="other"):
        for attempt in range(retries + 1):
            if self.past_deadline():
                self._count(kind, "skipped-deadline")
                return None
            self._wait(lookup)
            self.requests += 1
            try:
                req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
                with urlopen(req, timeout=self.timeout) as r:
                    body = r.read()
                self._count(kind, 200)
                self.consec_403 = 0
                if not body.strip():
                    return None
                return json.loads(body)
            except HTTPError as e:
                self._count(kind, e.code)
                if e.code in (429, 403):
                    self._slow_down(lookup)
                if e.code == 403:
                    self._on_403()
                if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                    time.sleep(3 * (attempt + 1))
                    continue
                self._fail(url, f"HTTP {e.code}")
                return None
            except json.JSONDecodeError:
                self._count(kind, "bad-json")
                self._fail(url, "bad json")
                return None
            except (URLError, TimeoutError, ConnectionError, OSError) as e:
                self._count(kind, "net-" + type(e).__name__)
                if attempt < retries:
                    time.sleep(2 * (attempt + 1))
                    continue
                self._fail(url, type(e).__name__ + ": " + str(e)[:120])
                return None
        return None

    def _fail(self, url, msg):
        self.failures += 1
        if len(self.errors) < 40:
            self.errors.append({"url": url, "error": msg})


# ---------------------------------------------------------------- charts

def parse_v2(data):
    out = []
    for i, r in enumerate(((data or {}).get("feed") or {}).get("results") or []):
        if r.get("id"):
            out.append({"id": str(r["id"]), "name": r.get("name"), "artist": r.get("artistName"), "rank": i + 1, "genre": None})
    return out


def parse_legacy(data):
    entries = ((data or {}).get("feed") or {}).get("entry") or []
    if isinstance(entries, dict):
        entries = [entries]
    out = []
    for i, e in enumerate(entries):
        try:
            app_id = e["id"]["attributes"]["im:id"]
        except (KeyError, TypeError):
            continue
        cat = ((e.get("category") or {}).get("attributes") or {}).get("im:id")
        out.append({"id": str(app_id), "name": (e.get("im:name") or {}).get("label"),
                    "artist": (e.get("im:artist") or {}).get("label"), "rank": i + 1,
                    "genre": int(cat) if cat and str(cat).isdigit() else None})
    return out


def chart_jobs(storefronts, cfg, today):
    lim = cfg["chart_limit"]
    jobs = []

    def cat_jobs(cc):
        for g in cfg["category_chart_genres"]:
            jobs.append((cc, "free", g, f"{IT}/{cc}/rss/topfreeapplications/limit={lim}/genre={g}/json", "legacy"))
            jobs.append((cc, "grossing", g, f"{IT}/{cc}/rss/topgrossingapplications/limit={lim}/genre={g}/json", "legacy"))

    # 1) category charts for the big always-on storefronts first: richest non-game signal
    always = [cc for cc in cfg["always_category_storefronts"] if cc in storefronts]
    for cc in always:
        cat_jobs(cc)
    # 2) overall charts, every storefront
    for cc in storefronts:
        # legacy iTunes RSS is far more reliable than the v2 marketing-tools feed (v2 kept as fallback below)
        jobs.append((cc, "free", None, f"{IT}/{cc}/rss/topfreeapplications/limit={lim}/json", "legacy"))
        jobs.append((cc, "paid", None, f"{IT}/{cc}/rss/toppaidapplications/limit={lim}/json", "legacy"))
        jobs.append((cc, "grossing", None, f"{IT}/{cc}/rss/topgrossingapplications/limit={lim}/json", "legacy"))
    # rotating slice of storefronts for per-category charts (non-game genres surface here)
    n = cfg["category_chart_storefronts_per_day"]
    start = (today.toordinal() * n) % len(storefronts)
    rot = [storefronts[(start + i) % len(storefronts)] for i in range(min(n, len(storefronts)))]
    cat_sf = list(dict.fromkeys(always + rot))
    # 3) category charts for today's rotating slice
    for cc in rot:
        if cc not in always:
            cat_jobs(cc)
    return jobs, cat_sf


def collect_charts(f, storefronts, cfg, today, log):
    jobs, cat_sf = chart_jobs(storefronts, cfg, today)
    apps = {}
    feed_stats = {}
    lock = threading.Lock()

    def run(job):
        cc, chart, genre, url, kind = job
        skipped = f.past_deadline()
        data = None if skipped else f.get(url, kind="chart-" + kind)
        rows = parse_v2(data) if kind == "v2" else parse_legacy(data)
        return job, rows, skipped

    with ThreadPoolExecutor(cfg["workers"]) as ex:
        for fut in as_completed([ex.submit(run, j) for j in jobs]):
            (cc, chart, genre, url, kind), rows, skipped = fut.result()
            key = f"{chart}{'/genre' if genre else ''}"
            with lock:
                st = feed_stats.setdefault(key, {"ok": 0, "empty": 0, "skipped": 0})
                st["skipped" if skipped else ("ok" if rows else "empty")] += 1
                for r in rows:
                    a = apps.setdefault(r["id"], {"id": r["id"], "name": r["name"], "artist": r["artist"],
                                                   "chart_genre": None, "positions": []})
                    if r["genre"] and not a["chart_genre"]:
                        a["chart_genre"] = r["genre"]
                    a["positions"].append({"cc": cc, "chart": chart, "genre": genre, "rank": r["rank"]})
    log(f"charts: {len(jobs)} feeds, {len(apps)} unique apps, category storefronts today: {','.join(cat_sf)}")
    return apps, feed_stats, cat_sf


# ---------------------------------------------------------------- lookup

KEEP_FIELDS = ["trackName", "sellerName", "primaryGenreId", "primaryGenreName", "genreIds", "averageUserRating",
               "userRatingCount", "price", "currency", "formattedPrice", "currentVersionReleaseDate", "releaseDate",
               "version", "trackViewUrl", "contentAdvisoryRating"]


def trim_lookup(r, cc):
    d = {k: r.get(k) for k in KEEP_FIELDS}
    d["description"] = (r.get("description") or "")[:300]
    d["lookup_cc"] = cc
    return d


def best_cc(app, avoid="us"):
    pos = [p for p in sorted(app["positions"], key=lambda p: p["rank"]) if p["cc"] != avoid]
    return pos[0]["cc"] if pos else None


def collect_lookups(f, apps, cache, cfg, today, log):
    fresh_cut = (today - dt.timedelta(days=cfg["lookup_cache_days"])).isoformat()
    # skip lookups for apps the charts already say are games/excluded
    excluded = set(cfg["excluded_genre_ids"])
    need = [a for a in apps.values()
            if a["chart_genre"] not in excluded
            and not (cache.get(a["id"]) and cache[a["id"]]["fetched"] >= fresh_cut)]
    by_cc = {}
    for a in need:
        by_cc.setdefault("us", []).append(a["id"])
    missing = []
    for cc_round in range(2):
        batches = []
        for cc, ids in by_cc.items():
            for i in range(0, len(ids), 200):
                batches.append((cc, ids[i:i + 200]))
        got = set()
        for cc, ids in batches:
            data = f.get(f"{IT}/lookup?id={','.join(ids)}&country={cc}&entity=software", lookup=True, kind="lookup")
            for r in (data or {}).get("results") or []:
                tid = str(r.get("trackId"))
                if r.get("wrapperType") == "software" or r.get("kind") == "software":
                    cache[tid] = {"fetched": today.isoformat(), "data": trim_lookup(r, cc)}
                    got.add(tid)
        if cc_round == 0:
            missing = [i for ids in by_cc.values() for i in ids if i not in got]
            by_cc = {}
            for i in missing:
                cc = best_cc(apps[i])
                if cc:
                    by_cc.setdefault(cc, []).append(i)
            if not missing:
                break
    log(f"lookup: {len(need)} needed, {len(missing)} not in US store, cache size {len(cache)}")
    return cache


# ---------------------------------------------------------------- candidates

def is_excluded(meta, cfg):
    excluded = set(cfg["excluded_genre_ids"])
    pg = meta.get("primaryGenreId")
    if pg in excluded:
        return True
    gids = {int(g) for g in (meta.get("genreIds") or []) if str(g).isdigit()}
    # any game sub-genre (7xxx) or Games anywhere -> excluded
    return GAME_GENRE in gids or any(7000 <= g < 8000 for g in gids)


# ---------------------------------------------------------------- focus segments

def collect_focus(f, apps, cache, cfg, today, log):
    """Keyword segments that are not App Store genres (e.g. Islamic apps).
    Uses the iTunes Search API per (term, storefront); results carry full metadata,
    so they go straight into the lookup cache. Returns {appId: {"segments", "storefronts"}}."""
    focus = {}
    for seg, spec in (cfg.get("focus_segments") or {}).items():
        before = len(focus)
        for group in spec.get("groups", []):
            for term in group["terms"]:
                for cc in group["storefronts"]:
                    if f.past_deadline():
                        break
                    url = f"{IT}/search?term={quote(term)}&country={cc}&entity=software&limit={spec.get('limit', 50)}"
                    data = f.get(url, lookup=True, kind=f"focus-{seg}")
                    for r in (data or {}).get("results") or []:
                        if not r.get("trackId"):
                            continue
                        tid = str(r["trackId"])
                        if tid not in cache or cache[tid]["fetched"] < today.isoformat():
                            cache[tid] = {"fetched": today.isoformat(), "data": trim_lookup(r, cc)}
                        fe = focus.setdefault(tid, {"segments": set(), "storefronts": []})
                        fe["segments"].add(seg)
                        if cc not in fe["storefronts"]:
                            fe["storefronts"].append(cc)
                        if tid not in apps:
                            apps[tid] = {"id": tid, "name": r.get("trackName"), "artist": r.get("sellerName"),
                                         "chart_genre": r.get("primaryGenreId"), "positions": []}
        log(f"focus '{seg}': {len(focus) - before} apps found by search")
    return focus


def build_candidates(apps, cache, cfg, focus=None):
    focus = focus or {}
    cands = []
    for a in apps.values():
        c = cache.get(a["id"])
        if not c:
            continue
        m = c["data"]
        if is_excluded(m, cfg):
            continue
        sfs = {}
        for p in a["positions"]:
            sfs[p["cc"]] = min(sfs.get(p["cc"], 999), p["rank"])
        n_sf = len(sfs)
        rc = m.get("userRatingCount") or 0
        seg_min = min([cfg["focus_segments"][sg].get("min_ratings", cfg["min_ratings"])
                       for sg in focus.get(a["id"], {}).get("segments", [])] or [cfg["min_ratings"]])
        if rc < seg_min and n_sf < cfg["min_storefronts_if_few_ratings"]:
            continue
        grossing_sf = len({p["cc"] for p in a["positions"] if p["chart"] == "grossing"})
        paid_sf = len({p["cc"] for p in a["positions"] if p["chart"] == "paid"})
        top_sf = sorted(sfs.items(), key=lambda kv: kv[1])
        cands.append({
            "id": a["id"], "name": m.get("trackName") or a["name"], "seller": m.get("sellerName") or a["artist"],
            "genre": m.get("primaryGenreName"), "genre_id": m.get("primaryGenreId"),
            "rating": m.get("averageUserRating"), "ratings": rc, "ratings_cc": m.get("lookup_cc"),
            "price": m.get("formattedPrice"), "updated": (m.get("currentVersionReleaseDate") or "")[:10],
            "released": (m.get("releaseDate") or "")[:10], "url": m.get("trackViewUrl"),
            "description": m.get("description"),
            "storefronts": n_sf, "grossing_storefronts": grossing_sf, "paid_storefronts": paid_sf,
            "best_rank": top_sf[0][1] if top_sf else None,
            "top_storefronts": [cc for cc, _ in top_sf[:10]],
            "all_storefronts": [cc for cc, _ in top_sf],
            "focus": sorted(focus[a["id"]]["segments"]) if a["id"] in focus else [],
            "search_storefronts": focus[a["id"]]["storefronts"] if a["id"] in focus else [],
        })
    sweet_lo, sweet_hi = cfg.get("sweet_spot_ratings", [2000, 300000])
    for c in cands:
        r = c["rating"] or 0
        rc = c["ratings"]
        # size: proven but not a mega-app. Peaks inside the sweet spot, falls off above it.
        size = math.log10(rc + 1)
        if rc > sweet_hi:
            size = math.log10(sweet_hi) - (math.log10(rc) - math.log10(sweet_hi)) * 1.5
        c["scan"] = rc <= cfg.get("max_ratings_to_scan", 1500000)
        upd = c.get("updated") or ""
        stale = len(upd) == 10 and (dt.date.today() - dt.date.fromisoformat(upd)).days > 365
        c["priority"] = round(2 * size + min(c["storefronts"], 30) / 10
                              + (1.5 if c["grossing_storefronts"] else 0) + (0.75 if c["paid_storefronts"] else 0)
                              + (1.0 if 0 < r < 4.5 else 0) + (0.5 if 0 < r < 4.0 else 0)
                              + (0.5 if sweet_lo <= rc <= sweet_hi else 0)
                              + (1.5 if stale else 0)  # abandoned-but-charting apps are prime leads
                              + max([cfg["focus_segments"][sg].get("boost", 0) for sg in c["focus"]] or [0]), 3)
    cands.sort(key=lambda c: c["priority"], reverse=True)
    return cands


# ---------------------------------------------------------------- reviews

def parse_reviews(data, cc):
    entries = ((data or {}).get("feed") or {}).get("entry") or []
    if isinstance(entries, dict):
        entries = [entries]
    out = []
    for e in entries:
        rating = (e.get("im:rating") or {}).get("label")
        if not rating:
            continue  # app-info entry in old feeds
        out.append({
            "rid": (e.get("id") or {}).get("label"),
            "stars": int(rating),
            "title": ((e.get("title") or {}).get("label") or "")[:200],
            "text": ((e.get("content") or {}).get("label") or "")[:1500],
            "version": (e.get("im:version") or {}).get("label"),
            "votes": int((e.get("im:voteCount") or {}).get("label") or 0),
            "helpful": int((e.get("im:voteSum") or {}).get("label") or 0),
            "date": ((e.get("updated") or {}).get("label") or "")[:10],
            "cc": cc,
        })
    return out


def fetch_review_page(f, cc, app_id, page, sort="mostrecent"):
    """Apple's review feed often returns an empty 200 when hit quickly; for page 1 retry with
    a pause and the alternate URL form before treating it as empty. Deeper pages: one try."""
    alt_sort = {"mostrecent": "mostRecent", "mosthelpful": "mostHelpful"}[sort]
    urls = [f"{IT}/{cc}/rss/customerreviews/page={page}/id={app_id}/sortby={sort}/json",
            f"{IT}/{cc}/rss/customerreviews/id={app_id}/sortBy={alt_sort}/page={page}/json"]
    pauses = [0, 2] if page == 1 else [0]
    for attempt, pause in enumerate(pauses):
        if pause:
            time.sleep(pause)
        rows = parse_reviews(f.get(urls[attempt % 2], kind="reviews"), cc)
        if rows:
            f._count("reviews", f"{sort} p{page} ok" + (f" after retry {attempt}" if attempt else ""))
            return rows
        if f.past_deadline():
            return []
    f._count("reviews", f"{sort} p{page} empty")
    return []


def scan_app(f, cand, cfg, today, deadline):
    """Pull the most recent AND most helpful reviews from several storefronts.
    (Apple's feed currently serves ~50 reviews per sort/page; breadth beats depth.)"""
    oldest_ok = (today - dt.timedelta(days=cfg["review_max_age_days"])).isoformat()
    stats, low = {}, []
    order = cfg.get("_storefront_order", {})
    charted = sorted(cand["all_storefronts"], key=lambda cc: order.get(cc, 999))
    pool = list(dict.fromkeys(cand.get("search_storefronts", []) + charted))
    sfs = pool[:cand.get("_sf_per_app") or cfg["storefronts_per_app"]] or [cand.get("ratings_cc") or "us"]
    for cc in sfs:
        hist = {str(s): 0 for s in range(1, 6)}
        fetched, newest, oldest, seen = 0, None, None, set()
        for sort in cfg.get("review_sorts", ["mostrecent"]):
            for page in range(1, cfg["review_pages_per_storefront"] + 1):
                if time.monotonic() > deadline:
                    break
                rows = fetch_review_page(f, cc, cand["id"], page, sort)
                if not rows:
                    break
                for r in rows:
                    if r["rid"] in seen:
                        continue
                    seen.add(r["rid"])
                    hist[str(r["stars"])] += 1
                    fetched += 1
                    newest = max(newest or r["date"], r["date"])
                    oldest = min(oldest or r["date"], r["date"])
                    if r["stars"] <= cfg["low_star_max"] and r["date"] >= oldest_ok and r["text"].strip():
                        low.append(r)
                if sort == "mostrecent" and oldest and oldest < oldest_ok:
                    break
        stats[cc] = {"fetched": fetched, "hist": hist, "newest": newest, "oldest": oldest}
    return stats, low


def merge_reviews(path, cand, stats, low, cfg, today):
    doc = load_json(path, {"id": cand["id"], "reviews": []})
    keep_after = (today - dt.timedelta(days=cfg["keep_reviews_days"])).isoformat()
    seen = {}
    for r in doc.get("reviews", []) + low:
        key = r.get("rid") or (r["cc"] + r["date"] + r["title"])
        seen[key] = r
    reviews = [r for r in seen.values() if r["date"] >= keep_after]
    reviews.sort(key=lambda r: r["date"], reverse=True)
    doc.update({"id": cand["id"], "app": {k: cand.get(k) for k in ("name", "seller", "genre", "rating", "ratings", "price", "updated", "url", "focus")},
                "last_scanned": today.isoformat(), "stats": stats, "reviews": reviews[:cfg["max_reviews_per_app"]]})
    save_json(path, doc, compact=True)
    return doc


# ---------------------------------------------------------------- phases
#
#  plan  : charts + focus search + lookup -> candidates + work/queue.json   (one runner)
#  scan  : one shard of the queue, reviews only, fresh runner IP            (N parallel runners)
#  merge : fold shard results into the data dir, history, run.json, health (one runner)
#  all   : plan -> scan (every shard, sequentially) -> merge, for local runs / fallback


class Ctx:
    def __init__(self, args):
        self.args = args
        self.cfg = load_json(HERE / "config.json", {})
        all_sf = load_json(HERE / "storefronts.json", ["us"])
        self.cfg["_storefront_order"] = {cc: i for i, cc in enumerate(all_sf)}
        self.storefronts = args.storefronts.split(",") if getattr(args, "storefronts", None) else all_sf
        if getattr(args, "max_apps", None) is not None:
            self.cfg["apps_to_scan_per_day"] = args.max_apps
        self.out = Path(args.out)
        self.today = now().date()
        self.started = now()
        self.t0 = time.monotonic()
        self.logs = []

    def log(self, msg):
        line = f"[{now().strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        self.logs.append(line)

    def minutes(self):
        return round((time.monotonic() - self.t0) / 60, 1)


def fresh_fetcher(cfg, kind):
    if kind == "scan":
        return Fetcher(cfg["request_timeout_seconds"], spacing=cfg.get("scan_spacing_s", 0.5),
                       jitter=cfg.get("scan_jitter_s", 0.5), breaker=cfg.get("breaker_consecutive_403", 25),
                       cooldown_s=cfg.get("breaker_cooldown_s", 90), max_cooldowns=cfg.get("breaker_max_cooldowns", 1))
    return Fetcher(cfg["request_timeout_seconds"], breaker=cfg.get("plan_breaker_consecutive_403", 60),
                   cooldown_s=30, max_cooldowns=1)


def build_queue(ctx, cands):
    cfg, today = ctx.cfg, ctx.today
    history = load_json(ctx.out / "state/history.json", {})
    rescan_cut = (today - dt.timedelta(days=cfg["rescan_after_days"])).isoformat()
    due = [c for c in cands if c["scan"] and history.get(c["id"], "") < rescan_cut]
    reserved, taken = [], set()
    for seg, spec in (cfg.get("focus_segments") or {}).items():
        pick = [c for c in due if seg in c["focus"] and c["id"] not in taken][:spec.get("reserve_scan_slots", 0)]
        reserved += pick
        taken.update(c["id"] for c in pick)
    rest = [c for c in due if c["id"] not in taken][:max(0, cfg["apps_to_scan_per_day"] - len(reserved))]
    todo, fi, gi = [], 0, 0  # interleave 1 focus : 2 general
    while fi < len(reserved) or gi < len(rest):
        if fi < len(reserved):
            todo.append(reserved[fi]); fi += 1
        todo += rest[gi:gi + 2]; gi += 2
    return todo


def lookup_ids(f, ids, cache, today, ccs=("us", "gb", "sa", "ae", "in", "de", "jp")):
    missing = list(ids)
    for cc in ccs:
        if not missing:
            break
        got = set()
        for i in range(0, len(missing), 200):
            data = f.get(f"{IT}/lookup?id={','.join(missing[i:i + 200])}&country={cc}&entity=software", lookup=True, kind="lookup")
            for r in (data or {}).get("results") or []:
                tid = str(r.get("trackId"))
                if tid and (r.get("wrapperType") == "software" or r.get("kind") == "software"):
                    cache[tid] = {"fetched": today.isoformat(), "data": trim_lookup(r, cc)}
                    got.add(tid)
        missing = [i for i in missing if i not in got]
    return missing


def phase_plan(ctx):
    cfg, out, today, a = ctx.cfg, ctx.out, ctx.today, ctx.args
    stats = {"mode": a.mode, "phase_minutes": {}, "partial": False}
    cache = load_json(out / "state/lookup_cache.json", {})
    prev = {c["id"]: c for c in load_json(out / "latest/candidates.json", [])}

    if a.mode == "targeted":
        f = fresh_fetcher(cfg, "plan")
        ids = [x.strip() for x in (a.app_ids or "").split(",") if x.strip()]
        terms = [x.strip() for x in (a.terms or "").split(",") if x.strip()]
        lookup_ids(f, ids, cache, today)
        apps, focus = {}, {}
        for tid in ids:
            apps[tid] = {"id": tid, "name": None, "artist": None, "chart_genre": None, "positions": []}
            focus[tid] = {"segments": {"target"}, "storefronts": []}
        term_sf = (a.term_storefronts or "us,gb").split(",")
        for term in terms:
            for cc in term_sf:
                data = f.get(f"{IT}/search?term={quote(term)}&country={cc}&entity=software&limit=25", lookup=True, kind="target-search")
                for r in (data or {}).get("results") or []:
                    tid = str(r.get("trackId") or "")
                    if not tid:
                        continue
                    cache[tid] = {"fetched": today.isoformat(), "data": trim_lookup(r, cc)}
                    apps.setdefault(tid, {"id": tid, "name": r.get("trackName"), "artist": r.get("sellerName"),
                                          "chart_genre": r.get("primaryGenreId"), "positions": []})
                    fe = focus.setdefault(tid, {"segments": set(), "storefronts": []})
                    fe["segments"].add("target" if tid in ids else "target-competitor")
                    if cc not in fe["storefronts"]:
                        fe["storefronts"].append(cc)
        cfg.setdefault("focus_segments", {})
        cfg["focus_segments"]["target"] = {"min_ratings": 0}
        cfg["focus_segments"]["target-competitor"] = {"min_ratings": cfg.get("target_competitor_min_ratings", 300)}
        new = build_candidates(apps, cache, cfg, focus)
        for c in new:  # keep chart stats we already know
            old = prev.get(c["id"])
            if old:
                for k in ("storefronts", "grossing_storefronts", "paid_storefronts", "best_rank", "top_storefronts", "all_storefronts"):
                    c[k] = old.get(k, c[k])
                c["focus"] = sorted(set(old.get("focus", [])) | set(c["focus"]))
        order = {tid: i for i, tid in enumerate(ids)}
        new.sort(key=lambda c: (0 if c["id"] in order else 1, order.get(c["id"], 0), -c["priority"]))
        queue = new[: a.max_targets or 40]
        for c in queue:
            c["_sf_per_app"] = a.storefronts_per_app or cfg.get("targeted_storefronts_per_app", 8)
        merged = dict(prev)
        merged.update({c["id"]: {k: v for k, v in c.items() if not k.startswith("_")} for c in new})
        cands = sorted(merged.values(), key=lambda c: -(c.get("priority") or 0))
        stats.update({"targets": ids, "terms": terms, "unique_chart_apps": len(apps), "requests": f.requests,
                      "failures": f.failures, "http_status": f.status})
        ctx.log(f"targeted plan: {len(ids)} ids, {len(terms)} terms -> {len(queue)} apps queued")
    else:
        tp = time.monotonic()
        f = fresh_fetcher(cfg, "plan")
        f.deadline = ctx.t0 + cfg["charts_budget_minutes"] * 60
        apps, feed_stats, cat_sf = collect_charts(f, ctx.storefronts, cfg, today, ctx.log)
        if f.past_deadline():
            stats["partial"] = True
            ctx.log("charts: stopped early (time budget or 403 breaker) - continuing with what we have")
        stats["phase_minutes"]["charts"] = round((time.monotonic() - tp) / 60, 1)
        all_status, req, fail = dict(f.status), f.requests, f.failures

        tp = time.monotonic()
        f = fresh_fetcher(cfg, "plan")
        f.deadline = ctx.t0 + cfg["focus_budget_minutes"] * 60
        focus = collect_focus(f, apps, cache, cfg, today, ctx.log)
        f.deadline = ctx.t0 + cfg["lookup_budget_minutes"] * 60
        cache = collect_lookups(f, apps, cache, cfg, today, ctx.log)
        if f.past_deadline():
            stats["partial"] = True
        stats["phase_minutes"]["focus+lookup"] = round((time.monotonic() - tp) / 60, 1)
        for k, v in f.status.items():
            all_status[k] = all_status.get(k, 0) + v
        new = build_candidates(apps, cache, cfg, focus)
        for c in new:
            c["seen"] = today.isoformat()
        # resilience: if charts were cut short, keep yesterday's candidates we didn't see today (<= 7 days old)
        keep_cut = (today - dt.timedelta(days=7)).isoformat()
        new_ids = {c["id"] for c in new}
        carried = [c for c in prev.values() if c["id"] not in new_ids and c.get("seen", "") >= keep_cut]
        for c in carried:
            c["stale_chart"] = True
        cands = sorted(new + carried, key=lambda c: -(c.get("priority") or 0))
        queue = build_queue(ctx, cands)
        stats.update({"category_storefronts_today": cat_sf, "feeds": feed_stats, "unique_chart_apps": len(apps),
                      "carried_candidates": len(carried), "requests": req + f.requests,
                      "failures": fail + f.failures, "http_status": all_status})
        ctx.log(f"plan: {len(cands)} candidates ({len(carried)} carried over), queue {len(queue)} "
                f"({sum(1 for c in queue if c.get('focus'))} focus)")

    stale = (today - dt.timedelta(days=60)).isoformat()
    cache = {k: v for k, v in cache.items() if v["fetched"] >= stale}
    save_json(out / "state/lookup_cache.json", cache, compact=True)
    save_json(out / "latest/candidates.json", [{k: v for k, v in c.items() if not k.startswith("_")} for c in cands], compact=True)
    n_shards = max(1, min(a.shards, math.ceil(len(queue) / 8))) if queue else 1
    save_json(out / "work/queue.json", {"mode": a.mode, "date": today.isoformat(), "shards": n_shards, "items": queue})
    stats.update({"date": today.isoformat(), "eligible_candidates": len(cands), "queued": len(queue),
                  "shards": n_shards, "plan_minutes": ctx.minutes(), "log": ctx.logs})
    save_json(out / "work/plan.json", stats)
    if a.github_output:
        with open(a.github_output, "a") as fh:
            fh.write(f"shards={json.dumps(list(range(n_shards)))}\n")
    return stats


def phase_scan(ctx, shard, shards, shard_out):
    cfg, out, today = ctx.cfg, ctx.out, ctx.today
    q = load_json(out / "work/queue.json", {"items": []})
    items = [c for i, c in enumerate(q["items"]) if i % shards == shard]
    f = fresh_fetcher(cfg, "scan")
    deadline = ctx.t0 + cfg["scan_budget_minutes"] * 60
    f.deadline = deadline
    shard_out = Path(shard_out)
    (shard_out / "reviews").mkdir(parents=True, exist_ok=True)
    scanned, fetched_total, low_total = [], 0, 0
    ctx.log(f"shard {shard}/{shards}: {len(items)} apps")
    with ThreadPoolExecutor(cfg.get("scan_workers", 3)) as ex:
        futs = {ex.submit(scan_app, f, c, cfg, today, deadline): c for c in items}
        for fut in as_completed(futs):
            c = futs[fut]
            try:
                stats, low = fut.result()
            except Exception as e:
                f._fail(c["id"], f"scan error {e!r}"[:160])
                continue
            fetched = sum(s["fetched"] for s in stats.values())
            if fetched == 0:
                continue
            src = out / f"reviews/{c['id']}.json"
            dst = shard_out / f"reviews/{c['id']}.json"
            if src.exists():
                shutil.copy(src, dst)
            doc = merge_reviews(dst, c, stats, low, cfg, today)
            hist = {str(s): sum(st["hist"][str(s)] for st in stats.values()) for s in range(1, 6)}
            scanned.append({"id": c["id"], "name": c["name"], "genre": c["genre"], "focus": c.get("focus", []),
                            "fetched": fetched, "hist": hist, "low_new": len(low), "low_total": len(doc["reviews"]),
                            "low_share": round((hist["1"] + hist["2"]) / fetched, 3)})
            fetched_total += fetched
            low_total += len(low)
    res = {"shard": shard, "apps_queued": len(items), "apps_scanned": len(scanned), "scanned": scanned,
           "reviews_fetched": fetched_total, "low_star_kept": low_total, "requests": f.requests, "failures": f.failures,
           "http_status": f.status, "blocked": f.blocked, "cooldowns": f.cooldowns,
           "hit_deadline": time.monotonic() > deadline, "minutes": ctx.minutes(), "error_samples": f.errors[:15], "log": ctx.logs}
    save_json(shard_out / "scan.json", res)
    ctx.log(f"shard {shard}: scanned {len(scanned)}/{len(items)} apps, {fetched_total} reviews, blocked={f.blocked}, "
            f"status={f.status}")
    return res


def health_of(run, cfg):
    reasons, level = [], "OK"
    scanned = run.get("apps_scanned", 0)
    if run.get("status", "").startswith("error"):
        level = "FAILED"; reasons.append(run["status"])
    if scanned == 0:
        level = "FAILED"; reasons.append("no apps scanned")
    elif scanned < cfg.get("health_min_apps", 40) and run.get("mode") != "targeted":
        level = "DEGRADED" if level == "OK" else level
        reasons.append(f"only {scanned} apps scanned (< {cfg.get('health_min_apps', 40)})")
    blocked = [s["shard"] for s in run.get("shards_detail", []) if s.get("blocked")]
    missing = run.get("shards_missing", [])
    if blocked:
        level = "DEGRADED" if level == "OK" else level
        reasons.append(f"shards blocked by Apple 403s: {blocked}")
    if missing:
        level = "DEGRADED" if level == "OK" else level
        reasons.append(f"shards produced no output: {missing}")
    st = run.get("http_status", {})
    rv_403 = st.get("reviews 403", 0)
    rv_ok = st.get("reviews 200", 0)
    if rv_403 + rv_ok and rv_403 / (rv_403 + rv_ok) > 0.3:
        level = "DEGRADED" if level == "OK" else level
        reasons.append(f"review 403 rate {rv_403}/{rv_403 + rv_ok}")
    return {"level": level, "reasons": reasons}


def phase_merge(ctx, shards_dir):
    cfg, out, today = ctx.cfg, ctx.out, ctx.today
    plan = load_json(out / "work/plan.json", {})
    q = load_json(out / "work/queue.json", {"shards": 1, "items": []})
    history = load_json(out / "state/history.json", {})
    shard_results, missing = [], []
    shards_dir = Path(shards_dir)
    for k in range(q.get("shards", 1)):
        d = next((p for p in [shards_dir / f"scan-{k}", shards_dir / str(k), shards_dir] if (p / "scan.json").exists()
                  and load_json(p / "scan.json", {}).get("shard") == k), None)
        if not d:
            missing.append(k)
            continue
        res = load_json(d / "scan.json", {})
        (out / "reviews").mkdir(parents=True, exist_ok=True)
        for fp in (d / "reviews").glob("*.json"):
            shutil.copy(fp, out / "reviews" / fp.name)
        for srow in res.get("scanned", []):
            history[srow["id"]] = today.isoformat()
        shard_results.append(res)
    drop_cut = (today - dt.timedelta(days=cfg["drop_app_files_after_days"])).isoformat()
    for p in (out / "reviews").glob("*.json") if (out / "reviews").exists() else []:
        if history.get(p.stem, "") < drop_cut:
            p.unlink()
            history.pop(p.stem, None)
    save_json(out / "state/history.json", history, compact=True)
    scanned = sorted([r for s in shard_results for r in s["scanned"]], key=lambda r: -r["low_new"])
    mode = plan.get("mode", "daily")
    if mode == "targeted":  # keep the daily scanned list, add the targeted results on top
        prev = {r["id"]: r for r in load_json(out / "latest/scanned.json", [])}
        prev.update({r["id"]: r for r in scanned})
        save_json(out / "latest/scanned.json", sorted(prev.values(), key=lambda r: -r["low_new"]))
    else:
        save_json(out / "latest/scanned.json", scanned)
    status = dict(plan.get("http_status", {}))
    for s in shard_results:
        for k, v in s["http_status"].items():
            status[k] = status.get(k, 0) + v
    run = {
        "date": today.isoformat(), "mode": mode, "status": "ok", "finished": now().isoformat(timespec="seconds"),
        "plan_minutes": plan.get("plan_minutes"), "phase_minutes": plan.get("phase_minutes"), "partial": plan.get("partial"),
        "category_storefronts_today": plan.get("category_storefronts_today"), "feeds": plan.get("feeds"),
        "unique_chart_apps": plan.get("unique_chart_apps"), "eligible_candidates": plan.get("eligible_candidates"),
        "carried_candidates": plan.get("carried_candidates"), "targets": plan.get("targets"), "terms": plan.get("terms"),
        "queued": plan.get("queued"), "shards": q.get("shards"), "shards_missing": missing,
        "shards_detail": [{k: s[k] for k in ("shard", "apps_queued", "apps_scanned", "reviews_fetched", "blocked",
                                             "cooldowns", "hit_deadline", "minutes", "requests", "failures")} for s in shard_results],
        "apps_scanned": len(scanned), "reviews_fetched": sum(s["reviews_fetched"] for s in shard_results),
        "low_star_kept": sum(s["low_star_kept"] for s in shard_results),
        "review_files": len(list((out / "reviews").glob("*.json"))) if (out / "reviews").exists() else 0,
        "requests": plan.get("requests", 0) + sum(s["requests"] for s in shard_results),
        "failures": plan.get("failures", 0) + sum(s["failures"] for s in shard_results),
        "http_status": status, "error_samples": [e for s in shard_results for e in s.get("error_samples", [])][:30],
        "log": plan.get("log", []) + [l for s in shard_results for l in s.get("log", [])] + ctx.logs,
    }
    run["health"] = health_of(run, cfg)
    if mode == "targeted":
        save_json(out / "latest/targeted_run.json", run)
        daily = load_json(out / "latest/run.json", None)
        if daily:
            daily.setdefault("targeted_runs", []).append({k: run[k] for k in ("finished", "targets", "terms", "apps_scanned", "low_star_kept", "health")})
            save_json(out / "latest/run.json", daily)
        else:
            save_json(out / "latest/run.json", run)
    else:
        save_json(out / "latest/run.json", run)
    ctx.log(f"merge: {len(scanned)} apps scanned across {len(shard_results)} shards, missing {missing}, health {run['health']}")
    return run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["plan", "scan", "merge", "all"], default="all")
    ap.add_argument("--out", required=True, help="checked-out data branch directory")
    ap.add_argument("--mode", choices=["daily", "targeted"], default="daily")
    ap.add_argument("--app-ids", default="")
    ap.add_argument("--terms", default="")
    ap.add_argument("--term-storefronts", default="")
    ap.add_argument("--storefronts-per-app", type=int, default=0)
    ap.add_argument("--max-targets", type=int, default=0)
    ap.add_argument("--shards", type=int, default=3)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shard-out", default="")
    ap.add_argument("--shards-dir", default="")
    ap.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT", ""))
    ap.add_argument("--storefronts", help="comma list override (testing)")
    ap.add_argument("--max-apps", type=int, help="override apps_to_scan_per_day")
    args = ap.parse_args()
    ctx = Ctx(args)
    if args.phase == "plan":
        phase_plan(ctx)
    elif args.phase == "scan":
        phase_scan(ctx, args.shard, args.shards, args.shard_out or str(ctx.out / f"work/shard-{args.shard}"))
    elif args.phase == "merge":
        run = phase_merge(ctx, args.shards_dir or str(ctx.out / "work"))
        if run["health"]["level"] == "FAILED":
            print("HEALTH FAILED: " + "; ".join(run["health"]["reasons"]), file=sys.stderr)
    else:
        args.github_output = ""
        stats = phase_plan(ctx)
        for k in range(stats["shards"]):
            phase_scan(Ctx(args), k, stats["shards"], str(ctx.out / f"work/scan-{k}"))
        phase_merge(ctx, str(ctx.out / "work"))


if __name__ == "__main__":
    main()
