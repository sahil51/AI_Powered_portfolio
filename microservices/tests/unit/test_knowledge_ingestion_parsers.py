from __future__ import annotations

from unittest.mock import MagicMock, patch

from application.knowledge_ingestion.importer import KnowledgeImporter
from application.knowledge_ingestion.models import ImportSource, ImportSourceType
from application.knowledge_ingestion.parsers import (
    BaseDocumentParser,
    DOCXParser,
    HTMLParser,
    MarkdownParser,
    ParseResult,
    PDFParser,
    Section,
    TXTParser,
    WebsiteParser,
)
from domain.knowledge.value_objects import DocumentType


class MockParser(BaseDocumentParser):
    @property
    def supported_extensions(self) -> list[str]:
        return [".mock"]

    @property
    def supported_mime_types(self) -> list[str]:
        return ["application/x-mock"]

    def supports(self, source: ImportSource) -> bool:
        ext = self._get_extension(source.filename or source.file_path)
        return ext in self.supported_extensions or source.mime_type in self.supported_mime_types

    def parse(self, source: ImportSource) -> ParseResult:
        return ParseResult(title="mock", content="mock content")

    def _get_extension(self, path: str) -> str:
        if not path:
            return ""
        idx = path.rfind(".")
        if idx == -1:
            return ""
        return path[idx:].lower()


class TestParseResult:
    def test_defaults(self) -> None:
        result = ParseResult()
        assert result.title == ""
        assert result.content == ""
        assert result.sections == []
        assert result.metadata == {}
        assert result.language == "en"
        assert result.word_count == 0
        assert result.character_count == 0

    def test_with_values(self) -> None:
        sections = [Section(heading="Intro", content="Hello", level=1)]
        result = ParseResult(
            title="Test",
            content="Hello world",
            sections=sections,
            metadata={"author": "me"},
            language="fr",
            word_count=2,
            character_count=11,
        )
        assert result.title == "Test"
        assert result.content == "Hello world"
        assert result.sections == sections
        assert result.metadata == {"author": "me"}
        assert result.language == "fr"
        assert result.word_count == 2
        assert result.character_count == 11


class TestSection:
    def test_defaults(self) -> None:
        section = Section(heading="Intro", content="Some text")
        assert section.heading == "Intro"
        assert section.content == "Some text"
        assert section.level == 0
        assert section.metadata == {}

    def test_with_all_fields(self) -> None:
        section = Section(heading="Deep Dive", content="Details", level=3, metadata={"page": 5})
        assert section.heading == "Deep Dive"
        assert section.level == 3
        assert section.metadata == {"page": 5}


class TestBaseDocumentParser:
    def setup_method(self) -> None:
        self.parser = MockParser()

    def test_can_parse_by_mime_type(self) -> None:
        assert self.parser.can_parse("application/x-mock", ".unknown") is True

    def test_can_parse_by_extension(self) -> None:
        assert self.parser.can_parse("text/plain", ".mock") is True

    def test_can_parse_no_match(self) -> None:
        assert self.parser.can_parse("text/plain", ".txt") is False

    def test_count_words(self) -> None:
        assert self.parser._count_words("hello world") == 2
        assert self.parser._count_words("") == 0
        assert self.parser._count_words("  ") == 0

    def test_extract_sections_from_markdown(self) -> None:
        text = "# Title\n\nSome content\n\n## Sub\n\nMore"
        sections = self.parser._extract_sections_from_markdown(text)
        assert len(sections) == 2
        assert sections[0].heading == "Title"
        assert sections[0].level == 1
        assert sections[1].heading == "Sub"
        assert sections[1].level == 2

    def test_extract_sections_no_headings(self) -> None:
        sections = self.parser._extract_sections_from_markdown("Just plain text")
        assert len(sections) == 1
        assert sections[0].heading == ""
        assert sections[0].content == "Just plain text"

    def test_supports_extension(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="test.mock")
        assert self.parser.supports(source) is True

    def test_supports_mime_type(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, mime_type="application/x-mock")
        assert self.parser.supports(source) is True

    def test_supports_no_match(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="test.txt", mime_type="text/plain")
        assert self.parser.supports(source) is False


class TestPDFParser:
    def setup_method(self) -> None:
        self.parser = PDFParser()

    def test_supported_extensions(self) -> None:
        assert ".pdf" in self.parser.supported_extensions

    def test_supported_mime_types(self) -> None:
        assert "application/pdf" in self.parser.supported_mime_types

    def test_supports_pdf_extension(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="document.pdf")
        assert self.parser.supports(source) is True

    def test_supports_pdf_mime(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, mime_type="application/pdf")
        assert self.parser.supports(source) is True

    def test_parse_empty_source(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="empty.pdf")
        result = self.parser.parse(source)
        assert result.title == "empty.pdf"
        assert result.content == ""
        assert result.metadata == {}

    def test_is_likely_heading_short(self) -> None:
        assert self.parser._is_likely_heading("AB") is False

    def test_is_likely_heading_ends_with_period(self) -> None:
        assert self.parser._is_likely_heading("Introduction.") is False

    def test_is_likely_heading_uppercase(self) -> None:
        assert self.parser._is_likely_heading("INTRODUCTION") is True

    def test_is_likely_heading_normal(self) -> None:
        assert self.parser._is_likely_heading("Introduction") is False

    def test_clean_text_collapses_spaces(self) -> None:
        cleaned = self.parser._clean_text("hello    world")
        assert cleaned == "hello world"

    def test_clean_text_collapses_whitespace(self) -> None:
        cleaned = self.parser._clean_text("line1\n\n\n\nline2")
        assert cleaned == "line1 line2"


class TestDOCXParser:
    def setup_method(self) -> None:
        self.parser = DOCXParser()

    def test_supported_extensions(self) -> None:
        assert ".docx" in self.parser.supported_extensions

    def test_supported_mime_types(self) -> None:
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in self.parser.supported_mime_types

    def test_supports_docx_extension(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="report.docx")
        assert self.parser.supports(source) is True

    def test_parse_empty_content(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content="", filename="test.docx")
        result = self.parser.parse(source)
        assert result.title == "test.docx"

    def test_parse_empty_zip(self) -> None:
        import io
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content=buf.getvalue(), filename="test.docx")
        result = self.parser.parse(source)
        assert result.title == "test.docx"

    def test_parse_invalid_zip_returns_empty(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content=b"not a zip file", filename="test.docx")
        result = self.parser.parse(source)
        assert result.title == "test.docx"

    def test_parse_missing_document_xml(self) -> None:
        import io
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("other/file.xml", "<xml/>")
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content=buf.getvalue(), filename="test.docx")
        result = self.parser.parse(source)
        assert result.title == "test.docx"

    def test_get_heading_level(self) -> None:
        assert self.parser._get_heading_level("Heading1") == 1
        assert self.parser._get_heading_level("heading2") == 2
        assert self.parser._get_heading_level("Normal") == 0


class TestMarkdownParser:
    def setup_method(self) -> None:
        self.parser = MarkdownParser()

    def test_supported_extensions(self) -> None:
        assert ".md" in self.parser.supported_extensions
        assert ".markdown" in self.parser.supported_extensions

    def test_supported_mime_types(self) -> None:
        assert "text/markdown" in self.parser.supported_mime_types

    def test_supports_md_extension(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="readme.md")
        assert self.parser.supports(source) is True

    def test_parse_empty_content(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content="", filename="test.md")
        result = self.parser.parse(source)
        assert result.title == "test.md"

    def test_parse_with_headings(self) -> None:
        md = "# Main Title\n\nSome intro text.\n\n## Section One\n\nContent here.\n\n### Subsection\n\nMore details."
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content=md, filename="doc.md")
        result = self.parser.parse(source)
        assert result.title == "Main Title"
        assert len(result.sections) == 3
        assert result.sections[0].heading == "Main Title"
        assert result.sections[0].level == 1
        assert result.sections[1].heading == "Section One"
        assert result.sections[1].level == 2
        assert result.sections[2].heading == "Subsection"
        assert result.sections[2].level == 3

    def test_parse_with_front_matter(self) -> None:
        md = "---\ntitle: My Front Matter Doc\nauthor: Test\n---\n\n# Content\n\nBody text."
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content=md, filename="doc.md")
        result = self.parser.parse(source)
        assert result.title == "My Front Matter Doc"
        assert result.metadata.get("author") == "Test"
        assert result.metadata.get("title") == "My Front Matter Doc"

    def test_parse_with_code_blocks(self) -> None:
        md = "# Code Example\n\n```python\nprint('hello')\n```\n\nSome text."
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content=md, filename="code.md")
        result = self.parser.parse(source)
        assert result.title == "Code Example"
        assert "print('hello')" in result.content

    def test_parse_plain_text(self) -> None:
        md = "Just some plain text without headings."
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content=md, filename="plain.md")
        result = self.parser.parse(source)
        assert len(result.sections) == 1
        assert result.content == md

    def test_extract_front_matter_valid(self) -> None:
        text = "---\nkey: value\nname: test\n---\n\nbody"
        fm = self.parser._extract_front_matter(text)
        assert fm == {"key": "value", "name": "test"}

    def test_extract_front_matter_empty(self) -> None:
        fm = self.parser._extract_front_matter("no front matter")
        assert fm == {}


class TestHTMLParser:
    def setup_method(self) -> None:
        self.parser = HTMLParser()

    def test_supported_extensions(self) -> None:
        assert ".html" in self.parser.supported_extensions
        assert ".htm" in self.parser.supported_extensions

    def test_supported_mime_types(self) -> None:
        assert "text/html" in self.parser.supported_mime_types

    def test_supports_html_extension(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="page.html")
        assert self.parser.supports(source) is True

    def test_parse_empty_content(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content="", filename="test.html")
        result = self.parser.parse(source)
        assert result.title == "test.html"

    def test_parse_html_title(self) -> None:
        html = "<html><head><title>My Page</title></head><body><p>Content</p></body></html>"
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content=html, filename="page.html")
        result = self.parser.parse(source)
        assert result.title == "My Page"
        assert "Content" in result.content

    def test_parse_html_strips_script(self) -> None:
        html = "<html><body><script>alert('xss')</script><p>Real content</p></body></html>"
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content=html, filename="page.html")
        result = self.parser.parse(source)
        assert "alert" not in result.content
        assert "Real content" in result.content

    def test_parse_html_strips_style(self) -> None:
        html = "<html><head><style>body { color: red; }</style></head><body><p>Visible</p></body></html>"
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content=html, filename="page.html")
        result = self.parser.parse(source)
        assert "color" not in result.content
        assert "Visible" in result.content

    def test_parse_html_contains_content(self) -> None:
        html = "<html><body><h1>Main</h1><p>Intro</p><h2>Sub</h2><p>Detail</p></body></html>"
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content=html, filename="page.html")
        result = self.parser.parse(source)
        assert "Main" in result.content
        assert "Intro" in result.content
        assert "Detail" in result.content


class TestTXTParser:
    def setup_method(self) -> None:
        self.parser = TXTParser()

    def test_supported_extensions(self) -> None:
        assert ".txt" in self.parser.supported_extensions

    def test_supported_mime_types(self) -> None:
        assert "text/plain" in self.parser.supported_mime_types

    def test_supports_txt_extension(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="notes.txt")
        assert self.parser.supports(source) is True

    def test_parse_empty_content(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content="", filename="test.txt")
        result = self.parser.parse(source)
        assert result.title == "test.txt"

    def test_parse_plain_text(self) -> None:
        text = "Hello world.\nThis is a plain text document."
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content=text, filename="notes.txt")
        result = self.parser.parse(source)
        assert result.title == "notes.txt"
        assert result.content == text
        assert result.metadata.get("encoding") == "utf-8"
        assert result.word_count == 8

    def test_parse_with_markdown_like_headings(self) -> None:
        text = "# Heading\n\nSome content\n\n## Subheading\n\nMore content"
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, content=text, filename="notes.txt")
        result = self.parser.parse(source)
        assert len(result.sections) == 2
        assert result.sections[0].heading == "Heading"
        assert result.sections[0].level == 1


class TestWebsiteParser:
    def setup_method(self) -> None:
        self.parser = WebsiteParser()

    def test_supported_extensions(self) -> None:
        assert ".html" in self.parser.supported_extensions

    def test_supported_mime_types(self) -> None:
        assert "text/html" in self.parser.supported_mime_types

    def test_supports_url_source(self) -> None:
        source = ImportSource(url="https://example.com", source_type=ImportSourceType.URL)
        assert self.parser.supports(source) is True

    def test_supports_website_source(self) -> None:
        source = ImportSource(url="https://example.com", source_type=ImportSourceType.WEBSITE)
        assert self.parser.supports(source) is True

    def test_supports_no_url(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD)
        assert self.parser.supports(source) is False

    @patch("application.knowledge_ingestion.parsers.website_parser.httpx.Client")
    def test_parse_with_mock_response(self, mock_client_cls: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = "<html><head><title>Test Page</title></head><body><p>Hello world</p></body></html>"
        mock_response.content = b"<html><body><p>Hello world</p></body></html>"
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        source = ImportSource(url="https://example.com", source_type=ImportSourceType.WEBSITE)
        result = self.parser.parse(source)
        assert result.title == "Test Page"
        assert "Hello world" in result.content
        assert result.metadata.get("source_url") == "https://example.com"

    @patch("application.knowledge_ingestion.parsers.website_parser.httpx.Client")
    def test_parse_with_content_uses_content_directly(self, mock_client_cls: MagicMock) -> None:
        source = ImportSource(
            content="<html><body><p>Provided content</p></body></html>",
            url="https://example.com",
            source_type=ImportSourceType.WEBSITE,
        )
        result = self.parser.parse(source)
        assert "Provided content" in result.content
        mock_client_cls.assert_not_called()


class TestParserRegistry:
    def setup_method(self) -> None:
        self.mock_repo = MagicMock()
        self.mock_processor = MagicMock()
        self.importer = KnowledgeImporter(self.mock_processor, self.mock_repo)

    def test_find_parser_pdf(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="test.pdf")
        parser = self.importer.find_parser(source)
        assert isinstance(parser, PDFParser)

    def test_find_parser_docx(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="test.docx")
        parser = self.importer.find_parser(source)
        assert isinstance(parser, DOCXParser)

    def test_find_parser_markdown(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="test.md")
        parser = self.importer.find_parser(source)
        assert isinstance(parser, MarkdownParser)

    def test_find_parser_html(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="test.html")
        parser = self.importer.find_parser(source)
        assert isinstance(parser, HTMLParser)

    def test_find_parser_txt(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="test.txt")
        parser = self.importer.find_parser(source)
        assert isinstance(parser, TXTParser)

    def test_find_parser_website(self) -> None:
        source = ImportSource(url="https://example.com", source_type=ImportSourceType.WEBSITE)
        parser = self.importer.find_parser(source)
        assert isinstance(parser, WebsiteParser)

    def test_find_parser_no_match(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="test.xyz")
        parser = self.importer.find_parser(source)
        assert parser is None

    def test_find_parser_by_mime_type(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, mime_type="application/pdf")
        parser = self.importer.find_parser(source)
        assert isinstance(parser, PDFParser)

    def test_register_parser(self) -> None:
        mock = MockParser()
        self.importer.register_parser(mock)
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="test.mock")
        parser = self.importer.find_parser(source)
        assert isinstance(parser, MockParser)

    def test_resolve_doc_type_website(self) -> None:
        source = ImportSource(url="https://example.com", source_type=ImportSourceType.WEBSITE)
        parser = self.importer.find_parser(source)
        doc_type = self.importer._resolve_doc_type(source, parser)
        assert doc_type == DocumentType.WEBSITE

    def test_resolve_doc_type_pdf(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="test.pdf")
        parser = self.importer.find_parser(source)
        doc_type = self.importer._resolve_doc_type(source, parser)
        assert doc_type == DocumentType.PDF

    def test_resolve_doc_type_docx(self) -> None:
        source = ImportSource(source_type=ImportSourceType.FILE_UPLOAD, filename="test.docx")
        parser = self.importer.find_parser(source)
        doc_type = self.importer._resolve_doc_type(source, parser)
        assert doc_type == DocumentType.DOCX
