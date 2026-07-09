import pytest

from domain.memory.aggregate import Memory
from domain.memory.validator import MemoryValidationError, MemoryValidator
from domain.memory.value_objects import (
    MemoryCategory,
    MemoryConfidence,
    MemoryImportance,
    MemoryPriority,
    MemoryScope,
    MemorySource,
)


class TestMemoryValidator:
    def setup_method(self) -> None:
        self.validator = MemoryValidator()

    def test_validate_create_valid(self):
        self.validator.validate_create("user-1", MemoryCategory.FACT, MemoryScope.USER, "value")

    def test_validate_create_empty_user_id(self):
        with pytest.raises(MemoryValidationError, match="User ID is required"):
            self.validator.validate_create("", MemoryCategory.FACT, MemoryScope.USER, "value")

    def test_validate_create_empty_value(self):
        with pytest.raises(MemoryValidationError, match="Memory value is required"):
            self.validator.validate_create("user-1", MemoryCategory.FACT, MemoryScope.USER, "")

    def test_validate_create_invalid_category(self):
        with pytest.raises(MemoryValidationError, match="Invalid memory category"):
            self.validator.validate_create("user-1", "invalid", MemoryScope.USER, "value")  # type: ignore[arg-type]

    def test_validate_value_empty(self):
        with pytest.raises(MemoryValidationError, match="Memory value cannot be empty"):
            self.validator.validate_value("")

    def test_validate_value_whitespace(self):
        with pytest.raises(MemoryValidationError, match="Memory value cannot be empty"):
            self.validator.validate_value("   ")

    def test_validate_value_too_long(self):
        with pytest.raises(MemoryValidationError, match="Memory value exceeds maximum length"):
            self.validator.validate_value("x" * 100001)

    def test_validate_confidence_valid(self):
        self.validator.validate_confidence(MemoryConfidence.HIGH)
        self.validator.validate_confidence(MemoryConfidence.LOW)

    def test_validate_confidence_invalid(self):
        with pytest.raises(MemoryValidationError, match="Invalid confidence level"):
            self.validator.validate_confidence("invalid")  # type: ignore[arg-type]

    def test_validate_priority_valid(self):
        self.validator.validate_priority(MemoryPriority.HIGH)

    def test_validate_priority_invalid(self):
        with pytest.raises(MemoryValidationError, match="Invalid priority"):
            self.validator.validate_priority("invalid")  # type: ignore[arg-type]

    def test_validate_importance_valid(self):
        self.validator.validate_importance(MemoryImportance.HIGH)

    def test_validate_importance_invalid(self):
        with pytest.raises(MemoryValidationError, match="Invalid importance"):
            self.validator.validate_importance("invalid")  # type: ignore[arg-type]

    def test_validate_source_valid(self):
        self.validator.validate_source(MemorySource.USER_INPUT)

    def test_validate_source_invalid(self):
        with pytest.raises(MemoryValidationError, match="Invalid memory source"):
            self.validator.validate_source("invalid")  # type: ignore[arg-type]

    def test_validate_scope_valid(self):
        self.validator.validate_scope(MemoryScope.USER)

    def test_validate_scope_invalid(self):
        with pytest.raises(MemoryValidationError, match="Invalid memory scope"):
            self.validator.validate_scope("invalid")  # type: ignore[arg-type]

    def test_validate_category_valid(self):
        self.validator.validate_category(MemoryCategory.FACT)

    def test_validate_category_invalid(self):
        with pytest.raises(MemoryValidationError, match="Invalid memory category"):
            self.validator.validate_category("invalid")  # type: ignore[arg-type]

    def test_validate_ownership(self):
        memory = Memory(user_id="user-1", value="test")
        assert self.validator.validate_ownership(memory, "user-1")
        assert not self.validator.validate_ownership(memory, "user-2")

    def test_validate_duplicate(self):
        assert self.validator.validate_duplicate("existing", "new")
        assert not self.validator.validate_duplicate("same", "same")

    def test_validate_expiry_none(self):
        assert self.validator.validate_expiry(None)

    def test_validate_retention_not_exceeded(self):
        assert self.validator.validate_retention(1)
