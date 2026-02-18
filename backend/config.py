import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "./data/enbek.db")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,https://enbek-ai.vercel.app"
).split(",")

# Groq models
GROQ_MODEL_MAIN = "llama-3.3-70b-versatile"
GROQ_MODEL_FAST = "llama-3.1-8b-instant"

# Groq rate limits (free tier safe)
GROQ_MAX_REQUESTS_PER_MINUTE = 25
GROQ_RETRY_AFTER_SECONDS = 60
GROQ_MAX_RETRIES = 3

# Parser settings
PARSER_DELAY_SECONDS = 2.5
PARSER_USER_AGENT = "EnbekAI Research Bot/1.0 (student project for alem.ai battle)"
ENBEK_BASE_URL = "https://www.enbek.kz"

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
