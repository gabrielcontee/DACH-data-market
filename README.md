<div align="center">

# DACH job search: iOS, Kotlin/Spring and AI roles

[![tests](https://img.shields.io/github/actions/workflow/status/gabrielcontee/DACH-data-market/tests.yml?branch=main&label=tests&labelColor=221F1A&color=6FA37F&style=flat-square)](https://github.com/gabrielcontee/DACH-data-market/actions/workflows/tests.yml)
[![live postings](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fgabrielcontee%2FDACH-data-market%2Fmain%2Fdocs%2Fdata%2Fmeta.json&query=%24.live_postings&label=live%20postings&labelColor=221F1A&color=E3A23F&style=flat-square&cacheSeconds=1800)](https://gabrielcontee.github.io/DACH-data-market/)

**[Open the site](https://gabrielcontee.github.io/DACH-data-market/)**

</div>

A weekday snapshot of job postings in Germany, Austria and Switzerland that
fit one CV: senior iOS, Kotlin/Spring Boot backend, and AI roles. Each
posting gets a 0-100 fit score, and the postings table opens on Vienna plus
anything that mentions remote.

Forked from [Christoph Ruckensteiner's DACH data job market tracker](https://github.com/Chrisinho8/DACH-data-job-market),
which tracks data and AI roles on a Databricks pipeline. This fork keeps his
site and swaps the pipeline for one Python script run by GitHub Actions.

## What it searches for

| Group | Role families | Read from |
| --- | --- | --- |
| Your stack | iOS Engineer, Kotlin / Spring Backend, Java Backend, Mobile Engineer | the title, plus the full advert for generic titles ("Backend Engineer" found by a Kotlin search) |
| AI | AI Engineer, GenAI / LLM, ML Engineer, MLOps, AI Consulting, AI Research | the title, with the original tracker's rules |

Left out on purpose: data and BI roles, Android-only, Flutter and React
Native roles, junior roles and entry programmes, and non-engineering jobs
(product, sales, QA, design).

## The fit score

`src/fit.py` scores every posting against the CV:

- **Role**: iOS and Kotlin/Spring start at 65, Java and generic mobile at 45,
  GenAI and AI engineer at 45, the other AI families lower.
- **Skills** named in the title or snippet that are on the CV: +5 each, up
  to +25. Mobile and backend in the same posting: +10.
- **Seniority**: senior +5.
- **Gaps**: German at C1 or above -15, two or more database skills -10,
  model-training stack -10, advert written in German -5.

65 or more is a **strong** fit. Below that, AI roles are labelled **AI** and
the rest **partial**. Every weight is a constant in that file.

## How it runs

```
Adzuna API        de · at · ch, 16 searches, ~100 calls a run
    │
    ▼
src/adzuna.py     sorted newest first, cached per day under raw/
    │
    ▼
src/pipeline.py   merge searches → parse → quality rules → dedupe →
    │             classify (src/classify.py) → skills (src/matcher.py)
    │             → fit (src/fit.py) → the site's JSON files
    ▼
docs/data/*.json  committed by the workflow; state/ keeps the registry
    │
    ▼
GitHub Pages      docs/, static, no backend
```

`.github/workflows/refresh.yml` runs at 05:30 UTC on weekdays. Adzuna's free
key allows about 2,500 calls a month, so each run is capped at 100
(`ADZUNA_MAX_CALLS`). Big searches keep only their newest postings, and
`meta.json` lists which ones were cut.

### Setup

1. Get an `app_id` and `app_key` at [developer.adzuna.com](https://developer.adzuna.com).
2. Add them as repository secrets `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`
   (Settings → Secrets and variables → Actions).
3. Set Pages to deploy from `main`, folder `/docs` (Settings → Pages).
4. Run **refresh data** once from the Actions tab.

To run it locally:

```bash
pip install -r requirements.txt
export ADZUNA_APP_ID=... ADZUNA_APP_KEY=...
python src/pipeline.py
pytest tests/
```

### Tuning

- Searches and how deep each is read: `QUERIES` in `src/adzuna.py`.
- Role rules: `src/classify.py`, with test cases in `tests/test_classify.py`.
- Skills: `src/skills_dictionary.py`.
- Fit weights: `src/fit.py`.

## Limitations

- **One aggregator is not the whole market**, and its coverage is uneven
  across the three countries.
- **Descriptions are cut at about 500 characters**, mostly company intro.
  Skills, remote/hybrid and German-level flags only see that part, so they
  are floors.
- **No remote flag from the source.** "Remote" means the title or snippet
  says so; a blank means not stated.
- **A listed posting is not necessarily open.** It was live at the last
  run.
- **Multi-location jobs appear once per city.**

`notebooks/` holds the original Databricks pipeline. This fork no longer
runs it.

## Licence

MIT, as the original. The job data belongs to Adzuna and its source boards.
