from __future__ import annotations

import re
from typing import Any

from application.prompts.exceptions import PromptRenderError


class PromptRenderer:
    VARIABLE_PATTERN = re.compile(r"\{\{(\s*[a-zA-Z_][a-zA-Z0-9_.]*\s*)\}\}")

    def __init__(self, strict: bool = True) -> None:
        self._strict = strict

    def render(self, template: str, variables: dict[str, Any]) -> str:
        missing: list[str] = []
        unused = set(variables.keys())

        def replace(match: re.Match) -> str:
            var_name = match.group(1).strip()
            if var_name in variables:
                unused.discard(var_name)
                value = variables[var_name]
                if value is None:
                    value = ""
                return str(value)
            missing.append(var_name)
            if self._strict:
                raise PromptRenderError(
                    f"Missing required variable: {var_name}",
                    detail=f"Template uses {var_name} but it was not provided",
                )
            return ""

        try:
            result = self.VARIABLE_PATTERN.sub(replace, template)
        except PromptRenderError:
            raise
        except Exception as e:
            raise PromptRenderError(f"Render error: {e}")

        if missing:
            result = self.VARIABLE_PATTERN.sub("", result)

        return result

    def extract_variables(self, template: str) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for m in self.VARIABLE_PATTERN.finditer(template):
            var = m.group(1).strip()
            if var not in seen:
                seen.add(var)
                result.append(var)
        return result

    def validate_variables(self, template: str, expected: set[str]) -> list[str]:
        actual = set(self.extract_variables(template))
        missing = expected - actual
        extra = actual - expected
        errors: list[str] = []
        if missing:
            errors.append(f"Missing expected variables: {missing}")
        if extra:
            errors.append(f"Unexpected variables found: {extra}")
        return errors
