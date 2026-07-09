from application.context_builder.metrics import ContextMetrics


class TestContextMetrics:
    def test_defaults(self):
        metrics = ContextMetrics()
        assert metrics.total_builds == 0
        assert metrics.avg_build_time_ms == 0.0
        assert metrics.avg_tokens_per_build == 0.0

    def test_record_build(self):
        metrics = ContextMetrics()
        metrics.record_build(3, 500, 100.0)
        assert metrics.total_builds == 1
        assert metrics.total_layers_built == 3
        assert metrics.total_tokens_processed == 500
        assert metrics.total_build_time_ms == 100.0

    def test_cache_hit_miss(self):
        metrics = ContextMetrics()
        metrics.record_cache_hit()
        metrics.record_cache_miss()
        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 1

    def test_compression(self):
        metrics = ContextMetrics()
        metrics.record_compression()
        assert metrics.compression_applied == 1

    def test_merge(self):
        m1 = ContextMetrics()
        m1.record_build(2, 100, 50.0)
        m2 = ContextMetrics()
        m2.record_build(3, 200, 100.0)
        m1.merge(m2)
        assert m1.total_builds == 2
        assert m1.total_layers_built == 5
        assert m1.total_tokens_processed == 300
