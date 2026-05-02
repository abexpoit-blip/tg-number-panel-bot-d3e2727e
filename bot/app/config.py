from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DATABASE_URL: str = "postgresql+asyncpg://panel:panel@db:5432/panel"
    BOT_TOKEN: str = Field("", validation_alias=AliasChoices("BOT_TOKEN", "TELEGRAM_BOT_TOKEN"))
    ADMIN_CHAT_ID: int = 0
    OTP_FEED_CHANNEL_ID: int = Field(
        0,
        validation_alias=AliasChoices("OTP_FEED_CHANNEL_ID", "OTP_CHANNEL_ID"),
    )
    BOT_BRAND_NAME: str = "Seven1tel Number Panel"


settings = Settings()
