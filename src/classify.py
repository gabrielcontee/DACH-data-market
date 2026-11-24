"""Title rules: which role family a posting belongs to, and the flags
read off its title and snippet (seniority, work mode, language, German
level, agency).

Families are decided from the title, because the aggregator cuts the
description to about 500 characters of mostly company intro. The one
exception is the query tags: a generic "Backend Engineer" that came back
from a search for Kotlin or Spring names that stack somewhere in its
full text, so it counts as a Kotlin / Spring role.

The order of the checks is the classifier. Excludes come first, then
your stack, then data (excluded), then the AI families, most specific
first. A title that matches nothing is "other" and is dropped.
"""

import re

# ---- families --------------------------------------------------------

IOS = "ios engineer"
KOTLIN = "kotlin / spring backend"
JAVA = "java backend"
MOBILE = "mobile engineer"

STACK_FAMILIES = [IOS, KOTLIN, JAVA, MOBILE]
AI_FAMILIES = ["ai engineer", "genai / llm", "ml engineer", "mlops",
               "ai consultant", "ai research"]
KEEP = STACK_FAMILIES + AI_FAMILIES


def role_group(family):
    if family in STACK_FAMILIES:
        return "stack"
    if family in AI_FAMILIES:
        return "ai"
    return "excluded"


# ---- normalisation ---------------------------------------------------

def fold(s):
    s = (s or "").lower().strip()
    for a, b in [("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")]:
        s = s.replace(a, b)
    return s


# ---- excludes that beat every positive rule --------------------------

INVALID = (r"^initiativbewerbung|initiativbewerbung|talentpool|"
           r"^deine aufgaben|^\"+title|^zum \d|^wachstum durch")

ENTRY = (r"\bausbildung\b|duales? studium|dualer bachelor|"
         r"\bwerkstudent|werkstudierend|\bpraktikum\b|\bpraktikant|"
         r"\bintern\b|\binternship\b|"
         r"\btrainee\b|traineeprogramm|bachelor thesis|"
         r"master student|studienkolleg|bachelor of science|"
         r"\bdhbw\b|\bhwr\b|b\.\s?a\.\s+in\b|"
         r"^b\.\s?a\.|abschlussarbeit|\blehrling\b|\blehre\b")

DATACENTRE = r"data\s*cent(er|re)|rechenzentrum|\bdceo\b"

FINANCE = (r"controlling|\bcontroller\b|finanzen|buchhalt|"
           r"\bfp&a\b|financial planning|finance transformation|"
           r"finance\s*&\s*accounting|finance business partner|"
           r"kaufmaennisch|vertriebscontrolling|"
           r"finance-consulting|finance solutions|"
           r"transaction advisory")

# Jobs that sit next to engineering but are not it. Checked only for
# your-stack families: "AI Product Manager" stays an AI consulting role,
# "Product Owner iOS App" is not an iOS engineering job.
NON_ENG = (r"\b(sales|vertrieb\w*|account manager|key account|"
           r"recruit\w*|talent acquisition|marketing|"
           r"product owner|product manager|produktmanager|"
           r"project manager|projektmanager|projektleiter|"
           r"scrum master|agile coach|"
           r"designer|"
           r"support|service desk|helpdesk|"
           r"tester|testmanager|test engineer|qa engineer|qa analyst|"
           r"quality assurance|testautomatisierer)\b")

# ---- your stack ------------------------------------------------------

DEV = (r"\b(developer|engineer|entwickler\w*|programmierer\w*|"
       r"architect|architekt\w*|lead|head|software|"
       r"engineering|ingenieur)\b|entwickler")

# Flutter, React Native and friends: the CV leaves them off, so a title
# that leads with one is out even when it also says iOS.
CROSS_PLATFORM = (r"\bflutter\b|react[\s\-]native|\bxamarin\b|\bmaui\b|"
                  r"\bionic\b|\bcordova\b|\bunity\b")
KMP = r"kotlin multiplatform|\bkmp\b|\bkmm\b"

R_IOS = (r"\b(ios|ipados|watchos|visionos|tvos|iphone|ipad)\b"
         r"(?![\s\-]?x[er]\b)")
R_SWIFT = r"\bswift(\s?ui)?\b(?![\s\-]*(payments?|messag\w*|network|gpi))"
CISCO = r"\bcisco\b|netzwerk|network engineer|\bios[\s\-]?x[er]\b"

R_ANDROID = r"\bandroid\b"
R_KOTLIN_SPRING = r"\bkotlin\b|\bspring\b|\bwebflux\b"
R_JAVA = r"\bjava\b(?![\s\-]?script)|\bjvm\b|\bjakarta ee\b"
R_MOBILE = (r"\bmobile\b|\bmobil[\s\-]|\bapp[\s\-]?(entwickl\w*|developer|"
            r"engineer)|\bapps?\b")
# "SAP Fiori App Developer" and "Power Apps" are not mobile apps
NOT_MOBILE_APP = (r"\bsap\b|\bfiori\b|power ?apps?|salesforce|servicenow|"
                  r"\bweb[\s\-]?apps?\b|\bmendix\b|\boutsystems\b")
R_GENERIC_SWE = (r"\bbackend\b|\bback[\s\-]end\b|\bsoftware\b|"
                 r"softwareentwickl|softwareengineer|"
                 r"\bfull[\s\-]?stack\b|\bplatform engineer\b|"
                 r"\bapi\b|\bintegration\b")

# ---- data roles: dropped, but still classified so they do not land in
# an AI family ("Data Engineer AI Platform" is a data job) -------------

R_DATA = (r"data\s+[\w\s\-&/]*architect|datenarchitekt|"
          r"analytics engineer|data engineer|dateningenieur|\bbig data\b|"
          r"data platform|data scraping|data processing|"
          r"data\s+(migration|integration|pipeline)|"
          r"datenbankadministrator|database administrator|\bdba\b|"
          r"data warehouse|\bdwh\b|\betl\b|\bdbt\b|sap bw|datasphere|"
          r"data.?lake|data vault|data modeler|data mesh|"
          r"data governance|data quality|data privacy|master data|"
          r"data steward|data management|data strategy|data protection|"
          r"data scientist|data science|"
          r"data analyst|datenanalyst|\bbi analyst|"
          r"data\s*&\s*ai|data and ai|data\s*&\s*analytics|data analytics|"
          r"data consultant|\bdata expert\b|data insights|"
          r"\bbi\b|business intelligence|power ?bi|\btableau\b|"
          r"\bqlik\b|reporting analyst")

# ---- AI families, unchanged from the original tracker ----------------

R_GENAI = (r"\bgenai\b|\bgen[\s\-]?ai\b|generative ai|generative ki|"
           r"\bllms?\b|\bllmops\b|large language model|"
           r"sprachmodell|foundation model|grundlagenmodell|"
           r"\brag\b|retrieval[\s\-]augmented|"
           r"prompt[\s\-]?engineer|agentic|\bai agent|\bki[\s\-]agent|"
           r"conversational ai|chatbot engineer|"
           r"\bai[\s\-]native|copilot engineer")

R_MLOPS = (r"\bmlops\b|\bml[\s\-]?ops\b|\bmodel ops\b|"
           r"ml[\s\-](platform|infrastructure|infra|engineer[\s\-]platform)|"
           r"machine learning (platform|infrastructure|infra|operations)|"
           r"model (serving|deployment|monitoring)|"
           r"\bai (platform|infrastructure|infra)\b|"
           r"\bki[\s\-]plattform\b|feature store")

R_ML = (r"mas?chine\s*learning|\bml[\s\-]?engineer|\bml[\s\-]?ingenieur|"
        r"maschinelles lernen|deep learning|\bdl engineer\b|"
        r"reinforcement learning|bestaerkendes lernen|"
        r"computer vision|bildverarbeitung|bilderkennung|"
        r"\bnlp\b|natural language processing|"
        r"sprachverarbeitung|speech recognition|spracherkennung|"
        r"\bai/ml\b|\bai\s*&\s*ml\b|recommender|"
        r"predictive model|forecasting engineer")

R_AI_RESEARCH = (r"applied scientist|research scientist|"
                 r"research engineer|forschungsingenieur|"
                 r"\bai research|\bki[\s\-]forsch|"
                 r"machine learning (researcher|scientist)|"
                 r"\bphd\b.*\b(ai|ml)\b")

R_AI_CONSULT = (r"\bai\s+(consultant|consulting|architect|advisor|"
                r"strategy|strateg|transformation|solution|"
                r"presales|sales engineer|product manager|"
                r"product owner|governance|ethics|compliance)|"
                r"\bki[\s\-]?(berater|architekt|strategie|"
                r"transformation)|"
                r"artificial intelligence (consultant|architect|"
                r"strategy|advisor)|"
                r"(consultant|architect|berater)\s+(fuer\s+)?"
                r"(ai|ki|artificial intelligence)\b")

R_AI_ENGINEER = (r"\bai\s*[\-/]?\s*(engineer|developer|entwickler|"
                 r"specialist|spezialist|expert)|"
                 r"\bki\s*[\-/]?\s*(engineer|developer|entwickler|"
                 r"spezialist|experte)|"
                 r"artificial intelligence engineer|"
                 r"\bai software engineer\b")

R_AI_OTHER = (r"\bai\b|\bki\b|artificial intelligence|"
              r"kuenstliche intelligenz")


def _has(rx, s):
    return re.search(rx, s) is not None


def classify(title, tags=()):
    """Role family for a title. `tags` are the query tags the posting
    was found under (see adzuna.QUERIES), e.g. {"kotlin_text"}."""
    t = fold(title)
    tags = set(tags or ())

    if _has(INVALID, t):
        return "invalid"
    if _has(ENTRY, t):
        return "entry programme"
    if _has(DATACENTRE, t):
        return "data centre"
    if _has(FINANCE, t):
        return "finance"

    eng = _has(DEV, t) and not _has(NON_ENG, t)

    if eng:
        if _has(CROSS_PLATFORM, t):
            return "cross-platform mobile"
        if _has(KMP, t):
            return MOBILE
        if (_has(R_IOS, t) or _has(R_SWIFT, t)) and not _has(CISCO, t):
            return IOS
        if _has(R_ANDROID, t):
            return "android"
        if _has(R_KOTLIN_SPRING, t):
            return KOTLIN
        data = _has(R_DATA, t)
        if _has(R_JAVA, t) and not data:
            return JAVA
        if _has(R_MOBILE, t) and not data and not _has(NOT_MOBILE_APP, t):
            return MOBILE
        if _has(R_GENERIC_SWE, t) and not data:
            if tags & {"kotlin_text", "spring_text"}:
                return KOTLIN
            if "ios_text" in tags:
                return MOBILE

    if _has(R_DATA, t):
        return "data"

    if _has(R_AI_RESEARCH, t):
        return "ai research"
    if _has(R_GENAI, t):
        return "genai / llm"
    if _has(R_MLOPS, t):
        return "mlops"
    if _has(R_ML, t):
        return "ml engineer"
    if _has(R_AI_CONSULT, t):
        return "ai consultant"
    if _has(R_AI_ENGINEER, t):
        return "ai engineer"
    if _has(R_AI_OTHER, t):
        return "ai (other)"
    return "other"


# ---- flags -----------------------------------------------------------

SENIOR = (r"\b(senior|sr\.?|lead|principal|head|director|"
          r"staff|chief|vp)\b")
JUNIOR = (r"\b(junior|jr\.?|entry|graduate|absolvent\w*|"
          r"einsteiger\w*|berufseinsteiger\w*|associate)\b")


def seniority(title):
    t = fold(title)
    if _has(SENIOR, t):
        return "senior"
    if _has(JUNIOR, t):
        return "junior"
    return "mid"


AGENCY = (r"(consulting|personal|recruit|staffing|hays|"
          r"randstad|michael page|robert half|experis|"
          r"gulp|solcom|amoria|darwin|huzzle|talent)")


def is_agency(company):
    return _has(AGENCY, fold(company))


GERMAN_WORDS = (r"\b(und|der|die|das|mit|für|fuer|kenntnisse|erfahrung|"
                r"wir suchen|deine|ihre)\b")


def language(description):
    return "de" if _has(GERMAN_WORDS, (description or "").lower()) else "en"


REMOTE = (r"\bremote\b|home[\s\-]?office|\bhomeoffice\b|"
          r"work from (home|anywhere)|\bwfh\b|ortsunabhaengig|"
          r"mobiles arbeiten|mobile working|telearbeit|"
          r"\b100\s*%\s*(remote|home)")
HYBRID = r"\bhybrid\w*\b"


def work_mode(title, description):
    """'remote', 'hybrid' or '' when the snippet says neither. Hybrid
    wins when both appear: "hybrid or remote" still has an office."""
    t = fold(f"{title} {description}")
    if _has(HYBRID, t):
        return "hybrid"
    if _has(REMOTE, t):
        return "remote"
    return ""


# German at C1 or above, as postings tend to phrase it. Only the first
# ~500 characters are visible, so this flags what it can see.
GERMAN_C1 = (r"(deutsch|german)\w*[^.;\n]{0,40}\b(c1|c2)\b|"
             r"\b(c1|c2)\b[^.;\n]{0,30}(deutsch|german)|"
             r"verhandlungssicher\w*[^.;\n]{0,20}deutsch|"
             r"deutsch\w*[^.;\n]{0,25}verhandlungssicher|"
             # fold() has already turned "ß" into "ss"
             r"fliessend\w*[^.;\n]{0,15}deutsch|"
             r"deutsch\w*[^.;\n]{0,25}(fliessend|muttersprach\w*)|"
             r"sehr gute deutschkenntnisse|"
             r"(fluent|native|business[\s\-]fluent)[^.;\n]{0,25}german|"
             r"german[^.;\n]{0,25}(fluent|native|mother tongue)")


def german_c1(title, description):
    return _has(GERMAN_C1, fold(f"{title} {description}"))
