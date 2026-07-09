from application.context_builder.compression import ContextCompressionPolicy, DeduplicationStrategy, TruncationStrategy


class TestDeduplicationStrategy:
    def test_no_dedup_when_disabled(self):
        strategy = DeduplicationStrategy(enabled=False)
        items = [{"content": "a"}, {"content": "a"}]
        assert len(strategy.deduplicate(items)) == 2

    def test_deduplicates(self):
        strategy = DeduplicationStrategy(enabled=True)
        items = [{"content": "a"}, {"content": "a"}, {"content": "b"}]
        result = strategy.deduplicate(items)
        assert len(result) == 2

    def test_max_duplicates(self):
        strategy = DeduplicationStrategy(enabled=True, max_duplicates=2)
        items = [{"content": "a"}, {"content": "a"}, {"content": "a"}]
        result = strategy.deduplicate(items)
        assert len(result) == 2


class TestTruncationStrategy:
    def test_no_truncation_when_disabled(self):
        strategy = TruncationStrategy(enabled=False)
        data = {"content": "hello world"}
        result = strategy.truncate(data, len)
        assert result["content"] == "hello world"

    def test_truncates_long_content(self):
        strategy = TruncationStrategy(enabled=True, max_tokens=2)
        data = {"content": "hello world this is long"}
        result = strategy.truncate(data, len)
        assert "[truncated]" in result["content"]


class TestContextCompressionPolicy:
    def test_compress_no_token_counter(self):
        policy = ContextCompressionPolicy()
        data = {"content": "hello world"}
        result = policy.compress(data)
        assert result["content"] == "hello world"

    def test_compress_with_dedup(self):
        policy = ContextCompressionPolicy()
        data = {"messages": [{"content": "a"}, {"content": "a"}]}
        result = policy.compress(data)
        assert len(result["messages"]) == 1
