from pydantic import BaseModel, Field


class OCRResult(BaseModel):
    """Transcription output only; it is never a verification verdict."""

    text: str
    engine: str
    warnings: list[str] = Field(default_factory=list)
    mean_confidence: float | None = None


class OCRProcessingError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 503):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
