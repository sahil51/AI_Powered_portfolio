from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from application.knowledge_ingestion.models import ImportSource


@dataclass
class Section:
    heading: str
    content: str
    level: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseResult:
    title: str = ""
    content: str = ""
    sections: list[Section] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    language: str = "en"
    word_count: int = 0
    character_count: int = 0


class BaseDocumentParser(ABC):
    @abstractmethod
    def parse(self, source: ImportSource) -> ParseResult:
        ...

    @abstractmethod
    def supports(self, source: ImportSource) -> bool:
        ...

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        ...

    @property
    @abstractmethod
    def supported_mime_types(self) -> list[str]:
        ...

    def can_parse(self, mime_type: str, extension: str) -> bool:
        if mime_type in self.supported_mime_types:
            return True
        if extension in self.supported_extensions:
            return True
        return False

    def _count_words(self, text: str) -> int:
        return len(text.split())

    def _extract_sections_from_markdown(self, text: str) -> list[Section]:
        sections: list[Section] = []
        lines = text.splitlines()
        current_heading = ""
        current_content: list[str] = []
        current_level = 0

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                hashes = len(stripped) - len(stripped.lstrip("#"))
                if 1 <= hashes <= 6 and (len(stripped) == hashes or stripped[hashes] == " "):
                    if current_heading:
                        sections.append(Section(
                            heading=current_heading,
                            content="\n".join(current_content).strip(),
                            level=current_level,
                        ))
                    current_heading = stripped.lstrip("#").strip()
                    current_level = hashes
                    current_content = []
                    continue
            current_content.append(line)

        if current_heading or current_content:
            sections.append(Section(
                heading=current_heading,
                content="\n".join(current_content).strip(),
                level=current_level,
            ))

        return sections
