from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile
from typing import Any

from application.knowledge_ingestion.models import ImportSource
from application.knowledge_ingestion.parsers.base import BaseDocumentParser, ParseResult, Section

NAMESPACES = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


class DOCXParser(BaseDocumentParser):
    @property
    def supported_extensions(self) -> list[str]:
        return [".docx"]

    @property
    def supported_mime_types(self) -> list[str]:
        return [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]

    def supports(self, source: ImportSource) -> bool:
        ext = self._get_extension(source.filename or source.file_path)
        return ext in self.supported_extensions or source.mime_type in self.supported_mime_types

    def parse(self, source: ImportSource) -> ParseResult:
        content = self._read_content(source)
        if not content:
            return ParseResult(title=source.filename or "Untitled")

        try:
            z = zipfile.ZipFile(io.BytesIO(content))
            if "word/document.xml" not in z.namelist():
                return ParseResult(title=source.filename or "Untitled")
            xml_content = z.read("word/document.xml")
        except zipfile.BadZipFile:
            return ParseResult(title=source.filename or "Untitled")

        root = ET.fromstring(xml_content)
        body = root.find(".//w:body", NAMESPACES)
        if body is None:
            return ParseResult(title=source.filename or "Untitled")

        paragraphs: list[str] = []
        sections: list[Section] = []
        metadata: dict[str, Any] = {}

        core_props = self._read_core_properties(z)
        if core_props:
            metadata.update(core_props)

        for para in body.findall(".//w:p", NAMESPACES):
            text = self._extract_paragraph_text(para)
            if not text:
                continue
            style = self._get_paragraph_style(para)
            if style and style.startswith("Heading"):
                level = self._get_heading_level(style)
                sections.append(Section(heading=text, content="", level=level))
            paragraphs.append(text)

        content_text = "\n\n".join(paragraphs)
        title = str(metadata.get("title", "")) or source.filename or "Untitled"

        return ParseResult(
            title=title,
            content=content_text,
            sections=sections,
            metadata=metadata,
            word_count=self._count_words(content_text),
            character_count=len(content_text),
        )

    def _read_content(self, source: ImportSource) -> bytes:
        if source.file_path:
            with open(source.file_path, "rb") as f:
                return f.read()
        if source.content:
            return source.content.encode("utf-8") if isinstance(source.content, str) else source.content
        return b""

    def _extract_paragraph_text(self, para: ET.Element) -> str:
        texts: list[str] = []
        for t in para.findall(".//w:t", NAMESPACES):
            if t.text:
                texts.append(t.text)
        return "".join(texts).strip()

    def _get_paragraph_style(self, para: ET.Element) -> str:
        ppr = para.find("w:pPr", NAMESPACES)
        if ppr is not None:
            pstyle = ppr.find("w:pStyle", NAMESPACES)
            if pstyle is not None and pstyle.get("w:val"):
                return str(pstyle.get("w:val"))
        return ""

    def _get_heading_level(self, style: str) -> int:
        for i in range(1, 10):
            if f"Heading{i}" in style or f"heading{i}" in style:
                return i
        return 0

    def _read_core_properties(self, z: zipfile.ZipFile) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        try:
            if "docProps/core.xml" in z.namelist():
                core = ET.fromstring(z.read("docProps/core.xml"))
                core_ns = {
                    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
                    "dc": "http://purl.org/dc/elements/1.1/",
                }
                for title_el in core.findall(".//dc:title", core_ns):
                    if title_el.text:
                        metadata["title"] = title_el.text
                for creator in core.findall(".//dc:creator", core_ns):
                    if creator.text:
                        metadata["author"] = creator.text
                for desc in core.findall(".//dc:description", core_ns):
                    if desc.text:
                        metadata["description"] = desc.text
        except Exception:
            pass
        return metadata

    def _get_extension(self, path: str) -> str:
        if not path:
            return ""
        idx = path.rfind(".")
        if idx == -1:
            return ""
        return path[idx:].lower()
