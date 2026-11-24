"""Fake Adzuna search results, shaped like the real API's, for tests and
for previewing the site without an API key."""

import datetime
import random

TITLES = [
    # (title, snippet, query, tags)
    ("Senior iOS Engineer (m/w/d)",
     "Wir suchen dich mit Erfahrung in Swift, SwiftUI und Combine. Hybrid "
     "in Wien.", "ios", ["ios_title"]),
    ("iOS Developer",
     "Join our team building our banking app in Swift and SwiftUI. Remote "
     "within Austria.", "ios", ["ios_title"]),
    ("Lead iOS Engineer",
     "Lead a team of iOS engineers. Swift, UIKit, XCTest, Fastlane. "
     "Fluent German is a must.", "ios", ["ios_title"]),
    ("Mobile Engineer (iOS/Android)",
     "Mobile app for 2M users. Swift and Kotlin, REST APIs.", "ios",
     ["ios_title"]),
    ("Senior Backend Engineer Kotlin",
     "Kotlin, Spring Boot, Kubernetes on GCP, microservices.", "kotlin",
     ["kotlin_title"]),
    ("Java Developer - Spring Boot (m/w/d)",
     "Spring Boot, PostgreSQL, Oracle und SQL Server. Homeoffice möglich.",
     "spring", ["spring_title"]),
    ("Senior Java Developer",
     "Java 21 backend services for our logistics platform.", "java+spring",
     ["spring_text"]),
    ("Senior Backend Engineer",
     "Our platform team builds APIs for the mobile apps.",
     "backend+kotlin", ["kotlin_text"]),
    ("Senior Mobile Developer",
     "Wir entwickeln unsere App für iOS und Android.", "mobile+ios",
     ["ios_text"]),
    ("Flutter Developer (iOS & Android)",
     "Flutter and Dart.", "mobile+ios", ["ios_text"]),
    ("Junior iOS Developer",
     "Start your career with Swift.", "ios", ["ios_title"]),
    ("Product Owner iOS App",
     "Own the roadmap.", "ios", ["ios_title"]),
    ("GenAI Engineer",
     "LLM agents, RAG and evals in Python.", "genai", ["ai"]),
    ("AI Engineer",
     "Agentic AI, MCP and LLM APIs. Kotlin backend.", "ai engineer", ["ai"]),
    ("Machine Learning Engineer",
     "PyTorch and MLflow on Kubernetes.", "machine learning", ["ai"]),
    ("Data Engineer AI Platform",
     "Spark and Databricks.", "ai engineer", ["ai"]),
]

PLACES = [
    ("at", ["Österreich", "Wien", "Wien"], "Wien"),
    ("at", ["Österreich", "Steiermark", "Graz"], "Graz"),
    ("de", ["Deutschland", "Berlin", "Berlin"], "Berlin"),
    ("de", ["Deutschland", "Bayern", "München (Kreis)"], "München"),
    ("ch", ["Schweiz", "Zürich", "Zürich"], "Zürich"),
]

COMPANIES = ["Acme Mobile GmbH", "Billa Digital", "Nordbank AG",
             "Alpine Apps", "Hays", "Kotlin Works", "Swiss Retail AG",
             "Data & Co", "Vienna Fintech"]


def make_rows(n, today, seed=7):
    rnd = random.Random(seed)
    rows = []
    for i in range(n):
        title, desc, query, tags = TITLES[i % len(TITLES)]
        country, area, display = PLACES[rnd.randrange(len(PLACES))]
        # every eighth advert is from today, so a first run has new
        # postings to count
        age = 0 if i % 8 == 0 else rnd.randrange(1, 90)
        created = today - datetime.timedelta(days=age)
        rows.append({
            "id": str(100000 + i),
            "title": title,
            "description": desc + " " + "x" * rnd.randrange(0, 40) + " …",
            "company": {"display_name": COMPANIES[i % len(COMPANIES)]},
            "location": {"display_name": display, "area": area},
            "category": {"label": "IT Jobs"},
            "redirect_url": f"https://www.adzuna.at/details/{100000 + i}",
            "created": created.isoformat() + "T08:00:00Z",
            "salary_min": None,
            "salary_max": None,
            "_country": country,
            "_query": query,
            "_tags": tags,
        })
    return rows
