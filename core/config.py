from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Notion
    notion_token: str
    notion_database_id: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()