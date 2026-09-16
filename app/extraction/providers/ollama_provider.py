from ollama import Client

from app.core.config import settings
from app.extraction.providers.base import JSONProvider


class OllamaJSONProvider(JSONProvider):

    def __init__(self):
        self.client = Client(
            host=settings.ollama_base_url
        )

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return settings.ollama_model

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict,
    ) -> str:

        response = self.client.chat(
            model=settings.ollama_model,

            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],

            format=json_schema,

            options={
                "temperature": 0,
                "num_ctx": settings.ollama_num_ctx,
            },

            think=False,

            stream=False,
        )

        return response.message.content