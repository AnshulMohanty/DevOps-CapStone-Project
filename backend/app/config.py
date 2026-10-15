from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FoundIt API"
    # Shown by GET / and in the UI footer - bumping it is the visible change in the live demo.
    app_version: str = "1.0.0"
    database_url: str = "postgresql+psycopg://foundit:foundit@localhost:5432/foundit"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
