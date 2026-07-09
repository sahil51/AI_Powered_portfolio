from application.prompts.metadata import PromptMetadata, PromptStatus
from application.prompts.validator import PromptValidator


class TestPromptValidator:
    def setup_method(self):
        self.validator = PromptValidator()

    def test_validate_metadata_valid(self):
        meta = PromptMetadata(name="test", category="system", version="1.0.0", status=PromptStatus.ACTIVE)
        errors = self.validator.validate_metadata(meta)
        assert errors == []

    def test_validate_metadata_missing_name(self):
        meta = PromptMetadata()
        errors = self.validator.validate_metadata(meta)
        assert "name is required" in str(errors)

    def test_validate_content_empty(self):
        errors = self.validator.validate_content("")
        assert "empty" in str(errors)

    def test_validate_content_valid(self):
        errors = self.validator.validate_content("This is a valid prompt template with enough length.")
        assert errors == []

    def test_validate_syntax_valid(self):
        errors = self.validator.validate_syntax("Hello {{name}}")
        assert errors == []

    def test_validate_syntax_invalid(self):
        errors = self.validator.validate_syntax("Hello {{invalid-var}}")
        assert len(errors) > 0
        assert "Invalid variable syntax: {{invalid-var}}" in errors
