import os
from pathlib import Path
from dotenv import load_dotenv

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATES_DIR = BASE_DIR / "templates"
DOCS_DIR = BASE_DIR / "docs"

# Ensure directories exist
for folder in [DATA_DIR, OUTPUT_DIR, TEMPLATES_DIR, DOCS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Load .env file
load_dotenv(BASE_DIR / ".env")

# API Keys & LLM Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

# Agent Parameters
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "6"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))
MOCK_FALLBACK_ON_AUTH_ERROR = os.getenv("MOCK_FALLBACK_ON_AUTH_ERROR", "true").lower() in ("true", "1", "yes")

# Data File Paths
APPS_CSV_PATH = DATA_DIR / "apps.csv"
RESEARCH_RESULTS_PATH = DATA_DIR / "research_results.json"
VERIFICATION_RESULTS_PATH = DATA_DIR / "verification_results.json"
AUDIT_CSV_PATH = DATA_DIR / "audit.csv"
INSIGHTS_JSON_PATH = DATA_DIR / "insights.json"
REPORT_HTML_PATH = OUTPUT_DIR / "index.html"
DOCS_HTML_PATH = DOCS_DIR / "index.html"
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
