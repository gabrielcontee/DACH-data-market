"""How well a posting fits the CV, as a 0-100 score and a label.

The score is about the CV only: stack, seniority and the known gaps.
Where the job is (Vienna, remote) is a separate filter on the site, so
a strong-fit job in Munich still reads as a strong fit.

Every weight is here, in one place, so tuning it is an edit to this
file and a re-run. The labels:

  strong   score >= STRONG
  ai       an AI-family role below that line
  partial  anything else that was kept
"""

from classify import IOS, KOTLIN, JAVA, MOBILE, role_group

STRONG = 65

# Where a role starts before its skills are counted.
BASE = {
    IOS:             65,
    KOTLIN:          65,
    JAVA:            45,
    MOBILE:          45,
    # LLM APIs and agents: the Bug Bot, MCP and skills work
    "genai / llm":   45,
    "ai engineer":   45,
    "mlops":         25,
    "ml engineer":   20,
    "ai consultant": 20,
    "ai research":   10,
}

# Skills from the CV. Each one a posting names adds PER_SKILL, up to
# SKILL_CAP, so a keyword-stuffed advert cannot buy its way to the top.
CV_SKILLS = {
    "swift", "swiftui", "ios", "uikit", "objc", "tca", "xcode", "fastlane",
    "accessibility", "kmp",
    "kotlin", "java", "spring", "microservices", "rest_api", "bff", "cache",
    "jvm_testing", "ios_testing", "wiremock", "appium",
    "kubernetes", "docker", "gcp", "gitops", "observability", "git", "cicd",
    "llm", "genai", "ai_agents", "ai_coding", "openai_api", "ai_eval",
}
PER_SKILL = 5
SKILL_CAP = 25

MOBILE_SKILLS = {"swift", "swiftui", "ios", "uikit", "objc", "tca",
                 "xcode", "fastlane", "kmp"}
BACKEND_SKILLS = {"kotlin", "java", "spring", "microservices", "rest_api",
                  "bff"}
# Mobile and backend in one posting is the "Mobile & Backend" variant.
BOTH_SIDES = 10

# A query that found the posting by a stack word in its full text
# ("Java developer" whose advert mentions Spring) earns this once.
TAG_BONUS = {"spring_text": 10, "kotlin_text": 10, "ios_text": 5}

SENIOR = 5

# Gaps from the CV plan.
DB_SKILLS = {"sql", "postgres", "mysql", "mssql", "oracle", "mongodb"}
SQL_HEAVY = -10            # two or more database skills named
ML_SKILLS = {"pytorch", "tensorflow", "keras", "sklearn", "xgboost", "jax",
             "mlflow", "kubeflow", "sagemaker", "azureml", "deeplearning",
             "cv", "nlp"}
ML_HEAVY = -10             # model-training stack the CV does not have
OTHER_STACK = {"python", "golang", "dotnet", "php", "nodejs", "flutter",
               "react_native", "android", "compose"}
OTHER_STACK_PENALTY = -5   # once, when another stack is named and none of yours
GERMAN_C1 = -15            # B2 on the CV
GERMAN_ADVERT = -5         # advert written in German: German-speaking team


def flags(skills, german_c1):
    sk = set(skills)
    out = []
    if german_c1:
        out.append("german_c1")
    if len(sk & DB_SKILLS) >= 2:
        out.append("sql_heavy")
    return out


def score(family, skills, seniority="mid", language="en",
          german_c1=False, tags=(), title=""):
    sk = set(skills)
    s = BASE.get(family, 0)

    s += min(SKILL_CAP, PER_SKILL * len(sk & CV_SKILLS))

    title_l = (title or "").lower()
    mobile_side = bool(sk & MOBILE_SKILLS) or family in (IOS, MOBILE)
    backend_side = (bool(sk & BACKEND_SKILLS) or family in (KOTLIN, JAVA)
                    or "backend" in title_l)
    if mobile_side and backend_side:
        s += BOTH_SIDES

    s += max([TAG_BONUS.get(t, 0) for t in tags] or [0])

    if seniority == "senior":
        s += SENIOR

    if len(sk & DB_SKILLS) >= 2:
        s += SQL_HEAVY
    if sk & ML_SKILLS:
        s += ML_HEAVY
    if (sk & OTHER_STACK) and not (sk & CV_SKILLS - {"git", "docker"}):
        s += OTHER_STACK_PENALTY
    if german_c1:
        s += GERMAN_C1
    if language == "de":
        s += GERMAN_ADVERT

    return max(0, min(100, s))


def label(family, s):
    if s >= STRONG:
        return "strong"
    if role_group(family) == "ai":
        return "ai"
    return "partial"
