from urllib.parse import quote_plus

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    POSTGRES_USER: str = "panel"
    POSTGRES_PASSWORD: str = "panel"
    POSTGRES_DB: str = "panel"
    DATABASE_URL: str = ""
    BOT_TOKEN: str = Field("", validation_alias=AliasChoices("BOT_TOKEN", "TELEGRAM_BOT_TOKEN"))
    ADMIN_CHAT_ID: int = 0
    OTP_FEED_CHANNEL_ID: int = Field(
        0,
        validation_alias=AliasChoices("OTP_FEED_CHANNEL_ID", "OTP_CHANNEL_ID"),
    )
    BOT_BRAND_NAME: str = "Seven1tel Number Panel"

    @field_validator("DATABASE_URL", "BOT_TOKEN", "BOT_BRAND_NAME", mode="before")
    @classmethod
    def _strip_strings(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _build_database_url(self) -> "Settings":
        if not self.DATABASE_URL:
            user = quote_plus(self.POSTGRES_USER)
            password = quote_plus(self.POSTGRES_PASSWORD)
            db = quote_plus(self.POSTGRES_DB)
            self.DATABASE_URL = f"postgresql+asyncpg://{user}:{password}@db:5432/{db}"
        return self


settings = Settings()
