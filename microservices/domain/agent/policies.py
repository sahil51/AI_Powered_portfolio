from dataclasses import dataclass
from datetime import timedelta


@dataclass
class AgentPolicies:
    max_execution_time: timedelta = timedelta(minutes=30)
    max_pause_duration: timedelta = timedelta(hours=24)
    max_retries: int = 3
    retry_delay: timedelta = timedelta(seconds=10)
    heartbeat_interval: timedelta = timedelta(seconds=30)
    max_checkpoints: int = 10
    idle_timeout: timedelta = timedelta(minutes=5)
    max_concurrent_agents: int = 100
    enable_heartbeat: bool = True
    enable_checkpoint: bool = True
    enable_recovery: bool = True
    default_timeout: timedelta = timedelta(minutes=5)
    priority_queue: bool = True
    max_error_count: int = 10

    def execution_time_exceeded(self, elapsed: timedelta) -> bool:
        return elapsed > self.max_execution_time

    def pause_duration_exceeded(self, elapsed: timedelta) -> bool:
        return elapsed > self.max_pause_duration

    def retry_allowed(self, attempt: int) -> bool:
        return attempt < self.max_retries

    def idle_exceeded(self, elapsed: timedelta) -> bool:
        return elapsed > self.idle_timeout

    def error_limit_exceeded(self, error_count: int) -> bool:
        return error_count >= self.max_error_count

    def should_send_heartbeat(self, elapsed: timedelta) -> bool:
        return self.enable_heartbeat and elapsed >= self.heartbeat_interval


default_agent_policies = AgentPolicies()
