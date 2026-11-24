"""Adzuna search client: the queries, a call budget, and a day cache.

Adzuna's free key allows about 25 calls a minute and 2,500 a month.
The workflow runs on weekdays (about 22 runs a month), so each run gets
MAX_CALLS calls by default and the rest of the month is left for manual
re-runs. Queries run in the order below; when the budget runs out the
lower ones are cut short, and meta.json records which.

Every response is cached under RAW_DIR with the day in its name, so a
re-run on the same day costs no calls.
"""

import datetime
import json
import os
import pathlib
import random
import time

import requests

BASE = "https://api.adzuna.com/v1/api/jobs"

# Austria only for now: every search costs at least one call per country,
# and Germany is where the extra pages go. To search Germany and
# Switzerland again, set ADZUNA_COUNTRIES="at,de,ch" in refresh.yml.
ALL_COUNTRIES = ("at", "de", "ch")
DEFAULT_COUNTRIES = "at"


def countries_from_env():
    raw = os.environ.get("ADZUNA_COUNTRIES", DEFAULT_COUNTRIES)
    out = [c.strip().lower() for c in raw.split(",") if c.strip()]
    bad = [c for c in out if c not in ALL_COUNTRIES]
    if bad or not out:
        raise SystemExit(f"ADZUNA_COUNTRIES must be a comma-separated subset "
                         f"of {','.join(ALL_COUNTRIES)}, got {raw!r}")
    return out


COUNTRIES = countries_from_env()
PER_PAGE = 50
RETRY_STATUS = {429, 500, 502, 503, 504}
RETRIES = 6
PACE = 2.6                              # seconds between calls: 25 a minute

# name -> Adzuna params, the pages to read at most, and the tags given
# to every posting it returns. `title_only` matches the job title;
# `what_or` matches any of its words anywhere in the advert. The tags
# let classify.py and fit.py know a stack word was in the full text even
# when the snippet we get back does not show it.
QUERIES = [
    # your stack, newest first, read deepest
    ("ios",            {"title_only": "ios"},                       8, {"ios_title"}),
    ("swift",          {"title_only": "swift"},                     2, {"ios_title"}),
    ("kotlin",         {"title_only": "kotlin"},                    6, {"kotlin_title"}),
    ("spring",         {"title_only": "spring"},                    6, {"spring_title"}),
    ("java+spring",    {"title_only": "java",
                        "what_or": "spring kotlin"},                6, {"spring_text"}),
    ("backend+kotlin", {"title_only": "backend",
                        "what_or": "kotlin spring"},                6, {"kotlin_text"}),
    ("software+kotlin", {"title_only": "software",
                         "what": "kotlin"},                         4, {"kotlin_text"}),
    ("mobile+ios",     {"title_only": "mobile",
                        "what_or": "ios swift"},                    4, {"ios_text"}),
    ("app+ios",        {"title_only": "app",
                        "what_or": "ios swift"},                    3, {"ios_text"}),
    # AI roles, kept but read less deep
    ("llm",            {"title_only": "llm"},                       2, {"ai"}),
    ("genai",          {"title_only": "genai"},                     2, {"ai"}),
    ("ai engineer",    {"title_only": "ai engineer"},               3, {"ai"}),
    ("ki entwickler",  {"title_only": "ki entwickler"},             2, {"ai"}),
    ("agentic",        {"what": "agentic engineer"},                2, {"ai"}),
    ("machine learning", {"title_only": "machine learning"},        2, {"ai"}),
    ("mlops",          {"title_only": "mlops"},                     1, {"ai"}),
]


class Budget:
    def __init__(self, max_calls):
        self.max_calls = max_calls
        self.calls = 0
        self.cache_hits = 0

    @property
    def left(self):
        return self.max_calls - self.calls


def _backoff(attempt):
    return min(30, 2 ** attempt) * (0.5 + random.random())


def _slug(s):
    return "".join(c if c.isalnum() else "-" for c in s).strip("-")


def fetch_page(country, name, params, page, budget, raw_dir, today,
               app_id, app_key, session=None):
    """One page of results, from the cache if today's copy exists.
    Returns None when the budget is spent."""
    path = pathlib.Path(raw_dir) / f"{country}__{_slug(name)}__p{page}__{today}.json"
    if path.exists():
        budget.cache_hits += 1
        return json.loads(path.read_text())
    if budget.left <= 0:
        return None

    q = {"app_id": app_id, "app_key": app_key,
         "results_per_page": PER_PAGE, "sort_by": "date",
         "content-type": "application/json", **params}
    http = session or requests

    for attempt in range(RETRIES):
        try:
            r = http.get(f"{BASE}/{country}/search/{page}", params=q,
                         timeout=30)
        except requests.exceptions.RequestException as e:
            wait = _backoff(attempt)
            print(f"  {type(e).__name__}, retrying in {wait:.0f}s")
            time.sleep(wait)
            continue

        budget.calls += 1
        if r.status_code in RETRY_STATUS:
            ra = r.headers.get("Retry-After")
            wait = float(ra) if ra and ra.isdigit() else _backoff(attempt)
            print(f"  HTTP {r.status_code}, retrying in {wait:.0f}s")
            time.sleep(wait)
            if budget.left <= 0:
                return None
            continue
        if r.status_code == 410:            # past the last page
            return {"results": [], "count": 0}
        if r.status_code in (401, 403):
            raise SystemExit(
                f"Adzuna refused the key (HTTP {r.status_code}). Check the "
                f"ADZUNA_APP_ID and ADZUNA_APP_KEY repository secrets.")
        r.raise_for_status()

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(r.text)
        time.sleep(PACE)
        return r.json()

    raise RuntimeError(f"gave up on {country}/{name}/p{page}")


def fetch_all(raw_dir, max_calls, app_id, app_key, today=None,
              queries=QUERIES, countries=COUNTRIES):
    """Every result of every query, each tagged with the query that
    found it. Returns (rows, report)."""
    today = today or datetime.date.today().isoformat()
    budget = Budget(max_calls)
    session = requests.Session()
    rows, report = [], []

    # First pages of every query before any second page, so a tight
    # budget still sees every query in every country once.
    plan = [(c, q) for q in queries for c in countries]
    state = {}
    for country, (name, params, max_pages, tags) in plan:
        data = fetch_page(country, name, params, 1, budget, raw_dir, today,
                          app_id, app_key, session)
        state[(country, name)] = data
        if data is None:
            report.append({"query": name, "country": country, "total": None,
                           "pages": 0, "complete": False})
            continue
        for r in data.get("results", []):
            rows.append({**r, "_country": country, "_query": name,
                         "_tags": sorted(tags)})

    for country, (name, params, max_pages, tags) in plan:
        first = state[(country, name)]
        if first is None:
            continue
        total = first.get("count", 0) or 0
        need = min(max_pages, -(-total // PER_PAGE)) if total else 1
        pages = 1
        complete = True
        for page in range(2, need + 1):
            data = fetch_page(country, name, params, page, budget, raw_dir,
                              today, app_id, app_key, session)
            if data is None:
                complete = False
                break
            res = data.get("results", [])
            for r in res:
                rows.append({**r, "_country": country, "_query": name,
                             "_tags": sorted(tags)})
            pages = page
            if len(res) < PER_PAGE:
                break
        if total > max_pages * PER_PAGE:
            complete = False            # capped on purpose: newest only
        report.append({"query": name, "country": country, "total": total,
                       "pages": pages, "complete": complete})
        print(f"{country}  {name:18} total={total:6}  pages={pages}"
              f"{'' if complete else '  (newest only)'}")

    print(f"API calls this run: {budget.calls}, from cache: "
          f"{budget.cache_hits}")
    return rows, {"calls": budget.calls, "cache_hits": budget.cache_hits,
                  "queries": report}


def credentials():
    app_id = os.environ.get("ADZUNA_APP_ID", "").strip()
    app_key = os.environ.get("ADZUNA_APP_KEY", "").strip()
    if not app_id or not app_key:
        raise SystemExit(
            "ADZUNA_APP_ID and ADZUNA_APP_KEY are not set. In GitHub they "
            "are repository secrets; locally, export them first.")
    return app_id, app_key
