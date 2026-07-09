from __future__ import annotations

from application.knowledge_ingestion.parsers.base import BaseDocumentParser, ParseResult, Section
from application.knowledge_ingestion.parsers.docx_parser import DOCXParser
from application.knowledge_ingestion.parsers.html_parser import HTMLParser
from application.knowledge_ingestion.parsers.markdown_parser import MarkdownParser
from application.knowledge_ingestion.parsers.pdf_parser import PDFParser
from application.knowledge_ingestion.parsers.txt_parser import TXTParser
from application.knowledge_ingestion.parsers.website_parser import WebsiteParser

__all__ = [
    "BaseDocumentParser",
    "ParseResult",
    "Section",
    "PDFParser",
    "DOCXParser",
    "MarkdownParser",
    "HTMLParser",
    "TXTParser",
    "WebsiteParser",
]
