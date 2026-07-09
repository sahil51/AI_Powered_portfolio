from datetime import timedelta

from domain.agent.policies import AgentPolicies, default_agent_policies


class TestAgentPolicies:
    def test_default_policies(self):
        policies = default_agent_policies
        assert policies.max_execution_time == timedelta(minutes=30)
        assert policies.max_retries == 3
        assert policies.max_checkpoints == 10
        assert policies.max_concurrent_agents == 100
        assert policies.enable_heartbeat
        assert policies.enable_recovery

    def test_execution_time_exceeded(self):
        policies = AgentPolicies(max_execution_time=timedelta(seconds=10))
        assert policies.execution_time_exceeded(timedelta(seconds=15))
        assert not policies.execution_time_exceeded(timedelta(seconds=5))

    def test_pause_duration_exceeded(self):
        policies = AgentPolicies(max_pause_duration=timedelta(hours=1))
        assert policies.pause_duration_exceeded(timedelta(hours=2))
        assert not policies.pause_duration_exceeded(timedelta(minutes=30))

    def test_retry_allowed(self):
        policies = AgentPolicies(max_retries=3)
        assert policies.retry_allowed(0)
        assert policies.retry_allowed(2)
        assert not policies.retry_allowed(3)
        assert not policies.retry_allowed(5)

    def test_idle_exceeded(self):
        policies = AgentPolicies(idle_timeout=timedelta(minutes=5))
        assert policies.idle_exceeded(timedelta(minutes=10))
        assert not policies.idle_exceeded(timedelta(minutes=3))

    def test_error_limit_exceeded(self):
        policies = AgentPolicies(max_error_count=5)
        assert policies.error_limit_exceeded(5)
        assert policies.error_limit_exceeded(10)
        assert not policies.error_limit_exceeded(3)

    def test_should_send_heartbeat(self):
        policies = AgentPolicies(enable_heartbeat=True, heartbeat_interval=timedelta(seconds=30))
        assert policies.should_send_heartbeat(timedelta(seconds=35))
        assert not policies.should_send_heartbeat(timedelta(seconds=10))
        policies_no_hb = AgentPolicies(enable_heartbeat=False)
        assert not policies_no_hb.should_send_heartbeat(timedelta(seconds=60))
