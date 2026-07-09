from application.response_validation.sanitizer import ResponseSanitizer


class TestResponseSanitizer:
    def setup_method(self):
        self.sanitizer = ResponseSanitizer()

    def test_sanitize_clean_text(self):
        result = self.sanitizer.sanitize("Hello world")
        assert result == "Hello world"

    def test_sanitize_redacts_email(self):
        result = self.sanitizer.sanitize("Email: test@example.com")
        assert "[REDACTED]" in result
        assert "test@example.com" not in result

    def test_sanitize_redacts_bearer_token(self):
        result = self.sanitizer.sanitize("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9")
        assert "[REDACTED]" in result

    def test_sanitize_removes_control_chars(self):
        result = self.sanitizer.sanitize("hello\x00world\x01test")
        assert "hello" in result
        assert "world" in result
        assert "\x00" not in result
        assert "\x01" not in result

    def test_sanitize_preserves_newlines(self):
        result = self.sanitizer.sanitize("line1\nline2\r\nline3")
        assert "\n" in result
