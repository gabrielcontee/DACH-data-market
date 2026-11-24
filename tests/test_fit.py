import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

import fit  # noqa: E402
from matcher import extract  # noqa: E402


def score(family, text="", **kw):
    return fit.score(family, extract(text), **kw)


def test_plain_ios_job_is_a_strong_fit():
    s = score("ios engineer", "iOS Developer", seniority="mid")
    assert fit.label("ios engineer", s) == "strong"


def test_german_ios_advert_is_still_strong():
    s = score("ios engineer", "iOS Entwickler", language="de")
    assert fit.label("ios engineer", s) == "strong"


def test_mobile_and_backend_beats_mobile_only():
    both = score("ios engineer", "iOS, Swift and Kotlin Spring Boot backend")
    one = score("ios engineer", "iOS and Swift")
    assert both > one


def test_java_without_spring_is_partial():
    s = score("java backend", "Java Developer", language="de")
    assert fit.label("java backend", s) == "partial"


def test_java_found_by_spring_query_gets_closer():
    plain = score("java backend", "Java Developer")
    tagged = score("java backend", "Java Developer", tags=["spring_text"])
    assert tagged > plain


def test_german_c1_costs():
    base = score("kotlin / spring backend", "Kotlin")
    c1 = score("kotlin / spring backend", "Kotlin", german_c1=True)
    assert c1 < base


def test_sql_heavy_costs_and_is_flagged():
    text = "Kotlin, PostgreSQL, Oracle and SQL Server"
    assert score("kotlin / spring backend", text) < \
        score("kotlin / spring backend", "Kotlin")
    assert "sql_heavy" in fit.flags(extract(text), False)


def test_genai_role_is_labelled_ai():
    s = score("genai / llm", "LLM Engineer, Python")
    assert fit.label("genai / llm", s) == "ai"


def test_agentic_role_with_your_stack_can_be_strong():
    s = score("genai / llm",
              "Agentic AI engineer: LLM agents, MCP, Kotlin, Spring Boot, "
              "Kubernetes", seniority="senior")
    assert fit.label("genai / llm", s) == "strong"


def test_ml_research_ranks_below_genai():
    assert score("ai research", "PyTorch") < score("genai / llm", "LLM")


def test_score_is_bounded():
    s = score("ios engineer", " ".join(sorted(fit.CV_SKILLS)) +
              " swift ios kotlin spring", seniority="senior",
              tags=["kotlin_text"])
    assert 0 <= s <= 100
    assert fit.score("ai research", ["pytorch", "python"],
                     german_c1=True, language="de") >= 0
