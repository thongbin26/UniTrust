from pydantic import BaseModel, Field


class URLExtractionResult(BaseModel):
    """Extracted user input, never an official-evidence record."""

    requested_url: str
    final_url: str
    title: str | None = None
    text: str
    content_type: str
    warnings: list[str] = Field(default_factory=list)
