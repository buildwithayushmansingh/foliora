import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    STARTUP_NAME = os.getenv("STARTUP_NAME", "Foliora")
    CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "hello@example.com")
    # The existing portfolio stays a separate project; we only link/embed it.
    PORTFOLIO_URL = os.getenv("PORTFOLIO_URL", "").strip()
    PORTFOLIO_TITLE = os.getenv("PORTFOLIO_TITLE", "Developer Portfolio")
    GITHUB_URL = os.getenv("GITHUB_URL") or "#"
    LINKEDIN_URL = os.getenv("LINKEDIN_URL") or "#"


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
