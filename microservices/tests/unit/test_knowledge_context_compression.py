from __future__ import annotations

from unittest.mock import MagicMock, patch

from application.knowledge_context.compressor import KnowledgeContextCompressor
from application.knowledge_context.models import CompressionStrategy


class TestKnowledgeContextCompressor:
    def setup_method(self) -> None:
        self.compressor = KnowledgeContextCompressor()

    def test_compress_under_max_tokens_returns_unchanged(self):
        text = "short text"
        result, saved = self.compressor.compress(text, CompressionStrategy.TRUNCATE, 1000)
        assert result == text
        assert saved == 0

    def test_truncate_with_tokenizer_available(self):
        mock_enc = MagicMock()
        mock_enc.encode.return_value = list(range(50))
        mock_enc.decode.return_value = "truncated content"
        with patch("application.knowledge_context.compressor.tiktoken.get_encoding", return_value=mock_enc):
            compressor = KnowledgeContextCompressor()
            text = "word " * 50
            result, saved = compressor.compress(text, CompressionStrategy.TRUNCATE, 10)
            assert saved > 0

    def test_truncate_fallback_when_tokenizer_none(self):
        compressor = KnowledgeContextCompressor()
        compressor._tokenizer = None
        text = "word " * 50
        result, saved = compressor.compress(text, CompressionStrategy.TRUNCATE, 10)
        assert saved > 0
        assert len(result.split()) <= 10

    def test_extract_section_based_extraction(self):
        text = "# Introduction\nSome intro content\n# Details\nMore detailed content here\n# Conclusion\nFinal wrap up"
        result, saved = self.compressor.compress(text, CompressionStrategy.EXTRACT, 5)
        assert saved > 0

    def test_extract_single_section_falls_back_to_truncate(self):
        text = "No section headings here just a long plain text block " * 50
        result, saved = self.compressor.compress(text, CompressionStrategy.EXTRACT, 10)
        assert saved > 0

    def test_prioritize_headings_and_content(self):
        text = "# Main Heading\nsome lower priority line\n**Bold important text**\nSHOUTING LINE\nlow priority detail"
        result, saved = self.compressor.compress(text, CompressionStrategy.PRIORITIZE, 15)
        assert "# Main Heading" in result
        assert "**Bold important text**" in result
        assert "SHOUTING LINE" in result

    def test_prioritize_removes_low_priority_when_over_budget(self):
        text = "# Heading\nshort\nsome very long line that should be medium priority because it exceeds one hundred characters in length for testing prioritization strategy"
        result, saved = self.compressor.compress(text, CompressionStrategy.PRIORITIZE, 3)
        assert saved >= 0

    def test_estimate_tokens_with_tokenizer(self):
        mock_enc = MagicMock()
        mock_enc.encode.return_value = [1, 2, 3]
        with patch("application.knowledge_context.compressor.tiktoken.get_encoding", return_value=mock_enc):
            compressor = KnowledgeContextCompressor()
            tokens = compressor.estimate_tokens("hello world")
            assert tokens == 3

    def test_estimate_tokens_without_tokenizer(self):
        compressor = KnowledgeContextCompressor()
        compressor._tokenizer = None
        tokens = compressor.estimate_tokens("hello world")
        assert tokens == 2

    def test_estimate_tokens_empty_string(self):
        assert self.compressor.estimate_tokens("") == 0

    def test_truncate_under_max_tokens_returns_unchanged(self):
        text = "short"
        result, saved = self.compressor._truncate(text, 100)
        assert result == text
        assert saved == 0

    def test_truncate_with_tokenizer_under_max(self):
        mock_enc = MagicMock()
        mock_enc.encode.return_value = [1, 2]
        mock_enc.decode.return_value = "short"
        with patch("application.knowledge_context.compressor.tiktoken.get_encoding", return_value=mock_enc):
            compressor = KnowledgeContextCompressor()
            result, saved = compressor._truncate("short", 100)
            assert result == "short"
            assert saved == 0

    def test_truncate_without_tokenizer_under_max(self):
        compressor = KnowledgeContextCompressor()
        compressor._tokenizer = None
        result, saved = compressor._truncate("short", 100)
        assert result == "short"
        assert saved == 0

    def test_extract_first_section_already_over_max(self):
        text = "# " + "A" * 200
        result, saved = self.compressor.compress(text, CompressionStrategy.EXTRACT, 5)
        assert saved >= 0

    def test_prioritize_empty_text(self):
        result, saved = self.compressor.compress("", CompressionStrategy.PRIORITIZE, 100)
        assert result == ""
        assert saved == 0

    def test_summarize_falls_back_to_truncate(self):
        text = "word " * 100
        result, saved = self.compressor.compress(text, CompressionStrategy.SUMMARIZE, 10)
        assert saved > 0
