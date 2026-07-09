from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KnowledgeMetadata:
    author: str = ""
    description: str = ""
    source_url: str = ""
    content_type: str = ""
    language: str = "en"
    tags: tuple[str, ...] = ()
    custom: dict[str, str] = field(default_factory=dict)
