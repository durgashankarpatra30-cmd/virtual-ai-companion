import os
from dotenv import load_dotenv

# Ensure SSLKEYLOGFILE doesn't cause permission error on Windows with Python 3.14
os.environ.pop("SSLKEYLOGFILE", None)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

# Load environment files
for env_path in [
    os.path.join(BASE_DIR, ".env"),
    os.path.join(ROOT_DIR, ".env"),
    os.path.join(BASE_DIR, "gemini.env"),
]:
    if os.path.exists(env_path):
        load_dotenv(env_path)

# Cloud LLM API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip().strip("\"'").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip().strip("\"'").strip()
if not GROQ_MODEL:
    GROQ_MODEL = "openai/gpt-oss-120b"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip("\"'").strip()