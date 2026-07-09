import json

from application.response_validation.formatter import ResponseFormatter


class TestResponseFormatter:
    def setup_method(self):
        self.formatter = ResponseFormatter()

    def test_format_plain(self):
        result = self.formatter.format_plain("  hello  ")
        assert result == "hello"

    def test_format_markdown(self):
        result = self.formatter.format_markdown("# Hello\n\n\n\nWorld")
        assert result == "# Hello\n\nWorld"

    def test_format_json_pretty(self):
        result = self.formatter.format_json('{"key": "value"}')
        parsed = json.loads(result)
        assert parsed["key"] == "value"

    def test_format_json_non_json(self):
        result = self.formatter.format_json("plain text")
        assert result == "plain text"

    def test_format_json_invalid(self):
        result = self.formatter.format_json("{invalid")
        assert result == "{invalid"

    def test_format_json_compact(self):
        result = self.formatter.format_json('{"key": "value"}', pretty=False)
        assert '"key": "value"' in result

    def test_inject_citation_with_placeholder(self):
        result = self.formatter.inject_citation("Some text {{citation_placeholder}}", 1, "Source")
        assert "[^1]: Source" in result

    def test_inject_citation_without_placeholder(self):
        result = self.formatter.inject_citation("Some text", 1, "Source")
        assert "[^1]: Source" in result

    def test_inject_metadata(self):
        result = self.formatter.inject_metadata("Hello {{name}}!", {"name": "World"})
        assert result == "Hello World!"
