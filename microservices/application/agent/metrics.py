from __future__ import annotations

import time
from dataclasses import dataclass, field

from application.agent.models import AgentStatistics


@dataclass
class AgentMetrics:
    agent_id: str = ""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    pause_count: int = 0
    resume_count: int = 0
    cancel_count: int = 0
    retry_count: int = 0
    timeout_count: int = 0
    heartbeat_count: int = 0
    checkpoint_count: int = 0
    recovery_count: int = 0
    last_execution_time: float = 0.0
    state_transitions: dict[str, int] = field(default_factory=dict)

    @property
    def avg_latency_ms(self) -> float:
        if self.total_executions == 0:
            return 0.0
        return self.total_latency_ms / self.total_executions

    @property
    def success_rate(self) -> float:
        if self.total_executions == 0:
            return 1.0
        return self.successful_executions / self.total_executions

    @property
    def failure_rate(self) -> float:
        if self.total_executions == 0:
            return 0.0
        return self.failed_executions / self.total_executions

    def merge(self, other: AgentMetrics) -> None:
        self.total_executions += other.total_executions
        self.successful_executions += other.successful_executions
        self.failed_executions += other.failed_executions
        self.total_latency_ms += other.total_latency_ms
        if other.min_latency_ms > 0:
            self.min_latency_ms = (
                min(self.min_latency_ms, other.min_latency_ms)
                if self.min_latency_ms > 0
                else other.min_latency_ms
            )
        self.max_latency_ms = max(self.max_latency_ms, other.max_latency_ms)
        self.pause_count += other.pause_count
        self.resume_count += other.resume_count
        self.cancel_count += other.cancel_count
        self.retry_count += other.retry_count
        self.timeout_count += other.timeout_count
        self.heartbeat_count += other.heartbeat_count
        self.checkpoint_count += other.checkpoint_count
        self.recovery_count += other.recovery_count
        if other.last_execution_time > self.last_execution_time:
            self.last_execution_time = other.last_execution_time
        for state, count in other.state_transitions.items():
            self.state_transitions[state] = self.state_transitions.get(state, 0) + count

    def from_statistics(self, statistics: AgentStatistics) -> None:
        self.total_executions = statistics.total_executions
        self.successful_executions = statistics.successful_executions
        self.failed_executions = statistics.failed_executions
        self.total_latency_ms = statistics.total_latency_ms
        self.pause_count = statistics.pause_count
        self.resume_count = statistics.resume_count
        self.cancel_count = statistics.cancel_count
        self.retry_count = statistics.retry_count
        self.timeout_count = statistics.timeout_count
        self.heartbeat_count = statistics.heartbeat_count
        self.checkpoint_count = statistics.checkpoint_count
        self.recovery_count = statistics.recovery_count
        self.last_execution_time = statistics.last_execution_time
        self.state_transitions = dict(statistics.state_transitions)


@dataclass
class RuntimeMetrics:
    total_agents: int = 0
    registered_agents: int = 0
    running_agents: int = 0
    active_sessions: int = 0
    total_executions: int = 0
    total_errors: int = 0
    total_timeouts: int = 0
    total_retries: int = 0
    total_recoveries: int = 0
    total_heartbeats: int = 0
    total_checkpoints: int = 0
    uptime_seconds: float = 0.0

    @property
    def error_rate(self) -> float:
        if self.total_executions == 0:
            return 0.0
        return self.total_errors / self.total_executions


class AgentMetricsCollector:
    def __init__(self) -> None:
        self._agent_metrics: dict[str, AgentMetrics] = {}
        self._runtime_metrics: RuntimeMetrics = RuntimeMetrics()
        self._start_time: float = time.time()

    @property
    def runtime(self) -> RuntimeMetrics:
        self._runtime_metrics.uptime_seconds = time.time() - self._start_time
        return self._runtime_metrics

    def record_execution(
        self,
        agent_id: str,
        success: bool,
        latency_ms: float,
    ) -> None:
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
        metrics = self._agent_metrics[agent_id]
        metrics.total_executions += 1
        metrics.last_execution_time = time.time()
        if success:
            metrics.successful_executions += 1
        else:
            metrics.failed_executions += 1
            self._runtime_metrics.total_errors += 1
        metrics.total_latency_ms += latency_ms
        if metrics.min_latency_ms == 0 or latency_ms < metrics.min_latency_ms:
            metrics.min_latency_ms = latency_ms
        if latency_ms > metrics.max_latency_ms:
            metrics.max_latency_ms = latency_ms
        self._runtime_metrics.total_executions += 1

    def record_state_transition(self, agent_id: str, state: str) -> None:
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
        metrics = self._agent_metrics[agent_id]
        metrics.state_transitions[state] = metrics.state_transitions.get(state, 0) + 1

    def record_retry(self, agent_id: str) -> None:
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
        self._agent_metrics[agent_id].retry_count += 1
        self._runtime_metrics.total_retries += 1

    def record_timeout(self, agent_id: str) -> None:
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
        self._agent_metrics[agent_id].timeout_count += 1
        self._runtime_metrics.total_timeouts += 1

    def record_heartbeat(self, agent_id: str) -> None:
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
        self._agent_metrics[agent_id].heartbeat_count += 1
        self._runtime_metrics.total_heartbeats += 1

    def record_checkpoint(self, agent_id: str) -> None:
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
        self._agent_metrics[agent_id].checkpoint_count += 1
        self._runtime_metrics.total_checkpoints += 1

    def record_recovery(self, agent_id: str) -> None:
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
        self._agent_metrics[agent_id].recovery_count += 1
        self._runtime_metrics.total_recoveries += 1

    def record_registration(self, agent_id: str) -> None:
        self._runtime_metrics.registered_agents += 1

    def record_running(self, agent_id: str, running: bool) -> None:
        if running:
            self._runtime_metrics.running_agents += 1
        else:
            self._runtime_metrics.running_agents = max(0, self._runtime_metrics.running_agents - 1)

    def update_agent_count(self, count: int) -> None:
        self._runtime_metrics.total_agents = count

    def get_metrics(self, agent_id: str | None = None) -> AgentMetrics | dict[str, AgentMetrics]:
        if agent_id:
            return self._agent_metrics.get(agent_id, AgentMetrics(agent_id=agent_id))
        return dict(self._agent_metrics)

    def reset(self, agent_id: str | None = None) -> None:
        if agent_id:
            self._agent_metrics.pop(agent_id, None)
        else:
            self._agent_metrics.clear()
            self._runtime_metrics = RuntimeMetrics()
            self._start_time = time.time()
