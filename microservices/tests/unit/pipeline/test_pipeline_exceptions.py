
from application.pipeline.exceptions import (
    PipelineBudgetExceededError,
    PipelineConfigurationError,
    PipelineContextError,
    PipelineError,
    PipelinePromptError,
    PipelineProviderError,
    PipelineTimeoutError,
    PipelineValidationError,
)
from exceptions.base import AppError


class TestPipelineExceptions:
    def test_pipeline_error_base(self):
        err = PipelineError(message="test error", detail="detail", stage="validate")
        assert err.message == "test error"
        assert err.detail == "detail"
        assert err.stage == "validate"
        assert isinstance(err, AppError)
        assert "test error" in str(err)

    def test_pipeline_configuration_error(self):
        err = PipelineConfigurationError()
        assert err.status_code == 500
        assert "configuration" in err.message

    def test_pipeline_timeout_error(self):
        err = PipelineTimeoutError()
        assert err.status_code == 504

    def test_pipeline_validation_error(self):
        err = PipelineValidationError(detail="invalid input")
        assert err.status_code == 422
        assert err.detail == "invalid input"

    def test_pipeline_budget_exceeded_error(self):
        err = PipelineBudgetExceededError(detail="budget too low")
        assert err.status_code == 400
        assert err.detail == "budget too low"

    def test_pipeline_provider_error(self):
        err = PipelineProviderError(detail="provider unavailable")
        assert err.status_code == 503

    def test_pipeline_context_error(self):
        err = PipelineContextError(detail="conversation not found")
        assert err.status_code == 404

    def test_pipeline_prompt_error(self):
        err = PipelinePromptError(detail="prompt not found")
        assert err.status_code == 404
