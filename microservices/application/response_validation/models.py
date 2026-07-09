from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ValidationResult:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def merge(self, other: ValidationResult) -> ValidationResult:
        return ValidationResult(
            passed=self.passed and other.passed,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            details={**self.details, **other.details},
        )


@dataclass
class ValidationReport:
    passed: bool
    results: dict[str, ValidationResult] = field(default_factory=dict)
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warning_checks: int = 0
    latency_ms: float = 0.0
    validated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def all_errors(self) -> list[str]:
        errors: list[str] = []
        for key, result in self.results.items():
            errors.extend(f"[{key}] {e}" for e in result.errors)
        return errors

    @property
    def all_warnings(self) -> list[str]:
        warnings: list[str] = []
        for key, result in self.results.items():
            warnings.extend(f"[{key}] {w}" for w in result.warnings)
        return warnings


@dataclass
class ResponseMetadata:
    content: str = ""
    content_type: str = "text"
    content_length: int = 0
    line_count: int = 0
    word_count: int = 0
    has_json: bool = False
    has_markdown: bool = False
    has_code_blocks: bool = False
    has_html: bool = False
    has_urls: bool = False
    unicode_count: int = 0
    control_char_count: int = 0
    detected_pii: list[str] = field(default_factory=list)
    detected_prompt_leakage: bool = False
    detected_sensitive_data: list[str] = field(default_factory=list)
