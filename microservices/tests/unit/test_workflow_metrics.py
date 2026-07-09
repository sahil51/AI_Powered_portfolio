
from application.workflow.metrics import WorkflowEngineMetrics, WorkflowMetrics, WorkflowMetricsCollector


class TestWorkflowMetrics:
    def test_default_metrics(self):
        metrics = WorkflowMetrics(workflow_id="wf-1")
        assert metrics.total_executions == 0
        assert metrics.avg_latency_ms == 0.0
        assert metrics.success_rate == 1.0
        assert metrics.failure_rate == 0.0

    def test_avg_latency(self):
        metrics = WorkflowMetrics(workflow_id="wf-1", total_executions=4, total_latency_ms=800.0)
        assert metrics.avg_latency_ms == 200.0

    def test_success_rate(self):
        metrics = WorkflowMetrics(workflow_id="wf-1", total_executions=10, successful_executions=7, failed_executions=3)
        assert metrics.success_rate == 0.7
        assert metrics.failure_rate == 0.3

    def test_merge(self):
        m1 = WorkflowMetrics(workflow_id="wf-1", total_executions=5, successful_executions=4,
                             failed_executions=1, total_latency_ms=500.0, retry_count=2)
        m2 = WorkflowMetrics(workflow_id="wf-2", total_executions=3, successful_executions=2,
                             failed_executions=1, total_latency_ms=300.0, recovery_count=1)
        m1.merge(m2)
        assert m1.total_executions == 8
        assert m1.successful_executions == 6
        assert m1.failed_executions == 2
        assert m1.total_latency_ms == 800.0
        assert m1.retry_count == 2
        assert m1.recovery_count == 1

    def test_min_max_latency(self):
        m1 = WorkflowMetrics(workflow_id="wf-1")
        m2 = WorkflowMetrics(workflow_id="wf-2", min_latency_ms=50.0, max_latency_ms=500.0)
        m1.merge(m2)
        assert m1.min_latency_ms == 50.0
        assert m1.max_latency_ms == 500.0

    def test_engine_metrics_defaults(self):
        metrics = WorkflowEngineMetrics()
        assert metrics.total_engines == 0
        assert metrics.total_executions == 0
        assert metrics.uptime_seconds == 0.0


class TestWorkflowMetricsCollector:
    def setup_method(self):
        self.collector = WorkflowMetricsCollector()

    def test_record_execution_success(self):
        self.collector.record_execution("wf-1", True, 100.0)
        metrics = self.collector.get_metrics("wf-1")
        assert metrics.total_executions == 1
        assert metrics.successful_executions == 1
        assert metrics.total_latency_ms == 100.0
        assert self.collector.engine.total_executions == 1

    def test_record_execution_failure(self):
        self.collector.record_execution("wf-1", False, 200.0)
        metrics = self.collector.get_metrics("wf-1")
        assert metrics.total_executions == 1
        assert metrics.failed_executions == 1
        assert self.collector.engine.total_errors == 1

    def test_record_multiple_workflows(self):
        self.collector.record_execution("wf-1", True, 100.0)
        self.collector.record_execution("wf-2", True, 200.0)
        all_metrics = self.collector.get_metrics()
        assert len(all_metrics) == 2

    def test_record_retry(self):
        self.collector.record_retry("wf-1")
        metrics = self.collector.get_metrics("wf-1")
        assert metrics.retry_count == 1
        assert self.collector.engine.total_retries == 1

    def test_record_recovery(self):
        self.collector.record_recovery("wf-1")
        metrics = self.collector.get_metrics("wf-1")
        assert metrics.recovery_count == 1

    def test_record_checkpoint(self):
        self.collector.record_checkpoint("wf-1")
        metrics = self.collector.get_metrics("wf-1")
        assert metrics.checkpoint_count == 1

    def test_engine_uptime(self):
        engine = self.collector.engine
        assert engine.uptime_seconds >= 0

    def test_reset_workflow(self):
        self.collector.record_execution("wf-1", True, 100.0)
        self.collector.reset("wf-1")
        metrics = self.collector.get_metrics("wf-1")
        assert metrics.total_executions == 0

    def test_reset_all(self):
        self.collector.record_execution("wf-1", True, 100.0)
        self.collector.reset()
        assert len(self.collector.get_metrics()) == 0
