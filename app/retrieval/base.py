from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel, Field

class RetrievalChunk(BaseModel):
    chunk_id: str
    notice_id: int
    version_id: int
    source_id: str
    start_char: int
    end_char: int
    text: str
    
    # Metadata for better retrieval/context
    title: str
    publication_date: datetime | None = None
    canonical_url: str | None = None
    
    is_latest_version: bool = False

class RetrievalResult(BaseModel):
    chunk: RetrievalChunk
    rank: int
    score: float
    retrieval_method: str

class Retriever(ABC):
    @abstractmethod
    def index(self, chunks: list[RetrievalChunk]) -> None:
        """Index a list of chunks."""
        pass
        
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        """Search and return ranked results."""
        pass
