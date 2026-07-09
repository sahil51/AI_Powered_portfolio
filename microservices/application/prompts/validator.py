from __future__ import annotations

import re

from application.prompts.metadata import PromptMetadata, PromptStatus
from application.prompts.renderer import PromptRenderer


class PromptValidator:
    def __init__(self) -> None:
        self._renderer = PromptRenderer(strict=False)

    def validate_metadata(self, metadata: PromptMetadata) -> list[str]:
        errors: list[str] = []
        if not metadata.name:
            errors.append("Prompt name is required")
        if not metadata.category:
            errors.append("Prompt category is required")
        if not metadata.version:
            errors.append("Prompt version is required")
        if metadata.status not in PromptStatus.__members__.values():
            errors.append(f"Invalid status: {metadata.status}")
        return errors

    def validate_content(self, content: str) -> list[str]:
        errors: list[str] = []
        if not content or not content.strip():
            errors.append("Prompt content is empty")
        if len(content) < 10:
            errors.append("Prompt content is too short (min 10 chars)")
        return errors

    def validate_variables(self, content: str, metadata: PromptMetadata) -> list[str]:
        template_vars = set(self._renderer.extract_variables(content))
        metadata_vars = {v.name for v in metadata.variables}
        errors: list[str] = []
        missing = metadata_vars - template_vars
        if missing:
            errors.append(f"Variables declared in metadata but not in template: {missing}")
        return errors

    def validate_syntax(self, content: str) -> list[str]:
        errors: list[str] = []
        valid_pattern = re.compile(r"\{\{(\s*[a-zA-Z_][a-zA-Z0-9_.]*\s*)\}\}")
        matched_spans = set(m.span() for m in valid_pattern.finditer(content))
        for potential in re.finditer(r"\{\{[^}]+\}\}", content):
            if potential.span() not in matched_spans:
                errors.append(f"Invalid variable syntax: {potential.group(0)}")
        for match in valid_pattern.finditer(content):
            var = match.group(1).strip()
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_.]*$", var):
                errors.append(f"Invalid variable syntax: {match.group(0)}")
        return errors

    def validate_prompt(self, content: str, metadata: PromptMetadata) -> list[str]:
        errors: list[str] = []
        errors.extend(self.validate_metadata(metadata))
        errors.extend(self.validate_content(content))
        errors.extend(self.validate_syntax(content))
        errors.extend(self.validate_variables(content, metadata))
        return errors
