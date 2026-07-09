from application.pipeline.metrics import PipelineMetrics


class TestPipelineMetrics:
    def test_defaults(self):
        m = PipelineMetrics()
        assert m.total_pipelines == 0
        assert m.avg_latency_ms == 0.0
        assert m.success_rate == 1.0
        assert m.failure_rate == 0.0

    def test_record_pipeline_success(self):
        m = PipelineMetrics()
        m.record_pipeline(success=True, latency_ms=100.0, tokens=50, cost=0.001)
        assert m.total_pipelines == 1
        assert m.successful_pipelines == 1
        assert m.failed_pipelines == 0
        assert m.avg_latency_ms == 100.0
        assert m.success_rate == 1.0

    def test_record_pipeline_failure(self):
        m = PipelineMetrics()
        m.record_pipeline(success=False, latency_ms=50.0)
        assert m.total_pipelines == 1
        assert m.successful_pipelines == 0
        assert m.failed_pipelines == 1
        assert m.failure_rate == 1.0

    def test_record_stage(self):
        m = PipelineMetrics()
        m.record_stage("build_context", 25.0)
        m.record_stage("generate", 150.0)
        m.record_stage("build_context", 15.0)
        assert m.stage_latency["build_context"] == 40.0
        assert m.stage_latency["generate"] == 150.0

    def test_merge(self):
        a = PipelineMetrics()
        a.record_pipeline(success=True, latency_ms=100.0)
        a.record_stage("generate", 50.0)

        b = PipelineMetrics()
        b.record_pipeline(success=False, latency_ms=200.0)
        b.record_stage("validate", 10.0)

        a.merge(b)
        assert a.total_pipelines == 2
        assert a.successful_pipelines == 1
        assert a.failed_pipelines == 1
        assert a.total_latency_ms == 300.0
        assert a.stage_latency["generate"] == 50.0
        assert a.stage_latency["validate"] == 10.0
