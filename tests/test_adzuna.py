import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

import adzuna  # noqa: E402


def test_austria_only_by_default(monkeypatch):
    monkeypatch.delenv("ADZUNA_COUNTRIES", raising=False)
    assert adzuna.countries_from_env() == ["at"]


def test_countries_can_be_widened(monkeypatch):
    monkeypatch.setenv("ADZUNA_COUNTRIES", "at, DE,ch")
    assert adzuna.countries_from_env() == ["at", "de", "ch"]


def test_unknown_country_is_refused(monkeypatch):
    monkeypatch.setenv("ADZUNA_COUNTRIES", "at,uk")
    with pytest.raises(SystemExit):
        adzuna.countries_from_env()


def test_only_the_chosen_countries_are_fetched(tmp_path, monkeypatch):
    asked = []

    def fake_fetch(country, name, params, page, budget, *a, **k):
        asked.append(country)
        return {"count": 1, "results": []}

    monkeypatch.setattr(adzuna, "fetch_page", fake_fetch)
    adzuna.fetch_all(tmp_path, 100, "id", "key", today="2026-11-24",
                     countries=["at"])
    assert set(asked) == {"at"}
    assert len(asked) == len(adzuna.QUERIES)
