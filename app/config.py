import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@db:5432/tasks",
)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
