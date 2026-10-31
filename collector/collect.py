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
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
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

    def __init__(self, timeout, spacing=0.12, lookup_spacing=2.5, deadline=None):
        self.timeout = timeout
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
        return self.deadline is not None and time.monotonic() > self.deadline

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
        lock = self._lookup_lock if lookup else self._lock
        with lock:
            t = time.monotonic()
            nxt = self._next_lookup if lookup else self._next
            if nxt > t:
                time.sleep(nxt - t)
            stamp = time.monotonic() + (self.lookup_spacing if lookup else self.spacing)
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
                if not body.strip():
                    return None
                return json.loads(body)
            except HTTPError as e:
                self._count(kind, e.code)
                if e.code in (429, 403):
                    self._slow_down(lookup)
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
    for cc in storefronts:
        # legacy iTunes RSS is far more reliable than the v2 marketing-tools feed (v2 kept as fallback below)
        jobs.append((cc, "free", None, f"{IT}/{cc}/rss/topfreeapplications/limit={lim}/json", "legacy"))
        jobs.append((cc, "paid", None, f"{IT}/{cc}/rss/toppaidapplications/limit={lim}/json", "legacy"))
        jobs.append((cc, "grossing", None, f"{IT}/{cc}/rss/topgrossingapplications/limit={lim}/json", "legacy"))
    # rotating slice of storefronts for per-category charts (non-game genres surface here)
    n = cfg["category_chart_storefronts_per_day"]
    start = (today.toordinal() * n) % len(storefronts)
    rot = [storefronts[(start + i) % len(storefronts)] for i in range(min(n, len(storefronts)))]
    cat_sf = list(dict.fromkeys(cfg["always_category_storefronts"] + rot))
    for cc in cat_sf:
        for g in cfg["category_chart_genres"]:
            jobs.append((cc, "free", g, f"{IT}/{cc}/rss/topfreeapplications/limit={lim}/genre={g}/json", "legacy"))
            jobs.append((cc, "grossing", g, f"{IT}/{cc}/rss/topgrossingapplications/limit={lim}/genre={g}/json", "legacy"))
    return jobs, cat_sf


def collect_charts(f, storefronts, cfg, today, log):
    jobs, cat_sf = chart_jobs(storefronts, cfg, today)
    apps = {}
    feed_stats = {}
    lock = threading.Lock()

    def run(job):
        cc, chart, genre, url, kind = job
        data = f.get(url, kind="chart-" + kind)
        rows = parse_v2(data) if kind == "v2" else parse_legacy(data)
        return job, rows

    with ThreadPoolExecutor(cfg["workers"]) as ex:
        for fut in as_completed([ex.submit(run, j) for j in jobs]):
            (cc, chart, genre, url, kind), rows = fut.result()
            key = f"{chart}{'/genre' if genre else ''}"
            with lock:
                st = feed_stats.setdefault(key, {"ok": 0, "empty": 0})
                st["ok" if rows else "empty"] += 1
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


def build_candidates(apps, cache, cfg):
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
        if rc < cfg["min_ratings"] and n_sf < cfg["min_storefronts_if_few_ratings"]:
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
                              + (1.5 if stale else 0), 3)  # abandoned-but-charting apps are prime leads
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
    sfs = charted[:cfg["storefronts_per_app"]] or [cand.get("ratings_cc") or "us"]
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
    doc.update({"id": cand["id"], "app": {k: cand[k] for k in ("name", "seller", "genre", "rating", "ratings", "price", "updated", "url")},
                "last_scanned": today.isoformat(), "stats": stats, "reviews": reviews[:cfg["max_reviews_per_app"]]})
    save_json(path, doc, compact=True)
    return doc


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="checked-out data branch directory")
    ap.add_argument("--storefronts", help="comma list override (testing)")
    ap.add_argument("--max-apps", type=int, help="override apps_to_scan_per_day")
    args = ap.parse_args()

    cfg = load_json(HERE / "config.json", {})
    all_sf = load_json(HERE / "storefronts.json", ["us"])
    cfg["_storefront_order"] = {cc: i for i, cc in enumerate(all_sf)}
    storefronts = args.storefronts.split(",") if args.storefronts else all_sf
    if args.max_apps is not None:
        cfg["apps_to_scan_per_day"] = args.max_apps
    out = Path(args.out)
    today = now().date()
    started = now()
    t0 = time.monotonic()
    deadline = t0 + cfg["time_budget_minutes"] * 60
    logs = []

    def log(msg):
        line = f"[{now().strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        logs.append(line)

    f = Fetcher(cfg["request_timeout_seconds"])
    phases = {}
    state = {"apps": {}, "feed_stats": {}, "cat_sf": [], "cands": [], "scanned": [], "fetched": 0, "low": 0, "partial": False}

    def write_run(status):
        run = {
            "date": today.isoformat(), "status": status, "started": started.isoformat(timespec="seconds"),
            "finished": now().isoformat(timespec="seconds"), "minutes": round((time.monotonic() - t0) / 60, 1),
            "phase_minutes": phases, "partial": state["partial"], "storefronts": len(storefronts),
            "category_storefronts_today": state["cat_sf"], "feeds": state["feed_stats"],
            "unique_chart_apps": len(state["apps"]), "eligible_candidates": len(state["cands"]),
            "apps_scanned": len(state["scanned"]), "reviews_fetched": state["fetched"], "low_star_kept": state["low"],
            "review_files": len(list((out / "reviews").glob("*.json"))) if (out / "reviews").exists() else 0,
            "requests": f.requests, "failures": f.failures, "http_status": f.status,
            "final_spacing_s": {"feeds": f.spacing, "lookup": f.lookup_spacing},
            "error_samples": f.errors, "log": logs,
        }
        save_json(out / "latest/run.json", run)

    def phase_done(name, t_start):
        phases[name] = round((time.monotonic() - t_start) / 60, 1)
        write_run(f"running (after {name})")

    try:
        tp = time.monotonic()
        f.deadline = t0 + cfg["charts_budget_minutes"] * 60
        state["apps"], state["feed_stats"], state["cat_sf"] = collect_charts(f, storefronts, cfg, today, log)
        if f.past_deadline():
            state["partial"] = True
            log("charts: hit the charts time budget, continuing with what we have")
        phase_done("charts", tp)
        apps = state["apps"]

        tp = time.monotonic()
        f.deadline = t0 + cfg["lookup_budget_minutes"] * 60
        cache = load_json(out / "state/lookup_cache.json", {})
        cache = collect_lookups(f, apps, cache, cfg, today, log)
        if f.past_deadline():
            state["partial"] = True
            log("lookup: hit the lookup time budget, uncached apps wait for tomorrow")
        stale = (today - dt.timedelta(days=60)).isoformat()
        cache = {k: v for k, v in cache.items() if v["fetched"] >= stale}
        save_json(out / "state/lookup_cache.json", cache, compact=True)

        cands = build_candidates(apps, cache, cfg)
        state["cands"] = cands
        save_json(out / "latest/candidates.json", cands, compact=True)
        log(f"candidates: {len(cands)} eligible proven apps (excluded genres removed)")
        phase_done("lookup", tp)

        tp = time.monotonic()
        f.deadline = deadline
        history = load_json(out / "state/history.json", {})
        rescan_cut = (today - dt.timedelta(days=cfg["rescan_after_days"])).isoformat()
        todo = [c for c in cands if c["scan"] and history.get(c["id"], "") < rescan_cut][:cfg["apps_to_scan_per_day"]]
        log(f"scanning reviews for {len(todo)} apps")
        with ThreadPoolExecutor(cfg["workers"]) as ex:
            futs = {ex.submit(scan_app, f, c, cfg, today, deadline): c for c in todo}
            for fut in as_completed(futs):
                c = futs[fut]
                try:
                    stats, low = fut.result()
                except Exception as e:  # never let one app kill the run
                    f._fail(c["id"], f"scan error {e!r}"[:160])
                    continue
                fetched = sum(s["fetched"] for s in stats.values())
                if fetched == 0:
                    continue
                doc = merge_reviews(out / f"reviews/{c['id']}.json", c, stats, low, cfg, today)
                history[c["id"]] = today.isoformat()
                hist = {str(s): sum(st["hist"][str(s)] for st in stats.values()) for s in range(1, 6)}
                state["scanned"].append({"id": c["id"], "name": c["name"], "genre": c["genre"], "fetched": fetched,
                                         "hist": hist, "low_new": len(low), "low_total": len(doc["reviews"]),
                                         "low_share": round((hist["1"] + hist["2"]) / fetched, 3)})
                state["fetched"] += fetched
                state["low"] += len(low)
        if f.past_deadline():
            state["partial"] = True

        # housekeeping: drop review files for apps not scanned in N days
        drop_cut = (today - dt.timedelta(days=cfg["drop_app_files_after_days"])).isoformat()
        for p in (out / "reviews").glob("*.json") if (out / "reviews").exists() else []:
            if history.get(p.stem, "") < drop_cut:
                p.unlink()
                history.pop(p.stem, None)
        save_json(out / "state/history.json", history, compact=True)
        state["scanned"].sort(key=lambda s: s["low_new"], reverse=True)
        save_json(out / "latest/scanned.json", state["scanned"])
        phases["reviews"] = round((time.monotonic() - tp) / 60, 1)
        log(f"done: scanned {len(state['scanned'])} apps, {state['fetched']} reviews, {state['low']} low-star kept, "
            f"{f.requests} requests, {f.failures} failures, partial={state['partial']}, status={f.status}")
        write_run("ok")
    except Exception as e:
        log(f"FATAL: {e!r}")
        write_run(f"error: {e!r}"[:300])
        raise
    # fail the job only if nothing at all came back (Apple blocked us / endpoints changed)
    if not state["apps"]:
        print("ERROR: no chart data at all", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
