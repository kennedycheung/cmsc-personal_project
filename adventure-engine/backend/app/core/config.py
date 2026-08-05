from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    app_name: str = 'Adventure Arbitrage Engine API'
    database_url: str = 'sqlite:///./adventure.db'
    environment: str = 'development'
    # Also used to sign JWTs (see core/security.py) -- must be overridden via
    # env var in any real deployment, not left as the default.
    secret_key: str = 'change-me'
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    cors_origins: list[str] = ['http://localhost:5173', 'http://127.0.0.1:5173']

    # SerpAPI is a paid, keyed service (unlike every other external API this
    # app uses) -- see documentation/activity_discovery_engine.md. Empty by
    # default; the discovery endpoint returns a clear 503 rather than making
    # doomed billed requests when this isn't set.
    serpapi_key: str = ''

    # case_sensitive=False (the pydantic-settings default) so the documented
    # DATABASE_URL / SECRET_KEY env vars actually match these lowercase field
    # names. True here previously meant only an exact-case "database_url" env
    # var would ever override the SQLite default -- DATABASE_URL silently did
    # nothing.
    model_config = SettingsConfigDict(env_file=BASE_DIR / '.env', case_sensitive=False)

settings = Settings()
