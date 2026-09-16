from pydantic import BaseModel

from app.extraction.providers.factory import (
    get_json_provider,
)


class SmokeResult(BaseModel):
    status: str
    number: int


def main():

    provider = get_json_provider()

    result = provider.generate_json(
        system_prompt=(
            "Return only structured data "
            "matching the provided schema."
        ),
        user_prompt=(
            "Set status to exactly "
            "'UniTrust Local AI OK' "
            "and number to 42."
        ),
        json_schema=(
            SmokeResult.model_json_schema()
        ),
    )

    parsed = (
        SmokeResult.model_validate_json(
            result
        )
    )

    print(parsed)


if __name__ == "__main__":
    main()