
from application.pipeline.models import PipelineContext
from application.pipeline.validator import PipelineValidator


class TestPipelineValidator:
    def setup_method(self):
        self.validator = PipelineValidator()

    def test_validate_valid(self):
        ctx = PipelineContext(conversation_id="c1", user_id="u1", prompt_name="system.system")
        errors = self.validator.validate(ctx)
        assert errors == []

    def test_validate_missing_conversation_id(self):
        ctx = PipelineContext(conversation_id="", user_id="u1", prompt_name="system.system")
        errors = self.validator.validate(ctx)
        assert "conversation_id is required" in errors

    def test_validate_missing_user_id(self):
        ctx = PipelineContext(conversation_id="c1", user_id="", prompt_name="system.system")
        errors = self.validator.validate(ctx)
        assert "user_id is required" in errors

    def test_validate_missing_prompt_name(self):
        ctx = PipelineContext(conversation_id="c1", user_id="u1", prompt_name="")
        errors = self.validator.validate(ctx)
        assert "prompt_name is required" in errors

    def test_validate_invalid_max_tokens(self):
        ctx = PipelineContext(conversation_id="c1", user_id="u1", prompt_name="test", max_tokens=0)
        errors = self.validator.validate(ctx)
        assert "max_tokens must be >= 1" in errors

    def test_validate_invalid_temperature(self):
        ctx = PipelineContext(conversation_id="c1", user_id="u1", prompt_name="test", temperature=3.0)
        errors = self.validator.validate(ctx)
        assert "temperature must be between 0.0 and 2.0" in errors

    def test_validate_invalid_top_p(self):
        ctx = PipelineContext(conversation_id="c1", user_id="u1", prompt_name="test", top_p=1.5)
        errors = self.validator.validate(ctx)
        assert "top_p must be between 0.0 and 1.0" in errors

    def test_validate_multiple_errors(self):
        ctx = PipelineContext(conversation_id="", user_id="", prompt_name="", temperature=-1.0)
        errors = self.validator.validate(ctx)
        assert len(errors) >= 3
