"""Complaint theme lexicon shared by digest.py and reviews.py.

Keyword hits are only a triage signal: the daily Claude run reads and classifies the
actual reviews (in any language). Keep phrases lowercase.
"""
import re

# Themes that can become an app idea (a focused app can fix them).
OPPORTUNITY = {
    "paywall_price": ["subscription", "subscribe", "paywall", "pay wall", "premium", "pro version", "too expensive",
                      "overpriced", "price", "per month", "a month", "per year", "a year", "free trial", "trial",
                      "charged", "money grab", "cash grab", "greedy", "locked behind", "pay for", "lifetime"],
    "removed_regressed": ["removed", "no longer", "used to", "bring back", "new update", "latest update",
                          "since the update", "after the update", "after updating", "new version", "redesign",
                          "downgrade", "was better", "ruined"],
    "missing_feature": ["wish", "please add", "would be nice", "missing", "doesn't have", "does not have",
                        "no option", "no way to", "can't even", "cannot even", "need a way", "feature request",
                        "if only", "should have", "lacks", "lacking", "why can't", "why cant"],
    "ads": [" ads", "ads ", "advert", "commercial", "too many ads", "ad after", "pop up", "popup"],
    "account_privacy": ["sign up", "signup", "create an account", "forced to", "login", "log in", "privacy",
                        "my data", "personal data", "tracking", "permissions", "phone number", "email address"],
    "bloat_complexity": ["bloated", "bloat", "cluttered", "complicated", "confusing", "too many features",
                         "overcomplicated", "just want", "simple", "unintuitive", "hard to use"],
    "sync_export_data": ["sync", "export", "backup", "back up", "import", "icloud", "cloud", "widget", "offline",
                         "lost all", "lost my", "data loss", "csv", "pdf"],
    "locale_gap": ["arabic", "language", "translation", "not available in my country", "my country", "region",
                   "currency", "hijri", "right to left", "rtl", "metric", "localization"],
}

# Themes that are usually NOT an opportunity on their own (the incumbent's bug or ops issue).
NOISE = {
    "bugs_crashes": ["crash", "crashes", "bug", "freez", "not working", "doesn't work", "does not work", "broken",
                     "glitch", "won't load", "wont load", "keeps closing", "black screen", "stuck"],
    "support_billing": ["refund", "customer service", "support team", "no response", "scam", "fraud", "cancel",
                        "cancelled", "canceled", "charged twice", "banned", "suspended"],
}

ALL = {**OPPORTUNITY, **NOISE}
_PATTERNS = {k: [re.compile(re.escape(p)) for p in v] for k, v in ALL.items()}


def themes_of(text):
    t = " " + (text or "").lower() + " "
    return [k for k, pats in _PATTERNS.items() if any(p.search(t) for p in pats)]


def is_mostly_latin(text):
    letters = [c for c in (text or "") if c.isalpha()]
    if not letters:
        return True
    return sum(1 for c in letters if c.isascii()) / len(letters) > 0.8
