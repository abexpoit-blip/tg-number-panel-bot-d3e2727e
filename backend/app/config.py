from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://panel:panel@db:5432/panel"
    JWT_SECRET: str = "change_me"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MIN: int = 720
    ADMIN_EMAIL: str = "admin@seven1tel.com"
    ADMIN_PASSWORD: str = "change_me"
    BOT_BRAND_NAME: str = "Seven1tel Number Panel"


settings = Settings()
