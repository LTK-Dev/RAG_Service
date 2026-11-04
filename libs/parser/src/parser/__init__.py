from __future__ import annotations

from .docx_parser import DocxParser
from .pdf_parser import PdfParser
from .strategy import IParserStrategy

__all__ = ['DocxParser', 'PdfParser', 'IParserStrategy']
