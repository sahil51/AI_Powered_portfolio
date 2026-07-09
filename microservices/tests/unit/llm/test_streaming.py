from infrastructure.llm.streaming import LiteLLMStreamHandler


class ChunkStub:
    def __init__(self, content="", finish_reason=None, model="test-model", usage=None):
        self.choices = [ChoiceStub(content, finish_reason)]
        self.model = model
        self.usage = usage


class ChoiceStub:
    def __init__(self, content="", finish_reason=None):
        self.delta = DeltaStub(content)
        self.finish_reason = finish_reason


class DeltaStub:
    def __init__(self, content=""):
        self.content = content


class TestLiteLLMStreamHandler:
    def setup_method(self):
        self.handler = LiteLLMStreamHandler()

    def test_process_chunk_with_content(self):
        chunk = ChunkStub(content="Hello")
        result = self.handler._process_chunk(chunk)
        assert result is not None
        assert result.content == "Hello"
        assert result.model == "test-model"

    def test_process_chunk_with_finish_reason(self):
        chunk = ChunkStub(content="", finish_reason="stop")
        result = self.handler._process_chunk(chunk)
        assert result is not None
        assert result.finish_reason == "stop"

    def test_process_chunk_empty_choices(self):
        chunk = type("Chunk", (), {"choices": []})()
        result = self.handler._process_chunk(chunk)
        assert result is None

    def test_process_chunk_no_choices(self):
        chunk = type("Chunk", (), {})()
        result = self.handler._process_chunk(chunk)
        assert result is None

    def test_cancel(self):
        self.handler.cancel()
        assert self.handler._cancelled
