from app.core.config import settings
from app.extraction.providers.base import JSONProvider
from app.extraction.providers.ollama_provider import (
    OllamaJSONProvider,
)


def get_json_provider() -> JSONProvider:

    provider = settings.llm_provider.casefold()

    if provider == "ollama":
        return OllamaJSONProvider()

    if provider == "openai":
        from app.extraction.providers.openai_provider import (
            OpenAIJSONProvider,
        )

        return OpenAIJSONProvider()

    raise ValueError(
        f"Unsupported LLM provider: "
        f"{settings.llm_provider}"
    )