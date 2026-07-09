from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from application.embedding.exceptions import EmbeddingChunkingError
from domain.knowledge.value_objects import ChunkingStrategy


@dataclass
class ChunkingResult:
    chunks: list[str] = field(default_factory=list)
    chunk_count: int = 0
    strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    overlap: int = 0


def _estimate_tokens(text: str) -> int:
    return len(text.split())


class ChunkerStrategy(ABC):
    def __init__(self, max_size: int = 2000, overlap: int = 200) -> None:
        if max_size <= 0:
            raise EmbeddingChunkingError("max_size must be positive")
        if overlap < 0:
            raise EmbeddingChunkingError("overlap cannot be negative")
        if overlap >= max_size:
            raise EmbeddingChunkingError("overlap must be less than max_size")
        self._max_size = max_size
        self._overlap = overlap

    @abstractmethod
    def chunk(self, text: str) -> ChunkingResult:
        ...


class FixedSizeChunker(ChunkerStrategy):
    def chunk(self, text: str) -> ChunkingResult:
        if not text.strip():
            return ChunkingResult(strategy=ChunkingStrategy.FIXED_SIZE)
        words = text.split()
        chunks: list[str] = []
        i = 0
        while i < len(words):
            chunk_words = words[i:i + self._max_size]
            chunks.append(" ".join(chunk_words))
            i += self._max_size
        return ChunkingResult(
            chunks=chunks,
            chunk_count=len(chunks),
            strategy=ChunkingStrategy.FIXED_SIZE,
            overlap=0,
        )


class SlidingWindowChunker(ChunkerStrategy):
    def chunk(self, text: str) -> ChunkingResult:
        if not text.strip():
            return ChunkingResult(strategy=ChunkingStrategy.SLIDING_WINDOW)
        words = text.split()
        chunks: list[str] = []
        i = 0
        while i < len(words):
            chunk_words = words[i:i + self._max_size]
            chunks.append(" ".join(chunk_words))
            if i + self._max_size >= len(words):
                break
            i += self._max_size - self._overlap
        return ChunkingResult(
            chunks=chunks,
            chunk_count=len(chunks),
            strategy=ChunkingStrategy.SLIDING_WINDOW,
            overlap=self._overlap,
        )


class ParagraphChunker(ChunkerStrategy):
    def chunk(self, text: str) -> ChunkingResult:
        if not text.strip():
            return ChunkingResult(strategy=ChunkingStrategy.PARAGRAPH)
        paragraphs = re.split(r"\n\s*\n", text.strip())
        chunks: list[str] = []
        buffer: list[str] = []
        buffer_len = 0
        for para in paragraphs:
            para_tokens = _estimate_tokens(para)
            if para_tokens > self._max_size:
                if buffer:
                    chunks.append("\n\n".join(buffer))
                    buffer = []
                    buffer_len = 0
                words = para.split()
                for i in range(0, len(words), self._max_size):
                    chunks.append(" ".join(words[i:i + self._max_size]))
            elif buffer_len + para_tokens <= self._max_size:
                buffer.append(para)
                buffer_len += para_tokens
            else:
                chunks.append("\n\n".join(buffer))
                overlap_start = max(0, len(buffer) - self._overlap)
                buffer = buffer[overlap_start:]
                buffer_len = _estimate_tokens("\n\n".join(buffer))
                buffer.append(para)
                buffer_len += para_tokens
        if buffer:
            chunks.append("\n\n".join(buffer))
        return ChunkingResult(
            chunks=chunks,
            chunk_count=len(chunks),
            strategy=ChunkingStrategy.PARAGRAPH,
            overlap=self._overlap,
        )


class HeadingAwareChunker(ChunkerStrategy):
    _HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def chunk(self, text: str) -> ChunkingResult:
        if not text.strip():
            return ChunkingResult(strategy=ChunkingStrategy.HEADING_AWARE)
        sections = self._HEADING_PATTERN.split(text.strip())
        chunks: list[str] = []
        buffer: list[str] = []
        buffer_len = 0
        i = 0
        while i < len(sections):
            piece = sections[i]
            if i > 0 and i + 1 < len(sections):
                heading_level = piece
                heading_text = sections[i + 1]
                content_start = i + 2
                section_text = f"{heading_level} {heading_text}"
                section_content = sections[content_start] if content_start < len(sections) else ""
                block = f"{section_text}\n{section_content}".strip()
                i = content_start + 1 if content_start < len(sections) else len(sections)
            else:
                block = piece.strip()
                i += 1
            if not block:
                continue
            block_tokens = _estimate_tokens(block)
            if block_tokens > self._max_size:
                if buffer:
                    chunks.append("\n\n".join(buffer))
                    buffer = []
                    buffer_len = 0
                words = block.split()
                for j in range(0, len(words), self._max_size):
                    chunks.append(" ".join(words[j:j + self._max_size]))
            elif buffer_len + block_tokens <= self._max_size:
                buffer.append(block)
                buffer_len += block_tokens
            else:
                chunks.append("\n\n".join(buffer))
                overlap_start = max(0, len(buffer) - self._overlap)
                buffer = buffer[overlap_start:]
                buffer_len = _estimate_tokens("\n\n".join(buffer))
                buffer.append(block)
                buffer_len += block_tokens
        if buffer:
            chunks.append("\n\n".join(buffer))
        return ChunkingResult(
            chunks=chunks,
            chunk_count=len(chunks),
            strategy=ChunkingStrategy.HEADING_AWARE,
            overlap=self._overlap,
        )


class SentenceChunker(ChunkerStrategy):
    _SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")

    def chunk(self, text: str) -> ChunkingResult:
        if not text.strip():
            return ChunkingResult(strategy=ChunkingStrategy.SENTENCE)
        sentences = self._SENTENCE_PATTERN.split(text.strip())
        chunks: list[str] = []
        buffer: list[str] = []
        buffer_len = 0
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            sent_tokens = _estimate_tokens(sent)
            if sent_tokens > self._max_size:
                if buffer:
                    chunks.append(" ".join(buffer))
                    buffer = []
                    buffer_len = 0
                words = sent.split()
                for i in range(0, len(words), self._max_size):
                    chunks.append(" ".join(words[i:i + self._max_size]))
            elif buffer_len + sent_tokens <= self._max_size:
                buffer.append(sent)
                buffer_len += sent_tokens
            else:
                chunks.append(" ".join(buffer))
                overlap_start = max(0, len(buffer) - self._overlap)
                buffer = buffer[overlap_start:]
                buffer_len = _estimate_tokens(" ".join(buffer))
                buffer.append(sent)
                buffer_len += sent_tokens
        if buffer:
            chunks.append(" ".join(buffer))
        return ChunkingResult(
            chunks=chunks,
            chunk_count=len(chunks),
            strategy=ChunkingStrategy.SENTENCE,
            overlap=self._overlap,
        )


class ChunkerFactory:
    _CHUNKER_MAP: dict[ChunkingStrategy, type[ChunkerStrategy]] = {
        ChunkingStrategy.FIXED_SIZE: FixedSizeChunker,
        ChunkingStrategy.SLIDING_WINDOW: SlidingWindowChunker,
        ChunkingStrategy.PARAGRAPH: ParagraphChunker,
        ChunkingStrategy.HEADING_AWARE: HeadingAwareChunker,
        ChunkingStrategy.SENTENCE: SentenceChunker,
    }

    @classmethod
    def create(
        cls,
        strategy: ChunkingStrategy,
        max_size: int = 2000,
        overlap: int = 200,
    ) -> ChunkerStrategy:
        chunker_cls = cls._CHUNKER_MAP.get(strategy)
        if chunker_cls is None:
            raise EmbeddingChunkingError(f"Unsupported chunking strategy: {strategy.value}")
        return chunker_cls(max_size=max_size, overlap=overlap)
