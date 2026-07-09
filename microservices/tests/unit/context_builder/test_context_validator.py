import pytest

from application.context_builder.budget import ContextBudget
from application.context_builder.models import BuiltContext, ContextLayerResult, ContextMetadata
from application.context_builder.validator import ContextValidationError, ContextValidator


class TestContextValidator:
    def setup_method(self):
        self.validator = ContextValidator()

    def test_validate_budget_valid(self):
        budget = ContextBudget(max_tokens=8192, reserved_tokens=1024, output_tokens=2048)
        errors = self.validator.validate_budget(budget)
        assert errors == []

    def test_validate_budget_max_tokens_zero(self):
        budget = ContextBudget(max_tokens=0)
        errors = self.validator.validate_budget(budget)
        assert "max_tokens must be positive" in errors

    def test_validate_budget_reserved_exceeds(self):
        budget = ContextBudget(max_tokens=100, reserved_tokens=200, output_tokens=0)
        errors = self.validator.validate_budget(budget)
        assert "reserved + output tokens exceed max_tokens" in errors

    def test_validate_layer_result_valid(self):
        result = ContextLayerResult(name="test", tokens=100)
        errors = self.validator.validate_layer_result(result)
        assert errors == []

    def test_validate_layer_result_empty_name(self):
        result = ContextLayerResult(name="", tokens=100)
        errors = self.validator.validate_layer_result(result)
        assert "layer name must not be empty" in errors

    def test_validate_built_context_valid(self):
        context = BuiltContext(
            layers={"system": ContextLayerResult(name="system")},
            metadata=ContextMetadata(total_tokens=10, max_tokens=100),
        )
        errors = self.validator.validate_built_context(context)
        assert errors == []

    def test_raise_if_invalid(self):
        context = BuiltContext(layers={}, metadata=ContextMetadata(total_tokens=0, max_tokens=100))
        with pytest.raises(ContextValidationError):
            self.validator.raise_if_invalid(context)
