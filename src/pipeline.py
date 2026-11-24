"""Daily refresh: Adzuna -> classify -> CV fit -> docs/data/*.json.

Replaces the Databricks notebooks for this fork. Run by
.github/workflows/refresh.yml; locally:

    export ADZUNA_APP_ID=... ADZUNA_APP_KEY=...
    python src/pipeline.py

The JSON files keep the shapes the site already reads, so docs/app.js
only needed new role names, the fit column and the Vienna filter.
State that has to survive between runs (the registry of every posting
ever seen, and the day tracking started) lives in state/.
"""

import collections
import datetime
import hashlib
import html
import json
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import adzuna                                   # noqa: E402
import classify as C                            # noqa: E402
import fit                                      # noqa: E402
from matcher import extract, categorise         # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_AGE_DAYS = 365
MIN_FAMILY_FOR_SKILLS = 20      # thinner families would be noise
MIN_POSTINGS_TO_PUBLISH = 25    # fewer means the fetch broke: keep yesterday's

CITY_STATES = {"berlin", "hamburg", "bremen", "wien",
               "basel-stadt", "genf", "geneve", "geneva"}
VIENNA = ("at", "wien")


# ---- parsing ---------------------------------------------------------

def clean_text(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def city_of(area):
    """Same rules as the original silver notebook: city states keep
    their state name, otherwise the third level, otherwise the second."""
    a2 = C.fold(area[1]) if len(area) > 1 and area[1] else None
    a3 = C.fold(area[2]) if len(area) > 2 and area[2] else None
    if a2 in CITY_STATES:
        c = a2
    elif a3:
        c = a3
    else:
        c = a2 or "unknown"
    c = re.sub(r"\s*\(.*?\)\s*$", "", c).strip()           # "muenchen (kreis)"
    c = re.sub(r"[-\s](umgebung|umland|land|stadt)$", "", c)  # "graz-umgebung"
    c = re.sub(r"^(region|regionalverband)\s+", "", c)      # "region hannover"
    c = re.sub(r"(\s+im\s+breisgau|-mittelland)$", "", c)
    c = re.sub(r" am main$", "", c)
    return c.strip() or "unknown"


def _num(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def merge_queries(raw_rows):
    """One row per Adzuna advert, carrying every query that found it."""
    by_id = {}
    for r in raw_rows:
        key = (r["_country"], str(r.get("id")))
        if key in by_id:
            m = by_id[key]
            m["_tags"] = sorted(set(m["_tags"]) | set(r["_tags"]))
            m["_queries"] = sorted(set(m["_queries"]) | {r["_query"]})
        else:
            by_id[key] = {**r, "_queries": [r["_query"]]}
    return list(by_id.values())


def parse(r, today):
    title = clean_text(r.get("title"))
    desc = clean_text(r.get("description"))
    company = clean_text((r.get("company") or {}).get("display_name"))
    loc = r.get("location") or {}
    created = str(r.get("created") or "")[:10]
    try:
        created_d = datetime.date.fromisoformat(created)
    except ValueError:
        created_d = None
    tags = r.get("_tags", [])

    family = C.classify(title, tags)
    skills = extract(f"{title} . {desc}")
    sen = C.seniority(title)
    lang = C.language(desc)
    c1 = C.german_c1(title, desc)
    score = fit.score(family, skills, sen, lang, c1, tags, title)

    city = city_of(loc.get("area") or [])
    return {
        "adzuna_id": str(r.get("id")),
        "country": r["_country"],
        "title": title,
        "company": company,
        "city": city,
        "description": desc,
        "desc_truncated": desc.endswith("…"),
        "url": r.get("redirect_url") or "",
        "role_family": family,
        "role_group": C.role_group(family),
        "seniority": sen,
        "language": lang,
        "is_agency": C.is_agency(company),
        "work_mode": C.work_mode(title, desc),
        "german_c1": c1,
        "skills": skills,
        "fit": score,
        "fit_label": fit.label(family, score),
        "flags": fit.flags(skills, c1),
        "salary_min": _num(r.get("salary_min")),
        "salary_max": _num(r.get("salary_max")),
        "created_date": created_d,
        "age_days": (today - created_d).days if created_d else None,
        "tags": tags,
        "queries": r.get("_queries", []),
    }


def quality_ok(p, today):
    """The original quality rules. A failing row is quarantined."""
    return (len(p["title"]) > 3
            and p["role_family"] != "invalid"
            and len(p["company"]) > 1
            and p["created_date"] is not None
            and datetime.date(2024, 1, 1) <= p["created_date"] <= today
            and p["age_days"] >= 0
            and (p["salary_min"] is None
                 or 12000 <= p["salary_min"] <= 400000)
            and (p["salary_max"] is None or p["salary_min"] is None
                 or p["salary_max"] >= p["salary_min"]))


def posting_id(p):
    key = "|".join([p["title"].lower(), p["company"].lower(), p["city"],
                    p["description"].lower()[:200]])
    return hashlib.sha256(key.encode()).hexdigest()


def dedupe(rows):
    """Same job relisted under a new id: keep the oldest, merge tags."""
    best = {}
    for p in sorted(rows, key=lambda x: (x["created_date"], x["adzuna_id"])):
        pid = posting_id(p)
        if pid in best:
            b = best[pid]
            b["tags"] = sorted(set(b["tags"]) | set(p["tags"]))
            b["queries"] = sorted(set(b["queries"]) | set(p["queries"]))
            continue
        best[pid] = {**p, "posting_id": pid}
    return list(best.values())


# ---- small aggregation helpers ---------------------------------------

def r1(x):
    return round(x, 1)


def pct(rows, pred):
    return r1(100 * sum(1 for r in rows if pred(r)) / len(rows)) if rows else 0.0


def avg(vals):
    vals = list(vals)
    return r1(sum(vals) / len(vals)) if vals else 0.0


def median_low(vals):
    """Spark's percentile_approx(x, 0.5): the lower middle value."""
    v = sorted(vals)
    return v[(len(v) - 1) // 2] if v else 0


def group(rows, *keys):
    g = collections.defaultdict(list)
    for r in rows:
        g[tuple(r[k] for k in keys)].append(r)
    return g


def ts(d):
    """Dates as the original export wrote them, so nothing in the site
    that compares these strings sees two formats."""
    d = d if isinstance(d, str) else d.isoformat()
    return f"{d[:10]}T00:00:00.000"


def ages(rows):
    return [r["age_days"] for r in rows]


def survival(rows):
    return {f"pct_over_{d}d": pct(rows, lambda r, d=d: r["age_days"] > d)
            for d in (7, 30, 60, 90)}


# ---- the tables ------------------------------------------------------

def aggregate(P, today):
    T = ts(today)
    out = {}

    out["market_summary"] = [{
        "snapshot_date": T,
        "live_postings": len(P),
        "employers": len({r["company"] for r in P}),
        "avg_age_days": avg(ages(P)),
        "median_age_days": median_low(ages(P)),
        **survival(P),
        "pct_agency": pct(P, lambda r: r["is_agency"]),
        "pct_english": pct(P, lambda r: r["language"] == "en"),
    }]

    buckets = [(7, "0-7 days"), (14, "8-14 days"), (30, "15-30 days"),
               (60, "31-60 days"), (90, "61-90 days"),
               (180, "91-180 days"), (365, "181-365 days")]

    def bucket(a):
        for i, (hi, name) in enumerate(buckets):
            if a <= hi:
                return i + 1, name
        return len(buckets), buckets[-1][1]

    bc = collections.Counter(bucket(r["age_days"]) for r in P)
    out["age_distribution"] = [
        {"bucket": name, "sort_key": k, "n_postings": n,
         "pct": r1(100 * n / len(P))}
        for (k, name), n in sorted(bc.items())]

    out["agency_comparison"] = [
        {"poster_type": "Recruitment agency" if ag else "Direct employer",
         "n_postings": len(g), "pct": r1(100 * len(g) / len(P)),
         "avg_age_days": avg(ages(g)), "median_age_days": median_low(ages(g)),
         "pct_over_60d": pct(g, lambda r: r["age_days"] > 60)}
        for (ag,), g in group(P, "is_agency").items()]

    out["role_breakdown"] = sorted([
        {"country": c, "role_group": rg, "role_family": rf, "seniority": s,
         "n_postings": len(g), "avg_age_days": avg(ages(g)),
         "median_age_days": median_low(ages(g)), **survival(g),
         "pct_english": pct(g, lambda r: r["language"] == "en")}
        for (c, rg, rf, s), g in group(
            P, "country", "role_group", "role_family", "seniority").items()],
        key=lambda r: -r["n_postings"])

    def place(g):
        return {"n_postings": len(g), "avg_age_days": avg(ages(g)),
                "pct_english": pct(g, lambda r: r["language"] == "en"),
                "pct_agency": pct(g, lambda r: r["is_agency"])}

    out["city_breakdown"] = sorted([
        {"country": c, "city": city, **place(g)}
        for (c, city), g in group(P, "country", "city").items()],
        key=lambda r: -r["n_postings"])

    out["city_role_breakdown"] = sorted([
        {"country": c, "city": city, "role_family": rf, **place(g)}
        for (c, city, rf), g in group(
            P, "country", "city", "role_family").items()],
        key=lambda r: -r["n_postings"])

    out["country_breakdown"] = sorted([
        {"country": c, "n_postings": len(g),
         "employers": len({r["company"] for r in g}),
         "avg_age_days": avg(ages(g)), "median_age_days": median_low(ages(g)),
         **{k: v for k, v in survival(g).items() if k != "pct_over_7d"},
         "pct_english": pct(g, lambda r: r["language"] == "en"),
         "pct_with_salary": pct(g, lambda r: r["salary_min"] is not None),
         "pct_agency": pct(g, lambda r: r["is_agency"])}
        for (c,), g in group(P, "country").items()],
        key=lambda r: -r["n_postings"])

    by_skill = collections.defaultdict(list)
    for r in P:
        for s in r["skills"]:
            by_skill[s].append(r)
    out["skill_demand"] = sorted([
        {"skill": s, "skill_category": categorise(s), "n_postings": len(g),
         "pct_postings": r1(100 * len(g) / len(P)),
         "avg_age_days": avg(ages(g)), "snapshot_date": T}
        for s, g in by_skill.items()],
        key=lambda r: (-r["n_postings"], r["skill"]))

    sbr = []
    for (rf,), g in group(P, "role_family").items():
        if len(g) < MIN_FAMILY_FOR_SKILLS:
            continue
        fam_skill = collections.defaultdict(list)
        for r in g:
            for s in r["skills"]:
                fam_skill[s].append(r)
        for s, gs in fam_skill.items():
            if len(gs) < 3:
                continue
            sbr.append({"role_family": rf, "skill": s,
                        "skill_category": categorise(s),
                        "n_postings": len(gs), "role_postings": len(g),
                        "pct_role_postings": r1(100 * len(gs) / len(g)),
                        "avg_age_days": avg(ages(gs)), "snapshot_date": T})
    out["skill_by_role"] = sorted(
        sbr, key=lambda r: (r["role_family"], -r["n_postings"], r["skill"]))

    return out


def history_rows(P, agg, today):
    T = ts(today)
    ms = agg["market_summary"][0]
    rows = [
        {"snapshot_date": T, "metric": "live_postings", "dimension": "all",
         "value": float(ms["live_postings"])},
        {"snapshot_date": T, "metric": "avg_age_days", "dimension": "all",
         "value": ms["avg_age_days"]},
        {"snapshot_date": T, "metric": "pct_over_60d", "dimension": "all",
         "value": ms["pct_over_60d"]},
        {"snapshot_date": T, "metric": "fit_strong", "dimension": "all",
         "value": float(sum(r["fit_label"] == "strong" for r in P))},
        {"snapshot_date": T, "metric": "ai_share_of_market",
         "dimension": "all",
         "value": pct(P, lambda r: r["role_group"] == "ai")},
    ]
    rows += [{"snapshot_date": T, "metric": "skill_pct",
              "dimension": s["skill"], "value": s["pct_postings"]}
             for s in agg["skill_demand"]]
    for (rf,), g in group(P, "role_family").items():
        rows.append({"snapshot_date": T, "metric": "role_count",
                     "dimension": rf, "value": float(len(g))})
        rows.append({"snapshot_date": T, "metric": "role_avg_age_days",
                     "dimension": rf, "value": avg(ages(g))})
    return rows


def public_postings(P, today):
    T = ts(today)
    rows = [{
        "posting_id": r["posting_id"],
        "title": r["title"],
        "company": r["company"],
        "city": r["city"],
        "country": r["country"],
        "role_group": r["role_group"],
        "role_family": r["role_family"],
        "seniority": r["seniority"],
        "language": r["language"],
        "is_agency": r["is_agency"],
        "age_days": r["age_days"],
        "created_date": ts(r["created_date"]),
        "url": r["url"],
        "skills": r["skills"],
        "fit": r["fit"],
        "fit_label": r["fit_label"],
        "work_mode": r["work_mode"],
        "flags": r["flags"],
        "snapshot_date": T,
    } for r in P if r["url"]]
    rows.sort(key=lambda r: (r["created_date"], r["posting_id"]),
              reverse=True)
    return rows


# ---- state -----------------------------------------------------------

def load_json(path, default):
    try:
        return json.loads(pathlib.Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path, obj, compact=False):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(obj, indent=None if compact else 1,
                      separators=(",", ":") if compact else None,
                      ensure_ascii=False, default=str)
    path.write_text(body + "\n")


def update_registry(state, P, today):
    reg = state.setdefault("postings", {})
    for r in P:
        if r["posting_id"] not in reg:
            reg[r["posting_id"]] = {
                "created_date": r["created_date"].isoformat(),
                "country": r["country"], "role_family": r["role_family"],
                "seniority": r["seniority"], "first_seen": today.isoformat()}
    since = state["tracking_since"]
    counts = collections.Counter(
        (v["created_date"], v["country"], v["role_family"], v["seniority"])
        for v in reg.values() if v["created_date"] >= since)
    return [{"created_date": ts(d), "country": c, "role_family": rf,
             "seniority": s, "n": n}
            for (d, c, rf, s), n in sorted(counts.items())]


# ---- the run ---------------------------------------------------------

def build(raw_rows, today, fetch_report, data_dir, state_dir):
    """Everything after the fetch. Pure apart from the files it writes,
    so the tests can run it on fixture rows."""
    data_dir, state_dir = pathlib.Path(data_dir), pathlib.Path(state_dir)

    parsed = [parse(r, today) for r in merge_queries(raw_rows)]
    passed = [p for p in parsed if quality_ok(p, today)]
    quarantined = len(parsed) - len(passed)
    unique = dedupe(passed)

    reasons = collections.Counter()
    P = []
    for p in unique:
        if p["role_family"] not in C.KEEP:
            reasons[p["role_family"]] += 1
        elif p["seniority"] == "junior":
            reasons["junior"] += 1
        elif p["age_days"] > MAX_AGE_DAYS:
            reasons[f"older than {MAX_AGE_DAYS} days"] += 1
        else:
            P.append(p)

    print(f"raw rows {len(raw_rows):,} -> adverts {len(parsed):,} -> "
          f"passed quality {len(passed):,} -> unique {len(unique):,} -> "
          f"kept {len(P):,}")
    for k, n in reasons.most_common():
        print(f"  dropped {n:5,}  {k}")

    if len(P) < MIN_POSTINGS_TO_PUBLISH:
        raise SystemExit(
            f"only {len(P)} postings kept, refusing to publish over "
            f"yesterday's data")

    state_path = state_dir / "registry.json"
    state = load_json(state_path, None)
    first_run = state is None
    if first_run:
        state = {"tracking_since": today.isoformat(), "postings": {}}

    agg = aggregate(P, today)
    T = ts(today)

    # The old tracker's history counts data and AI roles; none of it is
    # comparable, so the first run of this pipeline starts a new one.
    history = [] if first_run else load_json(data_dir / "history.json", [])
    history = [h for h in history if h["snapshot_date"][:10] != T[:10]]
    history += history_rows(P, agg, today)

    new_daily = update_registry(state, P, today)
    postings = public_postings(P, today)

    labels = collections.Counter(r["fit_label"] for r in P)
    ms = agg["market_summary"][0]
    meta = {
        "updated": today.isoformat(),
        "tracking_since": state["tracking_since"],
        "live_postings": ms["live_postings"],
        "employers": ms["employers"],
        "avg_age_days": ms["avg_age_days"],
        "median_age_days": float(ms["median_age_days"]),
        "pct_over_60d": ms["pct_over_60d"],
        "fit_strong": labels["strong"],
        "fit_partial": labels["partial"],
        "fit_ai": labels["ai"],
        "vienna": sum((r["country"], r["city"]) == VIENNA for r in P),
        "vienna_strong": sum((r["country"], r["city"]) == VIENNA
                             and r["fit_label"] == "strong" for r in P),
        "remote_mentioned": sum(r["work_mode"] == "remote" for r in P),
        "hybrid_mentioned": sum(r["work_mode"] == "hybrid" for r in P),
        "quarantined": quarantined,
        "quarantine_rate": round(quarantined / max(len(parsed), 1), 4),
        "postings_published": len(postings),
        "dropped": dict(reasons.most_common()),
        "matcher_precision": None,
        "matcher_recall": None,
        "desc_truncated_pct": pct(P, lambda r: r["desc_truncated"]),
        "api_calls": fetch_report.get("calls"),
        "queries_newest_only": sorted(
            f"{q['query']} ({q['country']})"
            for q in fetch_report.get("queries", []) if not q["complete"]),
    }

    for name, obj in agg.items():
        write_json(data_dir / f"{name}.json", obj)
    write_json(data_dir / "history.json", history)
    write_json(data_dir / "new_postings_daily.json", new_daily)
    write_json(data_dir / "postings.json", postings, compact=True)
    write_json(data_dir / "meta.json", meta)
    write_json(state_path, state, compact=True)

    print(f"published {len(postings):,} postings: {labels['strong']} strong, "
          f"{labels['partial']} partial, {labels['ai']} AI; "
          f"{meta['vienna']} in Vienna")
    return meta


def main():
    today = datetime.date.today()
    app_id, app_key = adzuna.credentials()
    max_calls = int(os.environ.get("ADZUNA_MAX_CALLS", "100"))
    raw, report = adzuna.fetch_all(ROOT / "raw", max_calls, app_id, app_key,
                                   today=today.isoformat())
    if not raw:
        raise SystemExit("Adzuna returned no results at all")
    build(raw, today, report, ROOT / "docs" / "data", ROOT / "state")


if __name__ == "__main__":
    main()
