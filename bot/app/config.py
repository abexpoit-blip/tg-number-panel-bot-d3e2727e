from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DATABASE_URL: str = "postgresql+asyncpg://panel:panel@db:5432/panel"
    BOT_TOKEN: str = ""
    ADMIN_CHAT_ID: int = 0
    OTP_FEED_CHANNEL_ID: int = 0
    BOT_BRAND_NAME: str = "Seven1tel Number Panel"


settings = Settings()
