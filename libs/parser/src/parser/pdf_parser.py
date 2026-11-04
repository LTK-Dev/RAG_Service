import fitz
from io import BytesIO
from .strategy import IParserStrategy
import logging

logger = logging.getLogger(__name__)


class PdfParser(IParserStrategy):
    def parse(self, file_data: BytesIO) -> str:
        """Parses PDF file content into plain text."""
        logger.debug('Parsing PDF file...')
        text = ''
        try:
            with fitz.open(stream=file_data, filetype='pdf') as doc:
                for page in doc:
                    text += page.get_text()
            return text
        except Exception as e:
            logger.exception('Failed to parse PDF', extra={'error': str(e)})
            raise
