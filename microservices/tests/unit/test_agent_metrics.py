
from application.agent.metrics import AgentMetrics, AgentMetricsCollector, RuntimeMetrics
from application.agent.models import AgentStatistics


class TestAgentMetrics:
    def test_default_metrics(self):
        metrics = AgentMetrics(agent_id="test-1")
        assert metrics.total_executions == 0
        assert metrics.avg_latency_ms == 0.0
        assert metrics.success_rate == 1.0
        assert metrics.failure_rate == 0.0

    def test_avg_latency_with_executions(self):
        metrics = AgentMetrics(agent_id="test-1", total_executions=5, total_latency_ms=1000.0)
        assert metrics.avg_latency_ms == 200.0

    def test_success_rate(self):
        metrics = AgentMetrics(agent_id="test-1", total_executions=10, successful_executions=8, failed_executions=2)
        assert metrics.success_rate == 0.8
        assert metrics.failure_rate == 0.2

    def test_merge(self):
        m1 = AgentMetrics(agent_id="test-1", total_executions=5, successful_executions=4,
                          failed_executions=1, total_latency_ms=500.0, pause_count=2)
        m2 = AgentMetrics(agent_id="test-2", total_executions=3, successful_executions=2,
                          failed_executions=1, total_latency_ms=300.0, resume_count=1)
        m1.merge(m2)
        assert m1.total_executions == 8
        assert m1.successful_executions == 6
        assert m1.failed_executions == 2
        assert m1.total_latency_ms == 800.0

    def test_from_statistics(self):
        stats = AgentStatistics(total_executions=10, successful_executions=7,
                                failed_executions=3, total_latency_ms=2000.0,
                                retry_count=2, heartbeat_count=5)
        metrics = AgentMetrics(agent_id="test-1")
        metrics.from_statistics(stats)
        assert metrics.total_executions == 10
        assert metrics.successful_executions == 7
        assert metrics.failed_executions == 3
        assert metrics.total_latency_ms == 2000.0
        assert metrics.retry_count == 2
        assert metrics.heartbeat_count == 5

    def test_min_max_latency(self):
        m1 = AgentMetrics(agent_id="test-1")
        m2 = AgentMetrics(agent_id="test-2", min_latency_ms=100.0, max_latency_ms=500.0)
        m1.merge(m2)
        assert m1.min_latency_ms == 100.0
        assert m1.max_latency_ms == 500.0


class TestAgentMetricsCollector:
    def setup_method(self):
        self.collector = AgentMetricsCollector()

    def test_record_execution_success(self):
        self.collector.record_execution("agent-1", True, 150.0)
        metrics = self.collector.get_metrics("agent-1")
        assert metrics.total_executions == 1
        assert metrics.successful_executions == 1
        assert metrics.total_latency_ms == 150.0
        assert self.collector.runtime.total_executions == 1

    def test_record_execution_failure(self):
        self.collector.record_execution("agent-1", False, 200.0)
        metrics = self.collector.get_metrics("agent-1")
        assert metrics.total_executions == 1
        assert metrics.failed_executions == 1
        assert self.collector.runtime.total_errors == 1

    def test_record_multiple_agents(self):
        self.collector.record_execution("agent-1", True, 100.0)
        self.collector.record_execution("agent-2", True, 200.0)
        all_metrics = self.collector.get_metrics()
        assert len(all_metrics) == 2

    def test_record_state_transition(self):
        self.collector.record_state_transition("agent-1", "started")
        self.collector.record_state_transition("agent-1", "started")
        metrics = self.collector.get_metrics("agent-1")
        assert metrics.state_transitions["started"] == 2

    def test_record_retry(self):
        self.collector.record_retry("agent-1")
        metrics = self.collector.get_metrics("agent-1")
        assert metrics.retry_count == 1
        assert self.collector.runtime.total_retries == 1

    def test_record_timeout(self):
        self.collector.record_timeout("agent-1")
        metrics = self.collector.get_metrics("agent-1")
        assert metrics.timeout_count == 1

    def test_record_heartbeat(self):
        self.collector.record_heartbeat("agent-1")
        metrics = self.collector.get_metrics("agent-1")
        assert metrics.heartbeat_count == 1

    def test_record_checkpoint(self):
        self.collector.record_checkpoint("agent-1")
        metrics = self.collector.get_metrics("agent-1")
        assert metrics.checkpoint_count == 1
        assert self.collector.runtime.total_checkpoints == 1

    def test_record_recovery(self):
        self.collector.record_recovery("agent-1")
        metrics = self.collector.get_metrics("agent-1")
        assert metrics.recovery_count == 1

    def test_runtime_uptime(self):
        runtime = self.collector.runtime
        assert runtime.uptime_seconds >= 0

    def test_reset_agent(self):
        self.collector.record_execution("agent-1", True, 100.0)
        self.collector.reset("agent-1")
        metrics = self.collector.get_metrics("agent-1")
        assert metrics.total_executions == 0

    def test_reset_all(self):
        self.collector.record_execution("agent-1", True, 100.0)
        self.collector.reset()
        assert len(self.collector.get_metrics()) == 0

    def test_runtime_defaults(self):
        runtime = RuntimeMetrics()
        assert runtime.total_agents == 0
        assert runtime.error_rate == 0.0
