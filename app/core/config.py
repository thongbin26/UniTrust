from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "UniTrust"
    app_env: str = "development"
    debug: bool = True

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    database_url: str = "sqlite:///./unitrust.db"

    # Step 2 chưa sử dụng AI.
    llm_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "ollama"

    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    openai_reasoning_effort: str = "none"

    # Ollama settings
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:4b"
    ollama_num_ctx: int = 8192

settings = Settings()