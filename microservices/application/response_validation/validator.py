from __future__ import annotations

import time

from application.response_validation.models import ValidationReport
from application.response_validation.policy import ResponsePolicy
from application.response_validation.rules import ValidationRules


class ResponseValidator:
    def __init__(self, policy: ResponsePolicy | None = None) -> None:
        self._policy = policy or ResponsePolicy()
        self._rules = ValidationRules(self._policy)

    def validate(self, content: str) -> ValidationReport:
        start = time.time()
        results = self._rules.run_all(content)
        total = len(results)
        passed = sum(1 for r in results.values() if r.passed)
        failed = sum(1 for r in results.values() if not r.passed)
        warnings = sum(len(r.warnings) for r in results.values())
        elapsed = (time.time() - start) * 1000
        return ValidationReport(
            passed=failed == 0,
            results=results,
            total_checks=total,
            passed_checks=passed,
            failed_checks=failed,
            warning_checks=warnings,
            latency_ms=elapsed,
        )
