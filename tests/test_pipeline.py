"""The whole build step on fake Adzuna rows: what reaches the site, in
the shapes docs/app.js reads."""

import datetime
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

import pipeline  # noqa: E402
from sample_adzuna import make_rows  # noqa: E402

TODAY = datetime.date(2026, 11, 24)
REPORT = {"calls": 0, "queries": []}

# The keys the site reads from each file, from the original exports.
SHAPES = {
    "market_summary": {"snapshot_date", "live_postings", "employers",
                       "avg_age_days", "median_age_days", "pct_over_7d",
                       "pct_over_30d", "pct_over_60d", "pct_over_90d",
                       "pct_agency", "pct_english"},
    "role_breakdown": {"country", "role_group", "role_family", "seniority",
                       "n_postings", "avg_age_days", "median_age_days",
                       "pct_over_7d", "pct_over_30d", "pct_over_60d",
                       "pct_over_90d", "pct_english"},
    "city_breakdown": {"country", "city", "n_postings", "avg_age_days",
                       "pct_english", "pct_agency"},
    "city_role_breakdown": {"country", "city", "role_family", "n_postings",
                            "avg_age_days", "pct_english", "pct_agency"},
    "country_breakdown": {"country", "n_postings", "employers",
                          "avg_age_days", "median_age_days", "pct_over_30d",
                          "pct_over_60d", "pct_over_90d", "pct_english",
                          "pct_with_salary", "pct_agency"},
    "skill_demand": {"skill", "skill_category", "n_postings",
                     "pct_postings", "avg_age_days", "snapshot_date"},
    "skill_by_role": {"role_family", "skill", "skill_category", "n_postings",
                      "role_postings", "pct_role_postings", "avg_age_days",
                      "snapshot_date"},
    "agency_comparison": {"poster_type", "n_postings", "pct", "avg_age_days",
                          "median_age_days", "pct_over_60d"},
    "age_distribution": {"bucket", "sort_key", "n_postings", "pct"},
    "history": {"snapshot_date", "metric", "dimension", "value"},
    "new_postings_daily": {"created_date", "country", "role_family",
                           "seniority", "n"},
    "postings": {"posting_id", "title", "company", "city", "country",
                 "role_group", "role_family", "seniority", "language",
                 "is_agency", "age_days", "created_date", "url", "skills",
                 "snapshot_date", "fit", "fit_label", "work_mode", "flags"},
}


@pytest.fixture
def run(tmp_path):
    data, state = tmp_path / "data", tmp_path / "state"
    # an old-tracker history file that must not survive the first run
    data.mkdir()
    (data / "history.json").write_text(json.dumps([
        {"snapshot_date": "2026-11-20T00:00:00.000", "metric": "role_count",
         "dimension": "data engineer", "value": 900.0}]))

    def go(today=TODAY, n=160):
        meta = pipeline.build(make_rows(n, today), today, REPORT, data, state)
        load = lambda f: json.loads((data / f"{f}.json").read_text())  # noqa
        return meta, load
    return go


def test_every_file_has_the_shape_the_site_reads(run):
    _, load = run()
    for name, keys in SHAPES.items():
        rows = load(name)
        assert rows, f"{name}.json is empty"
        assert keys <= set(rows[0]), f"{name}.json lacks {keys - set(rows[0])}"


def test_only_stack_and_ai_roles_are_published(run):
    _, load = run()
    fams = {r["role_family"] for r in load("postings")}
    assert fams <= {"ios engineer", "kotlin / spring backend", "java backend",
                    "mobile engineer", "ai engineer", "genai / llm",
                    "ml engineer", "mlops", "ai consultant", "ai research"}
    assert "ios engineer" in fams and "genai / llm" in fams


def test_juniors_and_excluded_roles_are_dropped(run):
    meta, load = run()
    titles = {r["title"] for r in load("postings")}
    for gone in ("Junior iOS Developer", "Product Owner iOS App",
                 "Flutter Developer (iOS & Android)",
                 "Data Engineer AI Platform"):
        assert gone not in titles
    assert meta["dropped"]["junior"] > 0


def test_fit_labels_and_flags(run):
    meta, load = run()
    by_title = {r["title"]: r for r in load("postings")}
    assert by_title["Senior iOS Engineer (m/w/d)"]["fit_label"] == "strong"
    assert by_title["GenAI Engineer"]["fit_label"] == "ai"
    assert "german_c1" in by_title["Lead iOS Engineer"]["flags"]
    assert "sql_heavy" in by_title[
        "Java Developer - Spring Boot (m/w/d)"]["flags"]
    assert by_title["Senior iOS Engineer (m/w/d)"]["work_mode"] == "hybrid"
    assert meta["fit_strong"] > 0 and meta["vienna"] > 0


def test_generic_backend_found_by_kotlin_query_is_kept(run):
    _, load = run()
    by_title = {r["title"]: r for r in load("postings")}
    assert by_title["Senior Backend Engineer"]["role_family"] == \
        "kotlin / spring backend"


def test_cities_are_normalised(run):
    _, load = run()
    cities = {(r["country"], r["city"]) for r in load("city_breakdown")}
    assert ("at", "wien") in cities and ("de", "muenchen") in cities


def test_first_run_starts_history_and_registry_fresh(run):
    meta, load = run()
    assert meta["tracking_since"] == TODAY.isoformat()
    h = load("history")
    assert {r["snapshot_date"][:10] for r in h} == {TODAY.isoformat()}
    assert not any(r["dimension"] == "data engineer" for r in h)
    days = {r["created_date"][:10] for r in load("new_postings_daily")}
    assert days and min(days) >= TODAY.isoformat()


def test_second_run_appends_and_same_day_rerun_replaces(run):
    run()
    run(TODAY + datetime.timedelta(days=1))
    meta, load = run(TODAY + datetime.timedelta(days=1))
    days = sorted({r["snapshot_date"][:10] for r in load("history")})
    assert days == [TODAY.isoformat(),
                    (TODAY + datetime.timedelta(days=1)).isoformat()]
    live = [r for r in load("history") if r["metric"] == "live_postings"]
    assert len(live) == 2
    assert meta["tracking_since"] == TODAY.isoformat()


def test_refuses_to_publish_a_broken_fetch(run):
    with pytest.raises(SystemExit):
        run(n=5)


def test_postings_are_newest_first_and_linkable(run):
    _, load = run()
    p = load("postings")
    dates = [r["created_date"] for r in p]
    assert dates == sorted(dates, reverse=True)
    assert all(r["url"].startswith("https://") for r in p)
