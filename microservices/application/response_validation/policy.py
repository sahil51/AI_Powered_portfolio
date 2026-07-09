from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ResponsePolicy:
    min_length: int = 1
    max_length: int = 100000
    allow_empty: bool = False
    validate_json: bool = True
    validate_markdown: bool = True
    check_duplicate_content: bool = True
    check_repeated_sentences: bool = True
    detect_prompt_leakage: bool = True
    detect_pii: bool = True
    detect_sensitive_data: bool = True
    check_unicode_safety: bool = True
    check_control_characters: bool = True
    check_formatting: bool = True
    check_required_fields: list[str] = field(default_factory=list)
    forbidden_patterns: list[str] = field(default_factory=lambda: [
        "ignore all previous instructions",
        "ignore all instructions",
        "system prompt",
        "you are an ai",
        "you are a large language model",
    ])
    pii_patterns: list[str] = field(default_factory=lambda: [
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        r"\b\d{16}\d*\b",
    ])
    sensitive_patterns: list[str] = field(default_factory=lambda: [
        r"api[_-]?key",
        r"secret",
        r"password",
        r"token",
        r"bearer\s+[A-Za-z0-9\-._~+/]+",
    ])
    max_allowed_unicode_ratio: float = 0.5
    max_allowed_control_chars: int = 5
