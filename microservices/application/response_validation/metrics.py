from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ResponseMetrics:
    total_validations: int = 0
    passed_validations: int = 0
    failed_validations: int = 0
    total_latency_ms: float = 0.0
    total_warnings: int = 0
    pii_detections: int = 0
    leakage_detections: int = 0
    sensitive_data_detections: int = 0
    rule_failures: dict[str, int] = field(default_factory=dict)
    last_validation_time: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        if self.total_validations == 0:
            return 0.0
        return self.total_latency_ms / self.total_validations

    @property
    def pass_rate(self) -> float:
        if self.total_validations == 0:
            return 1.0
        return self.passed_validations / self.total_validations

    def record_validation(
        self, passed: bool, latency_ms: float, warnings: int = 0,
        rule_results: dict[str, bool] | None = None,
    ) -> None:
        self.total_validations += 1
        if passed:
            self.passed_validations += 1
        else:
            self.failed_validations += 1
        self.total_latency_ms += latency_ms
        self.total_warnings += warnings
        if rule_results:
            for rule, result in rule_results.items():
                if not result:
                    self.rule_failures[rule] = self.rule_failures.get(rule, 0) + 1
        import time
        self.last_validation_time = time.time()

    def record_pii_detection(self) -> None:
        self.pii_detections += 1

    def record_leakage_detection(self) -> None:
        self.leakage_detections += 1

    def record_sensitive_data_detection(self) -> None:
        self.sensitive_data_detections += 1

    def merge(self, other: ResponseMetrics) -> None:
        self.total_validations += other.total_validations
        self.passed_validations += other.passed_validations
        self.failed_validations += other.failed_validations
        self.total_latency_ms += other.total_latency_ms
        self.total_warnings += other.total_warnings
        self.pii_detections += other.pii_detections
        self.leakage_detections += other.leakage_detections
        self.sensitive_data_detections += other.sensitive_data_detections
        for rule, count in other.rule_failures.items():
            self.rule_failures[rule] = self.rule_failures.get(rule, 0) + count
