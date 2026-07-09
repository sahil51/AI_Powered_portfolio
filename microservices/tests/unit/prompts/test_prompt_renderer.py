import pytest

from application.prompts.exceptions import PromptRenderError
from application.prompts.renderer import PromptRenderer


class TestPromptRenderer:
    def setup_method(self):
        self.renderer = PromptRenderer(strict=True)

    def test_render_simple(self):
        result = self.renderer.render("Hello {{name}}", {"name": "World"})
        assert result == "Hello World"

    def test_render_multiple(self):
        result = self.renderer.render("{{a}} and {{b}}", {"a": "1", "b": "2"})
        assert result == "1 and 2"

    def test_render_missing_raises_in_strict_mode(self):
        with pytest.raises(PromptRenderError):
            self.renderer.render("Hello {{name}}", {})

    def test_render_missing_skips_in_non_strict(self):
        renderer = PromptRenderer(strict=False)
        result = renderer.render("Hello {{name}}", {})
        assert result == "Hello "

    def test_extract_variables(self):
        vars = self.renderer.extract_variables("{{a}} and {{b}} and {{a}}")
        assert sorted(vars) == ["a", "b"]

    def test_validate_variables(self):
        errors = self.renderer.validate_variables("{{a}}", {"a", "b"})
        assert len(errors) == 1
        assert "Missing" in errors[0]

    def test_validate_variables_extra(self):
        errors = self.renderer.validate_variables("{{a}} {{c}}", {"a"})
        assert len(errors) == 1
        assert "Unexpected" in errors[0]

    def test_validate_variables_clean(self):
        errors = self.renderer.validate_variables("{{a}}", {"a"})
        assert errors == []

    def test_none_value(self):
        result = self.renderer.render("Hello {{name}}", {"name": None})
        assert result == "Hello "
