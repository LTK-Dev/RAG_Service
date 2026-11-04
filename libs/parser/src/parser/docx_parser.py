from docx import Document
from io import BytesIO
from .strategy import IParserStrategy
import logging

logger = logging.getLogger(__name__)


class DocxParser(IParserStrategy):
    def parse(self, file_data: BytesIO) -> str:
        """Parses DOCX file content into plain text."""
        logger.debug('Parsing DOCX file...')
        try:
            doc = Document(file_data)
            text = '\n'.join([para.text for para in doc.paragraphs if para.text])
            return text
        except Exception as e:
            logger.exception('Failed to parse DOCX', extra={'error': str(e)})
            raise
