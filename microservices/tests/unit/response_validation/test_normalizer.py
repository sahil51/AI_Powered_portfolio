from application.response_validation.normalizer import ResponseNormalizer


class TestResponseNormalizer:
    def setup_method(self):
        self.normalizer = ResponseNormalizer()

    def test_normalize_strips_whitespace(self):
        result = self.normalizer.normalize("  hello  ")
        assert result == "hello"

    def test_normalize_collapses_newlines(self):
        result = self.normalizer.normalize("line1\n\n\n\nline2")
        assert result == "line1\n\nline2"

    def test_normalize_collapses_spaces(self):
        result = self.normalizer.normalize("hello    world")
        assert result == "hello world"

    def test_normalize_clean_formatting(self):
        result = self.normalizer.normalize("****bold****")
        assert "****" not in result

    def test_normalize_clean_carriage_returns(self):
        result = self.normalizer.normalize("line1\r\nline2\rline3")
        assert result == "line1\nline2\nline3"
