from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://panel:panel@db:5432/panel"
    JWT_SECRET: str = "change_me"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MIN: int = 720
    ADMIN_EMAIL: str = Field("admin@seven1tel.com", validation_alias=AliasChoices("ADMIN_EMAIL", "ADMIN_USERNAME"))
    ADMIN_PASSWORD: str = Field("change_me", validation_alias=AliasChoices("ADMIN_PASSWORD", "ADMIN_PASS"))
    BOT_BRAND_NAME: str = "Seven1tel Number Panel"


settings = Settings()
