from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    openai_api_key: str | None = None
    ollama_base_url: str | None = None


settings = Settings()  # type: ignore[call-arg]
