import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./access_review.db")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "no-reply@example.com")

settings = Settings()
