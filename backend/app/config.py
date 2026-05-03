from urllib.parse import quote_plus

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    POSTGRES_USER: str = "panel"
    POSTGRES_PASSWORD: str = "panel"
    POSTGRES_DB: str = "panel"
    DATABASE_URL: str = ""
    JWT_SECRET: str = "change_me"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MIN: int = 720
    ADMIN_EMAIL: str = Field("admin@seven1tel.com", validation_alias=AliasChoices("ADMIN_EMAIL", "ADMIN_USERNAME"))
    ADMIN_PASSWORD: str = Field("change_me", validation_alias=AliasChoices("ADMIN_PASSWORD", "ADMIN_PASS"))
    BOT_BRAND_NAME: str = "Seven1tel Number Panel"
    BOT_TOKEN: str = ""

    @field_validator("DATABASE_URL", "JWT_SECRET", "ADMIN_EMAIL", "ADMIN_PASSWORD", mode="before")
    @classmethod
    def _strip_strings(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _build_database_url(self) -> "Settings":
        if not self.DATABASE_URL or "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL:
            user = quote_plus(self.POSTGRES_USER)
            password = quote_plus(self.POSTGRES_PASSWORD)
            db = quote_plus(self.POSTGRES_DB)
            self.DATABASE_URL = f"postgresql+asyncpg://{user}:{password}@db:5432/{db}"
        return self


settings = Settings()
