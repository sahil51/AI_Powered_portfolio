from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ValidationStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ValidationItem:
    name: str
    status: ValidationStatus
    severity: ValidationSeverity = ValidationSeverity.MEDIUM
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    validator_name: str
    passed: bool
    items: list[ValidationItem] = field(default_factory=list)
    summary: str = ""
    duration_ms: float = 0.0


@dataclass
class BackupValidationResult(ValidationResult):
    database_backup_valid: bool = False
    redis_backup_valid: bool = False
    knowledge_backup_valid: bool = False
    configuration_backup_valid: bool = False
    restore_procedure_valid: bool = False
    backup_schedule_valid: bool = False
    backup_integrity_valid: bool = False


@dataclass
class RecoveryValidationResult(ValidationResult):
    database_recovery_valid: bool = False
    redis_recovery_valid: bool = False
    provider_recovery_valid: bool = False
    knowledge_recovery_valid: bool = False
    workflow_recovery_valid: bool = False
    recovery_time_acceptable: bool = False
    recovery_point_acceptable: bool = False
    graceful_degradation_valid: bool = False


@dataclass
class ArchitectureValidationResult(ValidationResult):
    ddd_compliant: bool = False
    clean_architecture_compliant: bool = False
    solid_compliant: bool = False
    dependency_rules_met: bool = False
    no_circular_dependencies: bool = False
    module_boundaries_respected: bool = False
    provider_independent: bool = False


@dataclass
class ConfigurationValidationResult(ValidationResult):
    secrets_configured: bool = False
    database_configured: bool = False
    redis_configured: bool = False
    celery_configured: bool = False
    ai_providers_configured: bool = False
    embedding_providers_configured: bool = False
    monitoring_configured: bool = False
    security_configured: bool = False


@dataclass
class EnvironmentValidationResult(ValidationResult):
    python_version_valid: bool = False
    dependencies_installed: bool = False
    environment_variables_set: bool = False
    disk_space_adequate: bool = False
    memory_adequate: bool = False
    cpu_adequate: bool = False


@dataclass
class InfrastructureValidationResult(ValidationResult):
    database_reachable: bool = False
    redis_reachable: bool = False
    celery_available: bool = False
    n8n_reachable: bool = False
    knowledge_storage_accessible: bool = False
    monitoring_stack_running: bool = False


@dataclass
class DeploymentValidationResult(ValidationResult):
    build_successful: bool = False
    migrations_applied: bool = False
    static_files_ready: bool = False
    deployment_scripts_valid: bool = False
    rollback_procedure_valid: bool = False
    health_checks_passing: bool = False


@dataclass
class ReleaseValidationResult(ValidationResult):
    version_tagged: bool = False
    changelog_updated: bool = False
    tests_passing: bool = False
    lint_checks_passing: bool = False
    type_checks_passing: bool = False
    security_audit_passing: bool = False


@dataclass
class ChecklistItem:
    category: str
    name: str
    description: str
    required: bool = True
    status: ValidationStatus = ValidationStatus.PENDING
    details: str = ""


@dataclass
class ProductionChecklist:
    items: list[ChecklistItem] = field(default_factory=list)
    total: int = 0
    passed: int = 0
    failed: int = 0
    warning: int = 0
    skipped: int = 0

    @property
    def pass_rate(self) -> float:
        completed = self.passed + self.failed
        return self.passed / completed if completed > 0 else 0.0

    @property
    def ready(self) -> bool:
        return self.failed == 0


@dataclass
class PerformanceValidationResult:
    startup_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    request_latency_ms: float = 0.0
    knowledge_retrieval_latency_ms: float = 0.0
    embedding_latency_ms: float = 0.0
    workflow_latency_ms: float = 0.0


@dataclass
class ReadinessReport:
    report_id: str
    timestamp: float = 0.0
    overall_ready: bool = False
    checklist: ProductionChecklist | None = None
    architecture: ArchitectureValidationResult | None = None
    deployment: DeploymentValidationResult | None = None
    backup: BackupValidationResult | None = None
    recovery: RecoveryValidationResult | None = None
    configuration: ConfigurationValidationResult | None = None
    environment: EnvironmentValidationResult | None = None
    infrastructure: InfrastructureValidationResult | None = None
    dependencies: ValidationResult | None = None
    release: ReleaseValidationResult | None = None
    performance: PerformanceValidationResult | None = None
    summary: str = ""
    recommendations: list[str] = field(default_factory=list)
