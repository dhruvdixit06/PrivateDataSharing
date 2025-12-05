import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Access Review POC v2"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./access_review.db")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "no-reply@example.com")

settings = Settings()
