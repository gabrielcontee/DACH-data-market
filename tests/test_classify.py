import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from classify import (classify, seniority, work_mode, german_c1,  # noqa: E402
                      language, role_group)

CASES = [
    # iOS
    ("Senior iOS Engineer (m/w/d)",                      "ios engineer"),
    ("iOS Developer - SwiftUI",                          "ios engineer"),
    ("Swift Developer",                                  "ios engineer"),
    ("Mobile Engineer (iOS/Android)",                    "ios engineer"),
    ("Lead iOS Entwickler",                              "ios engineer"),
    ("App-Entwickler iOS (m/w/d)",                       "ios engineer"),
    ("iOS Software Engineer – AI features",              "ios engineer"),
    # Kotlin / Spring
    ("Senior Backend Engineer Kotlin",                   "kotlin / spring backend"),
    ("Java Developer - Spring Boot (m/w/d)",             "kotlin / spring backend"),
    ("Kotlin Entwickler (all genders)",                  "kotlin / spring backend"),
    # generic titles count when the query found Kotlin/Spring in the text
    ("Senior Backend Engineer",                          "other"),
    # Java
    ("Senior Java Developer",                            "java backend"),
    ("Java Softwareentwickler (m/w/d)",                  "java backend"),
    # generic mobile
    ("Senior Mobile Developer",                          "mobile engineer"),
    ("Kotlin Multiplatform Engineer",                    "mobile engineer"),
    # out: other mobile platforms
    ("Flutter Developer (iOS & Android)",                "cross-platform mobile"),
    ("React Native Engineer",                            "cross-platform mobile"),
    ("Android Developer (Kotlin)",                       "android"),
    # out: not engineering
    ("Product Owner iOS App",                            "other"),
    ("Sales Manager Mobile Apps",                        "other"),
    ("QA Engineer iOS",                                  "other"),
    ("SAP Fiori App Developer",                          "other"),
    ("Network Engineer Cisco IOS-XE",                    "other"),
    ("SWIFT Payments Specialist",                        "other"),
    # out: data roles, even with AI in the title
    ("Data Engineer AI Platform",                        "data"),
    ("Senior Data Scientist",                            "data"),
    ("Big Data Engineer Java",                           "data"),
    # AI families, as in the original tracker
    ("Machine Learning Engineer (m/w/d)",                "ml engineer"),
    ("MLOps Engineer",                                   "mlops"),
    ("GenAI Engineer",                                   "genai / llm"),
    ("Agentic AI Developer",                             "genai / llm"),
    ("AI Research Engineer",                             "ai research"),
    ("AI Product Manager",                               "ai consultant"),
    ("KI-Berater Digitalisierung",                       "ai consultant"),
    ("AI Engineer",                                      "ai engineer"),
    ("Senior Backend & AI Engineer",                     "ai engineer"),
    ("Projektmanager KI",                                "ai (other)"),
    # excludes beat everything
    ("Werkstudent iOS Entwicklung",                      "entry programme"),
    ("Praktikum Backend Kotlin",                         "entry programme"),
    ("Rechenzentrum Techniker",                          "data centre"),
    ("Controlling Specialist AI",                        "finance"),
]


@pytest.mark.parametrize("title,expected", CASES)
def test_classify(title, expected):
    assert classify(title) == expected


def test_generic_backend_title_counts_when_found_by_kotlin_query():
    assert classify("Senior Backend Engineer",
                    ["kotlin_text"]) == "kotlin / spring backend"
    assert classify("Softwareentwickler (m/w/d)",
                    ["spring_text"]) == "kotlin / spring backend"


def test_generic_mobile_title_found_by_ios_query():
    assert classify("Senior Software Engineer",
                    ["ios_text"]) == "mobile engineer"


def test_tags_do_not_rescue_data_roles():
    assert classify("Data Engineer", ["kotlin_text"]) == "data"


def test_role_groups():
    assert role_group("ios engineer") == "stack"
    assert role_group("genai / llm") == "ai"
    assert role_group("data") == "excluded"


@pytest.mark.parametrize("title,expected", [
    ("Senior iOS Engineer", "senior"),
    ("Lead Mobile Engineer", "senior"),
    ("Junior Java Developer", "junior"),
    ("Berufseinsteiger Softwareentwicklung", "junior"),
    ("iOS Developer", "mid"),
])
def test_seniority(title, expected):
    assert seniority(title) == expected


def test_work_mode():
    assert work_mode("iOS Developer (Remote)", "") == "remote"
    assert work_mode("iOS Developer", "Homeoffice möglich") == "remote"
    assert work_mode("iOS Developer", "hybrid, 2 Tage im Büro") == "hybrid"
    assert work_mode("iOS Developer", "remote or hybrid") == "hybrid"
    assert work_mode("iOS Developer", "Büro in Wien") == ""


def test_german_c1():
    assert german_c1("", "Deutsch auf C1-Niveau")
    assert german_c1("", "verhandlungssichere Deutschkenntnisse")
    assert german_c1("", "Fließende Deutschkenntnisse in Wort und Schrift")
    assert german_c1("", "Fluent German is a must")
    assert not german_c1("", "German is a plus, English is our working "
                             "language")
    assert not german_c1("", "Deutsch B2")


def test_language():
    assert language("Wir suchen dich mit Erfahrung in Swift") == "de"
    assert language("We are looking for an iOS engineer") == "en"
