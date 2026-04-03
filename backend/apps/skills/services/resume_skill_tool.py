"""
Resume & text skill extraction: spaCy phrase matcher + Groq LLM.

This module is the **single source of truth** for skill extraction across the
project. It is used for:
- Uploaded resume/document skills
- User skills (manual skills, jobs ingestion, role seeding)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Set

from groq import Groq

from django.conf import settings


# ---------------------------------------------------------------------------
# PUBLIC HELPERS (used by views, jobs, roles)
# ---------------------------------------------------------------------------
_SKILL_NORMALIZATION_MAP = {
    # ── Programming Languages ──────────────────────────────────────
    "python": "Python",          "python3": "Python",           "python 3": "Python",
    "java": "Java",
    "javascript": "JavaScript",  "js": "JavaScript",
    "typescript": "TypeScript",  "ts": "TypeScript",
    "c++": "C++",                "cpp": "C++",                  "c plus plus": "C++",
    "c#": "C#",                  "csharp": "C#",                "c sharp": "C#",
    "c": "C",
    "go": "Go",                  "golang": "Go",
    "rust": "Rust",
    "php": "PHP",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "ruby": "Ruby",
    "scala": "Scala",
    "r": "R",
    "matlab": "MATLAB",
    "perl": "Perl",
    "shell": "Shell Scripting",  "shell scripting": "Shell Scripting",
    "bash": "Bash",              "bash scripting": "Bash",
    "powershell": "PowerShell",
    "groovy": "Groovy",
    "dart": "Dart",
    "elixir": "Elixir",
    "haskell": "Haskell",
    "lua": "Lua",
    "assembly": "Assembly",
    "vba": "VBA",
    "cobol": "COBOL",
    "fortran": "Fortran",
 
    # ── Web Frameworks & Libraries ─────────────────────────────────
    "react": "React",            "react.js": "React",           "reactjs": "React",        "react js": "React",
    "next.js": "Next.js",        "nextjs": "Next.js",           "next js": "Next.js",
    "vue": "Vue.js",             "vue.js": "Vue.js",            "vuejs": "Vue.js",          "vue js": "Vue.js",
    "angular": "Angular",        "angularjs": "AngularJS",      "angular.js": "AngularJS",
    "svelte": "Svelte",
    "ember": "Ember.js",         "ember.js": "Ember.js",
    "backbone": "Backbone.js",   "backbone.js": "Backbone.js",
    "jquery": "jQuery",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",        "fast api": "FastAPI",
    "express": "Express.js",     "express.js": "Express.js",    "expressjs": "Express.js",
    "node": "Node.js",           "node.js": "Node.js",          "nodejs": "Node.js",        "node js": "Node.js",
    "spring": "Spring",          "spring boot": "Spring Boot",  "springboot": "Spring Boot",
    "laravel": "Laravel",
    "rails": "Ruby on Rails",    "ruby on rails": "Ruby on Rails", "ror": "Ruby on Rails",
    "asp.net": "ASP.NET",        "asp net": "ASP.NET",
    ".net": ".NET",              "dotnet": ".NET",              "dot net": ".NET",          ".net core": ".NET",  "dotnet core": ".NET",
    "blazor": "Blazor",
    "nest": "NestJS",            "nestjs": "NestJS",            "nest.js": "NestJS",
    "nuxt": "Nuxt.js",           "nuxt.js": "Nuxt.js",
    "gatsby": "Gatsby",
    "remix": "Remix",
    "htmx": "HTMX",
    "fastify": "Fastify",
    "koa": "Koa.js",
    "hapi": "Hapi.js",
    "strapi": "Strapi",
 
    # ── Frontend / UI ──────────────────────────────────────────────
    "html": "HTML",              "html5": "HTML",
    "css": "CSS",                "css3": "CSS",                 "less": "CSS",
    "sass": "SASS",              "scss": "SASS",
    "tailwind": "Tailwind",      "tailwind css": "Tailwind",    "tailwindcss": "Tailwind",
    "bootstrap": "Bootstrap",
    "material ui": "Material UI","materialui": "Material UI",   "mui": "Material UI",
    "chakra ui": "Chakra UI",
    "shadcn": "shadcn/ui",       "shadcn/ui": "shadcn/ui",
    "ant design": "Ant Design",  "antd": "Ant Design",
    "styled components": "Styled Components",
    "emotion": "CSS-in-JS",
    "webpack": "Webpack",
    "vite": "Vite",
    "rollup": "Rollup",
    "babel": "Babel",
    "eslint": "ESLint",
    "prettier": "Prettier",
    "storybook": "Storybook",
    "figma": "Figma",
    "adobe xd": "Adobe XD",
    "sketch": "Sketch",
    "ui": "UI Design",           "ux": "UX Design",             "ui/ux": "UI/UX Design",    "ui ux": "UI/UX Design",
    "responsive design": "Responsive Design",
    "web design": "Web Design",
    "accessibility": "Accessibility", "wcag": "Accessibility",   "aria": "Accessibility",
 
    # ── Databases ──────────────────────────────────────────────────
    "postgresql": "PostgreSQL",  "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "sqlite": "SQLite",          "sqlite3": "SQLite",
    "mongodb": "MongoDB",        "mongo": "MongoDB",            "mongo db": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch", "elastic search": "Elasticsearch",
    "cassandra": "Cassandra",
    "dynamodb": "DynamoDB",      "dynamo db": "DynamoDB",
    "firestore": "Firestore",
    "firebase": "Firebase",
    "supabase": "Supabase",
    "neo4j": "Neo4j",
    "couchdb": "CouchDB",
    "mariadb": "MariaDB",
    "oracle": "Oracle DB",       "oracle db": "Oracle DB",
    "mssql": "SQL Server",       "sql server": "SQL Server",    "ms sql": "SQL Server",     "microsoft sql server": "SQL Server",
    "cockroachdb": "CockroachDB",
    "planetscale": "PlanetScale",
    "influxdb": "InfluxDB",
    "timescaledb": "TimescaleDB",
    "sql": "SQL",
    "nosql": "NoSQL",            "no sql": "NoSQL",
    "database": "Databases",     "databases": "Databases",      "db": "Databases",
    "orm": "ORM",
    "prisma": "Prisma",
    "sequelize": "Sequelize",
    "mongoose": "Mongoose",
    "sqlalchemy": "SQLAlchemy",
    "hibernate": "Hibernate",
 
    # ── Cloud & DevOps ─────────────────────────────────────────────
    "aws": "AWS",                "amazon web services": "AWS",  "amazon aws": "AWS",
    "azure": "Azure",            "microsoft azure": "Azure",
    "gcp": "GCP",                "google cloud": "GCP",         "google cloud platform": "GCP",
    "digitalocean": "DigitalOcean",
    "heroku": "Heroku",
    "vercel": "Vercel",
    "netlify": "Netlify",
    "cloudflare": "Cloudflare",
    "docker": "Docker",
    "kubernetes": "Kubernetes",  "k8s": "Kubernetes",
    "helm": "Helm",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "puppet": "Puppet",
    "chef": "Chef",
    "jenkins": "Jenkins",
    "github actions": "GitHub Actions",
    "gitlab ci": "GitLab CI",    "gitlab ci/cd": "GitLab CI",
    "circle ci": "CircleCI",     "circleci": "CircleCI",
    "travis ci": "Travis CI",    "travisci": "Travis CI",
    "ci/cd": "CI/CD",            "ci cd": "CI/CD",              "continuous integration": "CI/CD",
    "continuous deployment": "CI/CD", "continuous delivery": "CI/CD",
    "devops": "DevOps",          "dev ops": "DevOps",
    "sre": "SRE",                "site reliability": "SRE",
    "infrastructure as code": "Infrastructure as Code", "iac": "Infrastructure as Code",
    "linux": "Linux",            "ubuntu": "Linux",             "centos": "Linux",          "debian": "Linux",  "unix": "Linux",
    "networking": "Networking",  "tcp/ip": "Networking",        "dns": "Networking",
    "nginx": "Nginx",
    "apache": "Apache",
    "load balancing": "Load Balancing",
    "monitoring": "Monitoring",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "datadog": "Datadog",
    "new relic": "New Relic",
    "elk": "ELK Stack",          "elk stack": "ELK Stack",      "elasticsearch logstash kibana": "ELK Stack",
    "logstash": "Logstash",
    "kibana": "Kibana",
    "splunk": "Splunk",
    "cloudwatch": "AWS CloudWatch", "aws cloudwatch": "AWS CloudWatch",
    "lambda": "AWS Lambda",      "aws lambda": "AWS Lambda",
    "serverless": "Serverless",
    "microservices": "Microservices", "micro services": "Microservices",
    "service mesh": "Service Mesh",
    "istio": "Istio",
    "kafka": "Kafka",            "apache kafka": "Kafka",
    "rabbitmq": "RabbitMQ",      "rabbit mq": "RabbitMQ",
    "celery": "Celery",
    "message queue": "Message Queue",
    "pubsub": "Pub/Sub",         "pub/sub": "Pub/Sub",
 
    # ── Version Control ────────────────────────────────────────────
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",
    "svn": "SVN",
    "mercurial": "Mercurial",
    "version control": "Git",
 
    # ── APIs & Integration ─────────────────────────────────────────
    "rest api": "REST API",      "rest apis": "REST API",       "restful api": "REST API",
    "restful apis": "REST API",  "restful": "REST API",         "rest": "REST API",
    "api": "API Development",    "api development": "API Development",
    "api design": "API Design",  "api integration": "API Integration",
    "graphql": "GraphQL",
    "grpc": "gRPC",
    "soap": "SOAP",
    "webhook": "Webhooks",       "webhooks": "Webhooks",
    "websocket": "WebSockets",   "websockets": "WebSockets",
    "oauth": "OAuth",            "oauth2": "OAuth",
    "jwt": "JWT",                "json web token": "JWT",
    "openapi": "OpenAPI",
    "swagger": "Swagger",
 
    # ── Machine Learning & AI ──────────────────────────────────────
    "machine learning": "Machine Learning", "ml": "Machine Learning",
    "deep learning": "Deep Learning",       "dl": "Deep Learning",
    "artificial intelligence": "AI",        "ai": "AI",           "ai/ml": "Machine Learning",
    "tensorflow": "TensorFlow",             "tf": "TensorFlow",
    "pytorch": "PyTorch",                   "torch": "PyTorch",
    "keras": "Keras",
    "scikit-learn": "scikit-learn",         "scikit learn": "scikit-learn", "sklearn": "scikit-learn",
    "hugging face": "Hugging Face",         "huggingface": "Hugging Face",
    "transformers": "Transformers",
    "llm": "LLM",                           "large language model": "LLM",  "llms": "LLM",
    "langchain": "LangChain",               "lang chain": "LangChain",
    "openai": "OpenAI",                     "open ai": "OpenAI",
    "gpt": "GPT",                           "chatgpt": "GPT",
    "nlp": "NLP",                           "natural language processing": "NLP",
    "computer vision": "Computer Vision",   "cv": "Computer Vision",
    "object detection": "Computer Vision",  "image recognition": "Computer Vision",
    "neural network": "Neural Networks",    "neural networks": "Neural Networks",
    "cnn": "Neural Networks",               "rnn": "Neural Networks",       "lstm": "Neural Networks",
    "gan": "GANs",
    "reinforcement learning": "Reinforcement Learning", "rl": "Reinforcement Learning",
    "mlops": "MLOps",                       "ml ops": "MLOps",
    "feature engineering": "Feature Engineering",
    "model deployment": "Model Deployment",
    "model training": "Machine Learning",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
    "random forest": "Machine Learning",
    "faiss": "FAISS",
 
    # ── Data Science & Analytics ───────────────────────────────────
    "data science": "Data Science",
    "data analysis": "Data Analysis",       "data analytics": "Data Analysis",
    "data engineering": "Data Engineering",
    "data visualization": "Data Visualization", "data viz": "Data Visualization",
    "pandas": "Pandas",
    "numpy": "NumPy",                        "np": "NumPy",
    "matplotlib": "matplotlib",              "seaborn": "matplotlib",
    "plotly": "Plotly",
    "tableau": "Tableau",
    "power bi": "Power BI",                  "powerbi": "Power BI",
    "looker": "Looker",
    "metabase": "Metabase",
    "jupyter": "Jupyter Notebook",           "jupyter notebook": "Jupyter Notebook",
    "jupyter lab": "Jupyter Notebook",       "jupyterlab": "Jupyter Notebook",
    "statistics": "Statistics",              "statistical analysis": "Statistics",  "statistical modeling": "Statistics",
    "excel": "Excel",                        "ms excel": "Excel",            "microsoft excel": "Excel",
    "google sheets": "Google Sheets",        "spreadsheets": "Excel",
    "etl": "ETL",
    "data pipeline": "Data Pipelines",       "data pipelines": "Data Pipelines",
    "data warehouse": "Data Warehousing",    "data warehousing": "Data Warehousing",
    "data lake": "Data Lakes",               "data lakes": "Data Lakes",
    "big data": "Big Data",
    "hadoop": "Hadoop",                      "apache hadoop": "Hadoop",
    "spark": "Spark",                        "apache spark": "Spark",        "pyspark": "Spark",
    "hive": "Hive",
    "airflow": "Airflow",                    "apache airflow": "Airflow",
    "dbt": "dbt",                            "data build tool": "dbt",
    "snowflake": "Snowflake",
    "redshift": "AWS Redshift",              "aws redshift": "AWS Redshift",
    "bigquery": "BigQuery",                  "google bigquery": "BigQuery",
    "databricks": "Databricks",
    "a/b testing": "A/B Testing",            "ab testing": "A/B Testing",
 
    # ── Security ───────────────────────────────────────────────────
    "cybersecurity": "Cybersecurity",        "cyber security": "Cybersecurity",
    "information security": "Cybersecurity", "infosec": "Cybersecurity",
    "network security": "Network Security",
    "application security": "Application Security", "appsec": "Application Security",
    "penetration testing": "Penetration Testing", "pen testing": "Penetration Testing",
    "pentest": "Penetration Testing",        "ethical hacking": "Penetration Testing",
    "vulnerability assessment": "Security Testing",
    "siem": "SIEM",
    "soc": "SOC",
    "iam": "IAM",                            "identity access management": "IAM",
    "zero trust": "Zero Trust Security",
    "devsecops": "DevSecOps",               "dev sec ops": "DevSecOps",
    "ssl": "SSL/TLS",                        "tls": "SSL/TLS",               "ssl/tls": "SSL/TLS",
    "encryption": "Encryption",
    "authentication": "Authentication",      "bcrypt": "Authentication",
    "authorization": "Authorization",
    "saml": "SAML",
    "sso": "SSO",
    "firewall": "Network Security",
 
    # ── Mobile Development ─────────────────────────────────────────
    "react native": "React Native",          "react-native": "React Native",
    "flutter": "Flutter",
    "android": "Android",                    "android sdk": "Android",       "android development": "Android",
    "ios": "iOS",                            "ios development": "iOS",
    "swift ui": "SwiftUI",                   "swiftui": "SwiftUI",
    "xamarin": "Xamarin",
    "ionic": "Ionic",
    "expo": "React Native",
    "mobile development": "Mobile Development",
 
    # ── Testing ────────────────────────────────────────────────────
    "testing": "Testing",
    "unit testing": "Unit Testing",
    "integration testing": "Integration Testing",
    "e2e testing": "E2E Testing",            "end to end testing": "E2E Testing",
    "test driven development": "TDD",        "tdd": "TDD",
    "bdd": "BDD",                            "behavior driven development": "BDD",
    "jest": "Jest",
    "pytest": "pytest",
    "mocha": "Mocha",
    "chai": "Chai",
    "selenium": "Selenium",
    "cypress": "Cypress",
    "playwright": "Playwright",
    "postman": "Postman",
    "junit": "JUnit",
    "testng": "TestNG",
    "qa": "QA",                              "quality assurance": "QA",
    "performance testing": "Performance Testing",
    "load testing": "Load Testing",
 
    # ── Project Management & Agile ─────────────────────────────────
    "agile": "Agile",                        "agile methodologies": "Agile",  "agile methodology": "Agile",
    "scrum": "Scrum",
    "kanban": "Kanban",
    "jira": "Jira",
    "confluence": "Confluence",
    "trello": "Trello",
    "asana": "Asana",
    "project management": "Project Management",
    "product management": "Product Management",
    "sprint planning": "Agile",
    "stakeholder management": "Stakeholder Management",
    "team management": "Team Management",    "team leadership": "Team Management",
    "leadership": "Leadership",
    "communication": "Communication",
    "problem solving": "Problem Solving",
 
    # ── Big Data & Streaming ───────────────────────────────────────
    "mapreduce": "MapReduce",                "map reduce": "MapReduce",
    "hbase": "HBase",
    "pig": "Pig",
    "flink": "Apache Flink",                 "apache flink": "Apache Flink",
    "storm": "Apache Storm",                 "apache storm": "Apache Storm",
    "nifi": "Apache NiFi",                   "apache nifi": "Apache NiFi",
 
    # ── Architecture & Design ──────────────────────────────────────
    "system design": "System Design",
    "monolith": "Monolithic Architecture",
    "event driven": "Event-Driven Architecture", "event-driven": "Event-Driven Architecture",
    "domain driven design": "Domain-Driven Design", "ddd": "Domain-Driven Design",
    "design patterns": "Design Patterns",
    "solid": "SOLID Principles",             "solid principles": "SOLID Principles",
    "clean architecture": "Clean Architecture",
    "api gateway": "API Gateway",
    "load balancer": "Load Balancing",
    "caching": "Caching",
    "cdn": "CDN",
    "scalability": "Scalability",
    "high availability": "High Availability",
    "distributed systems": "Distributed Systems",
 
    # ── Blockchain & Web3 ──────────────────────────────────────────
    "blockchain": "Blockchain",
    "solidity": "Solidity",
    "ethereum": "Ethereum",
    "smart contracts": "Smart Contracts",
    "web3": "Web3",                          "web3.js": "Web3",
    "defi": "DeFi",
    "nft": "NFT",
 
    # ── Tools & IDEs ───────────────────────────────────────────────
    "windows server": "Windows Server",
    "active directory": "Active Directory",
    "ldap": "LDAP",
    "virtualbox": "Virtualization",
    "vmware": "VMware",
    "vagrant": "Vagrant",
    "makefile": "Makefile",
    "cmake": "CMake",
    "maven": "Maven",
    "gradle": "Gradle",
    "npm": "npm",
    "yarn": "Yarn",
    "pip": "pip",
    "poetry": "Poetry",
    "conda": "Conda",                        "anaconda": "Conda",
    "vscode": "VS Code",                     "vs code": "VS Code",           "visual studio code": "VS Code",
    "visual studio": "Visual Studio",
    "intellij": "IntelliJ IDEA",
    "pycharm": "PyCharm",
    "eclipse": "Eclipse",
    "vim": "Vim",
    "emacs": "Emacs",
    "slack": "Slack",
    "notion": "Notion",
 
    # ── General / Misc ─────────────────────────────────────────────
    "mern": "MERN Stack",                    "mern stack": "MERN Stack",
    "mean": "MEAN Stack",                    "mean stack": "MEAN Stack",
    "lamp": "LAMP Stack",
    "full stack": "Full Stack Development",  "fullstack": "Full Stack Development",
    "backend": "Backend Development",        "back end": "Backend Development",   "back-end": "Backend Development",
    "frontend": "Frontend Development",      "front end": "Frontend Development", "front-end": "Frontend Development",
    "algorithms": "Algorithms",
    "data structures": "Data Structures",    "data structures and algorithms": "Data Structures", "dsa": "Data Structures",
    "oop": "OOP",                            "object oriented programming": "OOP", "object-oriented programming": "OOP",
    "functional programming": "Functional Programming",
    "simulation": "Simulation",
    "analysis": "Data Analysis",
    "software": "Software Development",
    "programming": "Programming",            "programming basics": "Programming",
    "dashboards": "Data Visualization",
    "validation": "Testing",
    "crud": "Backend Development",
}


def normalize_skill(raw: str) -> str:
    """
    Normalize a raw skill string into a canonical form.
    """
    if not raw:
        return ""
    lower = raw.strip().lower()
    return _SKILL_NORMALIZATION_MAP.get(lower, raw.strip())


def extract_skills(text: str, use_llm: bool = False) -> List[str]:
    """
    Unified extraction API used across the app.

    use_llm=True  → spaCy + Groq LLM  (resume upload only)
    use_llm=False → spaCy only         (jobs sync, role seeding — never burns LLM tokens)
    """
    if not text or not text.strip():
        return []
    data = SkillTool.run(text, use_llm=use_llm)
    raw_skills = data.get("all_skills") or []
    seen = set()
    result: List[str] = []
    for s in raw_skills:
        ns = normalize_skill(s)
        if not ns:
            continue
        key = ns.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(ns)
    return result


# ---------------------------------------------------------------------------
# CONFIG (LLM - GROQ)
# ---------------------------------------------------------------------------
client = Groq(api_key=settings.GROQ_API_KEY)


# ---------------------------------------------------------------------------
# NLP SKILL EXTRACTOR (spaCy + skill.txt)
# ---------------------------------------------------------------------------
class SkillExtractor:
    _nlp = None
    _matcher = None

    @classmethod
    def _initialize(cls) -> None:
        import spacy
        from spacy.matcher import PhraseMatcher
        if cls._nlp is not None:
            return 
        try:
            # Use plain ASCII to avoid Windows console encoding crashes.
            print("[SkillExtractor] Loading spaCy model...")
            cls._nlp = spacy.load("en_core_web_sm")
            matcher = PhraseMatcher(cls._nlp.vocab, attr="LOWER")
            # Skills list lives in skills app data
            skills_path = Path(__file__).resolve().parent.parent / "data" / "skill.txt"
            if not skills_path.exists():
                raise Exception("skill.txt not found in apps/skills/data/")
            skills = [
                line.strip().lower()
                for line in skills_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            patterns = [cls._nlp.make_doc(skill) for skill in skills]
            matcher.add("SKILLS", patterns)
            cls._matcher = matcher
            print(f"[SkillExtractor] Skill matcher initialized with {len(skills)} skills.")
        except Exception as e:
            raise Exception(f"Failed to initialize SkillExtractor: {e}") from e

    @classmethod
    def extract(cls, text: str) -> List[str]:
        if not text:
            return []
        cls._initialize()
        doc = cls._nlp(text)
        matches = cls._matcher(doc)
        skills: Set[str] = set()
        for _, start, end in matches:
            span = doc[start:end]
            skills.add(span.text.lower())
        return sorted(skills)


# ---------------------------------------------------------------------------
# LLM SKILL EXTRACTOR (GROQ)
# ---------------------------------------------------------------------------
class LLMSkillExtractor:
    system_prompt = """
You are an expert resume parsing system.

Your task is to extract ALL professional technical skills from the provided resume text.

INCLUDE:
- Programming languages
- Frameworks and libraries
- Databases
- Cloud platforms
- DevOps tools
- Machine learning tools
- Data science tools
- Web technologies
- Operating systems
- Version control tools
- Software tools and platforms
- Technical methodologies

EXCLUDE:
- Soft skills (e.g., communication, leadership, teamwork)
- Personal traits
- Hobbies
- Certifications (unless they are technologies like AWS, Azure, etc.)
- Company names (unless they are technologies)

RULES:
- Return ONLY valid JSON.
- No explanation.
- No markdown.
- No extra text.
- Lowercase everything.
- Remove duplicates.
- Extract both explicitly mentioned and strongly implied technical skills.
- If a skill appears multiple times, return it only once.

FORMAT:
{
  "skills": ["python", "django", "aws", "machine learning"]
}

If no skills are found, return:
{
  "skills": []
}
"""

    def extract(self, resume_text: str) -> List[str]:
        if not resume_text:
            return []
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Resume:\n{resume_text}"},
                ],
                temperature=0.0,
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r"```json|```", "", text).strip()
            match = re.search(r"\{.*\}", text, re.DOTALL)
            json_text = match.group(0) if match else text
            data = json.loads(json_text)
            skills = data.get("skills", [])
            if not isinstance(skills, list):
                return []
            return list(set(skill.lower() for skill in skills))
        except Exception as e:
            print("[SkillExtractor] Groq Skill Extraction Error:", e)
            return []


# ---------------------------------------------------------------------------
# COMBINED SKILL TOOL (resume upload flow)
# ---------------------------------------------------------------------------
class SkillTool:
    rule_extractor = SkillExtractor()
    llm_extractor = LLMSkillExtractor()

    @staticmethod
    def run(text: str, use_llm: bool = True):
        """
        use_llm=True  → spaCy phrase matcher + Groq LLM  (resume upload)
        use_llm=False → spaCy phrase matcher only          (jobs sync, seeding)
        """
        if not text:
            return {
                "rule_based_skills": [],
                "llm_skills": [],
                "all_skills": [],
            }
        rule_skills: Set[str] = set(SkillTool.rule_extractor.extract(text))
        if use_llm:
            llm_skills: Set[str] = set(SkillTool.llm_extractor.extract(text))
        else:
            llm_skills = set()
        final_skills = sorted(rule_skills.union(llm_skills))
        return {
            "rule_based_skills": sorted(rule_skills),
            "llm_skills": sorted(llm_skills),
            "all_skills": final_skills,
        }