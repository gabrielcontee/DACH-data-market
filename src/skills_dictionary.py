"""Skills the matcher looks for in a posting's title and snippet.

Each skill has a category and a list of regex aliases. The matcher tries
the longest alias first and blanks the span it matched, so `sql` cannot
re-match inside `postgresql` and `kotlin` cannot re-match inside
`kotlin multiplatform`.

The mobile, backend and testing blocks are the stack on the CV; fit.py
scores a posting by how many of those it names. The data and BI blocks
stay because they are how fit.py spots a database-heavy role.
"""

SKILLS = {
 # --- languages ----------------------------------------------------
 "sql":         {"cat": "language",   "aliases": [r"\bsql\b"]},
 "python":      {"cat": "language",   "aliases": [r"\bpython\b"]},
 "scala":       {"cat": "language",   "aliases": [r"\bscala\b"]},
 "java":        {"cat": "language",   "aliases": [r"\bjava\b(?!script)"]},
 "kotlin":      {"cat": "language",   "aliases": [r"\bkotlin\b"]},
 "swift":       {"cat": "language",   "aliases": [
                    # not the SWIFT banking network
                    r"\bswift\b(?![\s\-]*(ui|payments?|messag\w*|network|"
                    r"gpi|mt\d*|mx|code)\b)"]},
 "objc":        {"cat": "language",   "aliases": [r"\bobjective[\s\-]?c\b"]},
 "javascript":  {"cat": "language",   "aliases": [r"\bjavascript\b",
                                                 r"\btypescript\b"]},
 "php":         {"cat": "language",   "aliases": [r"\bphp\b"]},
 "golang":      {"cat": "language",   "aliases": [r"\bgolang\b"]},
 "dotnet":      {"cat": "language",   "aliases": [r"\basp\.net\b",
                                                 r"(?<![\w.])\.net\b",
                                                 r"\bc#(?!\w)"]},
 "r_lang":      {"cat": "language",   "aliases": [
                                                 r"(?<=[ ,/(])r(?=[ ,/)])"]},

 # --- mobile -------------------------------------------------------
 "ios":         {"cat": "mobile",     "aliases": [r"\bios\b(?![\s\-]?x[er]\b)",
                                                 r"\bipados\b",
                                                 r"\bwatchos\b"]},
 "swiftui":     {"cat": "mobile",     "aliases": [r"\bswift[\s\-]?ui\b"]},
 "uikit":       {"cat": "mobile",     "aliases": [r"\buikit\b"]},
 "tca":         {"cat": "mobile",     "aliases": [r"\bcomposable "
                                                 r"architecture\b"]},
 "xcode":       {"cat": "mobile",     "aliases": [r"\bxcode\b"]},
 "fastlane":    {"cat": "mobile",     "aliases": [r"\bfastlane\b"]},
 "android":     {"cat": "mobile",     "aliases": [r"\bandroid\b"]},
 "compose":     {"cat": "mobile",     "aliases": [r"\bjetpack compose\b"]},
 "kmp":         {"cat": "mobile",     "aliases": [r"\bkotlin multiplatform\b",
                                                 r"\bkmp\b", r"\bkmm\b"]},
 "flutter":     {"cat": "mobile",     "aliases": [r"\bflutter\b"]},
 "react_native": {"cat": "mobile",    "aliases": [r"\breact[\s\-]native\b"]},
 "accessibility": {"cat": "mobile",   "aliases": [r"\baccessibility\b",
                                                 r"\bbarrierefrei\w*\b",
                                                 r"\bvoiceover\b",
                                                 r"\bwcag\b"]},

 # --- backend ------------------------------------------------------
 "spring":      {"cat": "backend",    "aliases": [r"\bspring[\s\-]?boot\b",
                                                 r"\bspring (framework|cloud|"
                                                 r"security|webflux|data|mvc)\b",
                                                 r"\bwebflux\b"]},
 "microservices": {"cat": "backend",  "aliases": [r"\bmicro[\s\-]?services?\b",
                                                 r"\bmicroservice\w*\b"]},
 "rest_api":    {"cat": "backend",    "aliases": [r"\brest(ful)?[\s\-]?"
                                                 r"(apis?|services?|"
                                                 r"schnittstellen?)\b",
                                                 r"\bopenapi\b",
                                                 r"\bswagger\b"]},
 "graphql":     {"cat": "backend",    "aliases": [r"\bgraphql\b"]},
 "grpc":        {"cat": "backend",    "aliases": [r"\bgrpc\b"]},
 "bff":         {"cat": "backend",    "aliases": [r"\bbackend[\s\-]for[\s\-]"
                                                 r"frontends?\b",
                                                 r"\bbff\b"]},
 "cache":       {"cat": "backend",    "aliases": [r"\bredis\b",
                                                 r"\bhazelcast\b"]},
 "nodejs":      {"cat": "backend",    "aliases": [r"\bnode\.?js\b"]},

 # --- testing ------------------------------------------------------
 "jvm_testing": {"cat": "testing",    "aliases": [r"\bjunit\b", r"\bmockk\b",
                                                 r"\bkotest\b"]},
 "ios_testing": {"cat": "testing",    "aliases": [r"\bxctest\b",
                                                 r"\bxcuitest\b",
                                                 r"\bswift testing\b"]},
 "wiremock":    {"cat": "testing",    "aliases": [r"\bwiremock\b"]},
 "appium":      {"cat": "testing",    "aliases": [r"\bappium\b",
                                                 r"\bbrowserstack\b"]},

 # --- processing and data -----------------------------------------
 "spark":       {"cat": "processing", "aliases": [r"\bapache spark\b",
                                                 r"\bpyspark\b",
                                                 r"\bspark\b"]},
 "hadoop":      {"cat": "legacy",     "aliases": [r"\bhadoop\b",
                                                 r"\bhdfs\b",
                                                 r"\bmapreduce\b",
                                                 r"\bhive\b"]},
 "kafka":       {"cat": "streaming",  "aliases": [r"\bkafka\b"]},
 "flink":       {"cat": "streaming",  "aliases": [r"\bflink\b"]},
 "databricks":  {"cat": "platform",   "aliases": [r"\bdatabricks\b"]},
 "snowflake":   {"cat": "warehouse",  "aliases": [r"\bsnowflake\b"]},
 "bigquery":    {"cat": "warehouse",  "aliases": [r"\bbigquery\b"]},
 "redshift":    {"cat": "warehouse",  "aliases": [r"\bredshift\b"]},
 "synapse":     {"cat": "warehouse",  "aliases": [r"\bsynapse\b"]},
 "airflow":     {"cat": "orchestr",   "aliases": [r"\bapache airflow\b",
                                                 r"\bairflow\b"]},
 "dbt":         {"cat": "transform",  "aliases": [r"\bdbt\b"]},
 "ssis":        {"cat": "legacy",     "aliases": [r"\bssis\b"]},
 "talend":      {"cat": "legacy",     "aliases": [r"\btalend\b"]},

 # --- databases ----------------------------------------------------
 "postgres":    {"cat": "database",   "aliases": [r"\bpostgresql\b",
                                                 r"\bpostgres\b"]},
 "mysql":       {"cat": "database",   "aliases": [r"\bmysql\b"]},
 "mssql":       {"cat": "database",   "aliases": [r"\bsql server\b",
                                                 r"\bt-sql\b",
                                                 r"\bms sql\b"]},
 "oracle":      {"cat": "database",   "aliases": [r"\boracle\b"]},
 "mongodb":     {"cat": "database",   "aliases": [r"\bmongodb\b",
                                                 r"\bmongo\b"]},
 "elastic":     {"cat": "database",   "aliases": [r"\belasticsearch\b"]},

 # --- cloud and operations ----------------------------------------
 "aws":         {"cat": "cloud",      "aliases": [r"\baws\b",
                                                 r"\bamazon web services\b"]},
 "azure":       {"cat": "cloud",      "aliases": [r"\bazure\b",
                                                 r"\bdata factory\b"]},
 "gcp":         {"cat": "cloud",      "aliases": [r"\bgcp\b",
                                                 r"\bgoogle cloud\b"]},
 "docker":      {"cat": "devops",     "aliases": [r"\bdocker\b"]},
 "kubernetes":  {"cat": "devops",     "aliases": [r"\bkubernetes\b",
                                                 r"\bk8s\b",
                                                 r"\bopenshift\b"]},
 "gitops":      {"cat": "devops",     "aliases": [r"\bgitops\b",
                                                 r"\bargo ?cd\b",
                                                 r"\bkustomize\b",
                                                 r"\bhelm\b"]},
 "observability": {"cat": "devops",   "aliases": [r"\bprometheus\b",
                                                 r"\bgrafana\b",
                                                 r"\bopentelemetry\b",
                                                 r"\bobservability\b"]},
 "terraform":   {"cat": "devops",     "aliases": [r"\bterraform\b"]},
 "git":         {"cat": "devops",     "aliases": [r"\bgithub\b",
                                                 r"\bgitlab\b",
                                                 r"\bgit\b"]},
 "cicd":        {"cat": "devops",     "aliases": [r"\bci/cd\b",
                                                 r"\bjenkins\b"]},

 # --- BI -----------------------------------------------------------
 "powerbi":     {"cat": "bi",         "aliases": [r"\bpower ?bi\b"]},
 "tableau":     {"cat": "bi",         "aliases": [r"\btableau\b"]},
 "looker":      {"cat": "bi",         "aliases": [r"\blooker\b"]},
 "qlik":        {"cat": "bi",         "aliases": [r"\bqlik\b"]},
 "excel":       {"cat": "bi",         "aliases": [r"\bexcel\b"]},

 # --- ML frameworks: how a model gets trained ---------------------
 "pytorch":     {"cat": "ml_framework", "aliases": [r"\bpytorch\b"]},
 "tensorflow":  {"cat": "ml_framework", "aliases": [r"\btensorflow\b"]},
 "keras":       {"cat": "ml_framework", "aliases": [r"\bkeras\b"]},
 "sklearn":     {"cat": "ml_framework", "aliases": [r"\bscikit-?learn\b",
                                                   r"\bsklearn\b"]},
 "xgboost":     {"cat": "ml_framework", "aliases": [r"\bxgboost\b",
                                                   r"\blightgbm\b",
                                                   r"\bcatboost\b"]},
 "jax":         {"cat": "ml_framework", "aliases": [r"\bjax\b"]},

 # --- MLOps: how a model reaches production -----------------------
 "mlflow":      {"cat": "mlops",      "aliases": [r"\bmlflow\b"]},
 "kubeflow":    {"cat": "mlops",      "aliases": [r"\bkubeflow\b"]},
 "sagemaker":   {"cat": "mlops",      "aliases": [r"\bsagemaker\b",
                                                 r"\bsage maker\b"]},
 "vertexai":    {"cat": "mlops",      "aliases": [r"\bvertex ai\b",
                                                 r"\bvertex\b"]},
 "azureml":     {"cat": "mlops",      "aliases": [r"\bazure ml\b",
                                                 r"\bazure machine "
                                                 r"learning\b",
                                                 r"\bazure ai foundry\b"]},

 # --- Generative AI -----------------------------------------------
 "llm":         {"cat": "genai",      "aliases": [r"\bllms?\b",
                                                 r"\blarge language "
                                                 r"models?\b",
                                                 r"\bsprachmodell\w*\b",
                                                 r"\bfoundation models?\b"]},
 "genai":       {"cat": "genai",      "aliases": [r"\bgenai\b",
                                                 r"\bgen[\s\-]?ai\b",
                                                 r"\bgenerative ai\b",
                                                 r"\bgenerative ki\b"]},
 "rag":         {"cat": "genai",      "aliases": [r"\bretrieval[\s\-]"
                                                 r"augmented\w*\b",
                                                 r"\brag\b"]},
 "ai_agents":   {"cat": "genai",      "aliases": [r"\bagentic\b",
                                                 r"\bai agents?\b",
                                                 r"\bki[\s\-]agenten?\b",
                                                 r"\bmulti[\s\-]agent\b",
                                                 r"\bmcp\b",
                                                 r"\bmodel context "
                                                 r"protocol\b"]},
 "ai_coding":   {"cat": "genai",      "aliases": [r"\bgithub copilot\b",
                                                 r"\bclaude code\b",
                                                 r"\bai[\s\-]assisted "
                                                 r"(coding|development|"
                                                 r"engineering)\b",
                                                 r"\bai coding\b"]},
 "prompting":   {"cat": "genai",      "aliases": [r"\bprompt[\s\-]?"
                                                 r"engineer\w*\b",
                                                 r"\bprompting\b"]},
 "langchain":   {"cat": "genai",      "aliases": [r"\blangchain\b",
                                                 r"\blanggraph\b",
                                                 r"\bllama[\s\-]?index\b",
                                                 r"\bsemantic kernel\b",
                                                 r"\bspring ai\b"]},
 "openai_api":  {"cat": "genai",      "aliases": [r"\bopenai\b",
                                                 r"\bgpt-?[45]\b",
                                                 r"\banthropic\b",
                                                 # not bare "Claude": it is
                                                 # a first name in Swiss
                                                 # postings
                                                 r"\bclaude (api|sonnet|"
                                                 r"opus)\b",
                                                 r"\bazure openai\b",
                                                 r"\bmistral\b",
                                                 r"\bgemini\b"]},
 "vectordb":    {"cat": "genai",      "aliases": [r"\bvector (db|"
                                                 r"database|store)\b",
                                                 r"\bpinecone\b",
                                                 r"\bweaviate\b",
                                                 r"\bqdrant\b",
                                                 r"\bpgvector\b"]},
 "ai_eval":     {"cat": "genai",      "aliases": [r"\bllm[\s\-]?as[\s\-]?"
                                                 r"a[\s\-]?judge\b",
                                                 r"\bguardrails?\b",
                                                 r"\bevals?\b",
                                                 r"\bai safety\b"]},

 # --- NLP and computer vision -------------------------------------
 "nlp":         {"cat": "nlp_cv",     "aliases": [r"\bnlp\b",
                                                 r"\bnatural language "
                                                 r"processing\b"]},
 "cv":          {"cat": "nlp_cv",     "aliases": [r"\bcomputer vision\b",
                                                 r"\bbildverarbeitung\b",
                                                 r"\bopencv\b"]},
 "deeplearning": {"cat": "nlp_cv",    "aliases": [r"\bdeep learning\b",
                                                 r"\bneural network\w*\b",
                                                 r"\bneuronale netze\b"]},

 # --- practice -----------------------------------------------------
 "sap":         {"cat": "enterprise", "aliases": [r"\bsap\b"]},
 "etl":         {"cat": "practice",   "aliases": [r"\betl\b", r"\belt\b"]},
 "datawarehouse": {"cat": "practice", "aliases": [
                    r"\bdata warehouse\b", r"\bdwh\b",
                    r"\bdata lakehouse\b", r"\bdata lake\b"]},
}


CATEGORY = {k: v["cat"] for k, v in SKILLS.items()}
