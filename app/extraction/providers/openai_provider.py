from openai import OpenAI

from app.core.config import settings
from app.extraction.providers.base import (
    JSONProvider,
)


class OpenAIJSONProvider(
    JSONProvider
):

    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is missing "
                "from .env"
            )

        self.client = OpenAI(
            api_key=(
                settings.openai_api_key
            )
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return settings.openai_model

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict,
    ) -> str:

        response = (
            self.client.responses.create(
                model=(
                    settings.openai_model
                ),

                instructions=(
                    system_prompt
                ),

                input=user_prompt,

                reasoning={
                    "effort": (
                        settings
                        .openai_reasoning_effort
                    )
                },

                text={
                    "format": {
                        "type": "json_schema",
                        "name": (
                            "unitrust_extraction"
                        ),
                        "schema": (
                            json_schema
                        ),
                        "strict": False,
                    }
                },

                max_output_tokens=6000,

                store=False,
            )
        )

        return response.output_text