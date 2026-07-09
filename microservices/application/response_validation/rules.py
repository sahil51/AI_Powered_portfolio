from __future__ import annotations

import json
import re

from application.response_validation.models import ValidationResult
from application.response_validation.policy import ResponsePolicy


class ValidationRules:
    def __init__(self, policy: ResponsePolicy | None = None) -> None:
        self._policy = policy or ResponsePolicy()

    def check_empty(self, content: str) -> ValidationResult:
        errors: list[str] = []
        if not content or not content.strip():
            errors.append("Response is empty")
        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def check_min_length(self, content: str) -> ValidationResult:
        errors: list[str] = []
        if len(content.strip()) < self._policy.min_length:
            errors.append(f"Response below minimum length ({len(content.strip())} < {self._policy.min_length})")
        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def check_max_length(self, content: str) -> ValidationResult:
        errors: list[str] = []
        if len(content) > self._policy.max_length:
            errors.append(f"Response exceeds maximum length ({len(content)} > {self._policy.max_length})")
        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def check_json_validity(self, content: str) -> ValidationResult:
        errors: list[str] = []
        trimmed = content.strip()
        if trimmed.startswith("{") or trimmed.startswith("["):
            try:
                json.loads(trimmed)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON: {e}")
        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def check_duplicate_content(self, content: str) -> ValidationResult:
        errors: list[str] = []
        if not self._policy.check_duplicate_content:
            return ValidationResult(passed=True)
        sentences = re.split(r"[.!?]+", content)
        seen: set[str] = set()
        duplicates: list[str] = []
        for s in sentences:
            stripped = s.strip().lower()
            if len(stripped) > 10:
                if stripped in seen:
                    duplicates.append(stripped[:50])
                seen.add(stripped)
        if duplicates:
            errors.append(f"Duplicate content detected ({len(duplicates)} instances)")
        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def check_repeated_sentences(self, content: str) -> ValidationResult:
        errors: list[str] = []
        if not self._policy.check_repeated_sentences:
            return ValidationResult(passed=True)
        lines = [line.strip().lower() for line in content.split("\n") if line.strip()]
        from collections import Counter
        line_counts = Counter(lines)
        repeated = [(line, count) for line, count in line_counts.items() if count > 2]
        if repeated:
            errors.append(f"Repeated sentences detected ({len(repeated)} lines repeated >2x)")
        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def check_prompt_leakage(self, content: str) -> ValidationResult:
        errors: list[str] = []
        if not self._policy.detect_prompt_leakage:
            return ValidationResult(passed=True)
        content_lower = content.lower()
        for pattern in self._policy.forbidden_patterns:
            if pattern.lower() in content_lower:
                errors.append(f"Prompt leakage detected: pattern '{pattern}' found")
                break
        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def check_pii(self, content: str) -> ValidationResult:
        errors: list[str] = []
        if not self._policy.detect_pii:
            return ValidationResult(passed=True)
        for pattern in self._policy.pii_patterns:
            matches = re.findall(pattern, content)
            if matches:
                errors.append(f"PII detected: {len(matches)} match(es) found")
                break
        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def check_sensitive_data(self, content: str) -> ValidationResult:
        errors: list[str] = []
        if not self._policy.detect_sensitive_data:
            return ValidationResult(passed=True)
        content_lower = content.lower()
        for pattern in self._policy.sensitive_patterns:
            if re.search(pattern, content_lower):
                errors.append("Sensitive data pattern detected")
                break
        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def check_unicode_safety(self, content: str) -> ValidationResult:
        errors: list[str] = []
        if not self._policy.check_unicode_safety:
            return ValidationResult(passed=True)
        non_ascii = sum(1 for c in content if ord(c) > 127)
        total = len(content)
        if total > 0 and non_ascii / total > self._policy.max_allowed_unicode_ratio:
            errors.append(f"High ratio of unicode characters ({non_ascii}/{total})")
        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def check_control_characters(self, content: str) -> ValidationResult:
        errors: list[str] = []
        if not self._policy.check_control_characters:
            return ValidationResult(passed=True)
        control_chars = [c for c in content if ord(c) < 32 and c not in "\n\r\t"]
        if len(control_chars) > self._policy.max_allowed_control_chars:
            errors.append(f"Excessive control characters ({len(control_chars)} found)")
        return ValidationResult(passed=len(errors) == 0, errors=errors)

    def run_all(self, content: str) -> dict[str, ValidationResult]:
        results: dict[str, ValidationResult] = {}
        results["empty"] = self.check_empty(content)
        results["min_length"] = self.check_min_length(content)
        results["max_length"] = self.check_max_length(content)
        results["json_validity"] = self.check_json_validity(content)
        results["duplicate_content"] = self.check_duplicate_content(content)
        results["repeated_sentences"] = self.check_repeated_sentences(content)
        results["prompt_leakage"] = self.check_prompt_leakage(content)
        results["pii"] = self.check_pii(content)
        results["sensitive_data"] = self.check_sensitive_data(content)
        results["unicode_safety"] = self.check_unicode_safety(content)
        results["control_characters"] = self.check_control_characters(content)
        return results
