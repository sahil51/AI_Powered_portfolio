from application.ai.models import (
    CompletionRequest,
    CompletionResponse,
    ModelCapabilities,
    ModelInfo,
    ProviderInfo,
    StreamChunk,
    Usage,
)


class TestUsage:
    def test_usage_defaults(self):
        usage = Usage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0
        assert usage.cost == 0.0

    def test_usage_addition(self):
        u1 = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30, cost=0.01)
        u2 = Usage(prompt_tokens=5, completion_tokens=10, total_tokens=15, cost=0.005)
        u3 = u1 + u2
        assert u3.prompt_tokens == 15
        assert u3.completion_tokens == 30
        assert u3.total_tokens == 45
        assert u3.cost == 0.015


class TestCompletionRequest:
    def test_defaults(self):
        req = CompletionRequest()
        assert req.temperature == 0.7
        assert req.max_tokens == 2048
        assert req.timeout == 30.0
        assert not req.stream

    def test_to_messages_with_system_prompt(self):
        req = CompletionRequest(system_prompt="You are a helper", messages=[{"role": "user", "content": "hi"}])
        msgs = req.to_messages()
        assert len(msgs) == 2
        assert msgs[0] == {"role": "system", "content": "You are a helper"}
        assert msgs[1] == {"role": "user", "content": "hi"}

    def test_to_messages_without_system_prompt(self):
        req = CompletionRequest(messages=[{"role": "user", "content": "hi"}])
        msgs = req.to_messages()
        assert len(msgs) == 1
        assert msgs[0] == {"role": "user", "content": "hi"}


class TestCompletionResponse:
    def test_defaults(self):
        resp = CompletionResponse(content="hello")
        assert resp.content == "hello"
        assert resp.model == ""
        assert resp.finish_reason == ""
        assert resp.provider == ""


class TestStreamChunk:
    def test_defaults(self):
        chunk = StreamChunk()
        assert chunk.content == ""
        assert chunk.finish_reason is None
        assert chunk.model == ""
        assert chunk.usage is None


class TestModelCapabilities:
    def test_has(self):
        caps = ModelCapabilities(supports_streaming=True, supports_json_mode=False)
        assert caps.has("completion")
        assert caps.has("streaming")
        assert not caps.has("json_mode")
        assert not caps.has("embeddings")


class TestModelInfo:
    def test_defaults(self):
        info = ModelInfo(id="test-model")
        assert info.id == "test-model"
        assert info.provider == ""
        assert info.healthy


class TestProviderInfo:
    def test_defaults(self):
        info = ProviderInfo(name="test-provider")
        assert info.name == "test-provider"
        assert info.healthy
