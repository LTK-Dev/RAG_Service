from abc import ABC, abstractmethod
from io import BytesIO


class IParserStrategy(ABC):
    @abstractmethod
    def parse(self, file_data: BytesIO) -> str:
        """Parses file content into plain text."""
        raise NotImplementedError()
