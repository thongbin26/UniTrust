from abc import ABC, abstractmethod

from app.extraction.types import (
    ExtractionInput,
    ExtractionRun,
)


class Extractor(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def extract(
        self,
        notice: ExtractionInput,
    ) -> ExtractionRun:
        raise NotImplementedError