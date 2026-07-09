from application.ai.models import Usage
from application.pipeline.models import (
    PipelineConfiguration,
    PipelineContext,
    PipelineResult,
    PipelineStage,
    PipelineStageResult,
)


class TestPipelineModels:
    def test_pipeline_configuration_defaults(self):
        config = PipelineConfiguration()
        assert config.default_provider is None
        assert config.default_prompt_name == "system.system"
        assert config.max_retries == 3
        assert config.fallback_enabled
        assert not config.streaming_enabled
        assert config.timeout == 60.0
        assert config.max_output_tokens == 2048
        assert config.temperature == 0.7
        assert config.top_p == 1.0
        assert config.budget_validation
        assert config.response_validation
        assert config.post_processing

    def test_pipeline_context_defaults(self):
        ctx = PipelineContext(conversation_id="conv-1", user_id="user-1")
        assert ctx.conversation_id == "conv-1"
        assert ctx.user_id == "user-1"
        assert ctx.session_id == ""
        assert ctx.prompt_name == "system.system"
        assert ctx.streaming is False
        assert ctx.correlation_id is None

    def test_pipeline_context_resolve(self):
        ctx = PipelineContext(conversation_id="c1", user_id="u1")
        assert ctx.resolve_temperature() == 0.7
        assert ctx.resolve_temperature(0.5) == 0.5
        ctx.temperature = 0.3
        assert ctx.resolve_temperature() == 0.3
        assert ctx.resolve_max_tokens() == 2048
        ctx.max_tokens = 4096
        assert ctx.resolve_max_tokens() == 4096
        assert ctx.resolve_top_p() == 1.0
        ctx.top_p = 0.9
        assert ctx.resolve_top_p() == 0.9

    def test_pipeline_stage_result(self):
        r = PipelineStageResult(stage=PipelineStage.VALIDATE_INPUT, success=True, latency_ms=10.5)
        assert r.stage == PipelineStage.VALIDATE_INPUT
        assert r.success
        assert r.latency_ms == 10.5
        assert r.error is None
        assert r.data == {}

    def test_pipeline_result_defaults(self):
        usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        r = PipelineResult(
            content="Hello",
            provider="test",
            model="test-model",
            latency_ms=100.0,
            token_usage=usage,
            estimated_cost=0.002,
            finish_reason="stop",
        )
        assert r.content == "Hello"
        assert r.provider == "test"
        assert r.token_usage.total_tokens == 30
        assert r.estimated_cost == 0.002
        assert r.finish_reason == "stop"
        assert r.warnings == []
        assert r.stage_results == []
        assert r.streaming is False

    def test_pipeline_stage_enum_values(self):
        assert PipelineStage.VALIDATE_INPUT.value == "validate_input"
        assert PipelineStage.BUILD_CONTEXT.value == "build_context"
        assert PipelineStage.GENERATE.value == "generate"
        assert PipelineStage.POST_PROCESS.value == "post_process"
        assert PipelineStage.COLLECT_METRICS.value == "collect_metrics"
