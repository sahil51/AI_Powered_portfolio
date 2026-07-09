from production.models import (
    ArchitectureValidationResult,
    BackupValidationResult,
    ChecklistItem,
    ConfigurationValidationResult,
    DeploymentValidationResult,
    EnvironmentValidationResult,
    InfrastructureValidationResult,
    PerformanceValidationResult,
    ProductionChecklist,
    ReadinessReport,
    RecoveryValidationResult,
    ReleaseValidationResult,
    ValidationItem,
    ValidationResult,
    ValidationSeverity,
    ValidationStatus,
)


class TestValidationSeverity:
    def test_values(self):
        assert ValidationSeverity.CRITICAL.value == "critical"
        assert ValidationSeverity.HIGH.value == "high"
        assert ValidationSeverity.MEDIUM.value == "medium"
        assert ValidationSeverity.LOW.value == "low"
        assert ValidationSeverity.INFO.value == "info"

    def test_is_enum(self):
        assert issubclass(ValidationSeverity, str)


class TestValidationStatus:
    def test_values(self):
        assert ValidationStatus.PENDING.value == "pending"
        assert ValidationStatus.PASSED.value == "passed"
        assert ValidationStatus.FAILED.value == "failed"
        assert ValidationStatus.WARNING.value == "warning"
        assert ValidationStatus.SKIPPED.value == "skipped"

    def test_is_enum(self):
        assert issubclass(ValidationStatus, str)


class TestValidationItem:
    def test_defaults(self):
        item = ValidationItem(name="test", status=ValidationStatus.PASSED)
        assert item.name == "test"
        assert item.status == ValidationStatus.PASSED
        assert item.severity == ValidationSeverity.MEDIUM
        assert item.message == ""
        assert item.details == {}

    def test_custom_values(self):
        item = ValidationItem(
            name="custom",
            status=ValidationStatus.FAILED,
            severity=ValidationSeverity.CRITICAL,
            message="Something went wrong",
            details={"key": "value"},
        )
        assert item.name == "custom"
        assert item.status == ValidationStatus.FAILED
        assert item.severity == ValidationSeverity.CRITICAL
        assert item.message == "Something went wrong"
        assert item.details == {"key": "value"}

    def test_details_mutable(self):
        item = ValidationItem(name="test", status=ValidationStatus.PASSED)
        item.details["extra"] = "info"
        assert item.details["extra"] == "info"


class TestValidationResult:
    def test_defaults(self):
        result = ValidationResult(validator_name="TestValidator", passed=True)
        assert result.validator_name == "TestValidator"
        assert result.passed is True
        assert result.items == []
        assert result.summary == ""
        assert result.duration_ms == 0.0

    def test_with_items(self):
        items = [
            ValidationItem(name="a", status=ValidationStatus.PASSED),
            ValidationItem(name="b", status=ValidationStatus.FAILED),
        ]
        result = ValidationResult(
            validator_name="Test", passed=False, items=items, summary="2 checks", duration_ms=10.5
        )
        assert result.passed is False
        assert result.items == items
        assert result.summary == "2 checks"
        assert result.duration_ms == 10.5


class TestBackupValidationResult:
    def test_defaults(self):
        r = BackupValidationResult(validator_name="B", passed=True)
        assert r.database_backup_valid is False
        assert r.redis_backup_valid is False
        assert r.knowledge_backup_valid is False
        assert r.configuration_backup_valid is False
        assert r.restore_procedure_valid is False
        assert r.backup_schedule_valid is False
        assert r.backup_integrity_valid is False

    def test_custom_values(self):
        r = BackupValidationResult(
            validator_name="B", passed=True, database_backup_valid=True,
            redis_backup_valid=True, knowledge_backup_valid=True,
            configuration_backup_valid=True, restore_procedure_valid=True,
            backup_schedule_valid=True, backup_integrity_valid=True,
        )
        assert r.database_backup_valid is True
        assert r.backup_integrity_valid is True

    def test_inherits_validation_result(self):
        r = BackupValidationResult(validator_name="B", passed=True, summary="ok")
        assert isinstance(r, ValidationResult)
        assert r.validator_name == "B"


class TestRecoveryValidationResult:
    def test_defaults(self):
        r = RecoveryValidationResult(validator_name="R", passed=True)
        assert r.database_recovery_valid is False
        assert r.redis_recovery_valid is False
        assert r.provider_recovery_valid is False
        assert r.knowledge_recovery_valid is False
        assert r.workflow_recovery_valid is False
        assert r.recovery_time_acceptable is False
        assert r.recovery_point_acceptable is False
        assert r.graceful_degradation_valid is False

    def test_custom_values(self):
        r = RecoveryValidationResult(
            validator_name="R", passed=True, graceful_degradation_valid=True
        )
        assert r.graceful_degradation_valid is True


class TestArchitectureValidationResult:
    def test_defaults(self):
        r = ArchitectureValidationResult(validator_name="A", passed=True)
        assert r.ddd_compliant is False
        assert r.clean_architecture_compliant is False
        assert r.solid_compliant is False
        assert r.dependency_rules_met is False
        assert r.no_circular_dependencies is False
        assert r.module_boundaries_respected is False
        assert r.provider_independent is False

    def test_custom_values(self):
        r = ArchitectureValidationResult(
            validator_name="A", passed=True, ddd_compliant=True,
            solid_compliant=True, provider_independent=True,
        )
        assert r.ddd_compliant is True
        assert r.solid_compliant is True


class TestConfigurationValidationResult:
    def test_defaults(self):
        r = ConfigurationValidationResult(validator_name="C", passed=True)
        assert r.secrets_configured is False
        assert r.database_configured is False
        assert r.redis_configured is False
        assert r.celery_configured is False
        assert r.ai_providers_configured is False
        assert r.embedding_providers_configured is False
        assert r.monitoring_configured is False
        assert r.security_configured is False

    def test_custom_values(self):
        r = ConfigurationValidationResult(
            validator_name="C", passed=True, secrets_configured=True,
            database_configured=True, monitoring_configured=True,
        )
        assert r.secrets_configured is True
        assert r.database_configured is True


class TestEnvironmentValidationResult:
    def test_defaults(self):
        r = EnvironmentValidationResult(validator_name="E", passed=True)
        assert r.python_version_valid is False
        assert r.dependencies_installed is False
        assert r.environment_variables_set is False
        assert r.disk_space_adequate is False
        assert r.memory_adequate is False
        assert r.cpu_adequate is False

    def test_custom_values(self):
        r = EnvironmentValidationResult(
            validator_name="E", passed=True, python_version_valid=True,
            disk_space_adequate=True, memory_adequate=True, cpu_adequate=True,
        )
        assert r.python_version_valid is True
        assert r.cpu_adequate is True


class TestInfrastructureValidationResult:
    def test_defaults(self):
        r = InfrastructureValidationResult(validator_name="I", passed=True)
        assert r.database_reachable is False
        assert r.redis_reachable is False
        assert r.celery_available is False
        assert r.n8n_reachable is False
        assert r.knowledge_storage_accessible is False
        assert r.monitoring_stack_running is False

    def test_custom_values(self):
        r = InfrastructureValidationResult(
            validator_name="I", passed=True, database_reachable=True,
            monitoring_stack_running=True,
        )
        assert r.database_reachable is True


class TestDeploymentValidationResult:
    def test_defaults(self):
        r = DeploymentValidationResult(validator_name="D", passed=True)
        assert r.build_successful is False
        assert r.migrations_applied is False
        assert r.static_files_ready is False
        assert r.deployment_scripts_valid is False
        assert r.rollback_procedure_valid is False
        assert r.health_checks_passing is False

    def test_custom_values(self):
        r = DeploymentValidationResult(
            validator_name="D", passed=True, build_successful=True,
            migrations_applied=True, health_checks_passing=True,
        )
        assert r.build_successful is True
        assert r.health_checks_passing is True


class TestReleaseValidationResult:
    def test_defaults(self):
        r = ReleaseValidationResult(validator_name="R", passed=True)
        assert r.version_tagged is False
        assert r.changelog_updated is False
        assert r.tests_passing is False
        assert r.lint_checks_passing is False
        assert r.type_checks_passing is False
        assert r.security_audit_passing is False

    def test_custom_values(self):
        r = ReleaseValidationResult(
            validator_name="R", passed=True, version_tagged=True,
            tests_passing=True, lint_checks_passing=True,
        )
        assert r.version_tagged is True
        assert r.lint_checks_passing is True


class TestChecklistItem:
    def test_defaults(self):
        item = ChecklistItem(category="Config", name="Test", description="desc")
        assert item.category == "Config"
        assert item.name == "Test"
        assert item.description == "desc"
        assert item.required is True
        assert item.status == ValidationStatus.PENDING
        assert item.details == ""

    def test_not_required(self):
        item = ChecklistItem(
            category="Config", name="Test", description="desc", required=False,
            status=ValidationStatus.PASSED, details="Done",
        )
        assert item.required is False
        assert item.status == ValidationStatus.PASSED
        assert item.details == "Done"

    def test_immutable_fields(self):
        item = ChecklistItem(category="A", name="B", description="C")
        assert item.category == "A"
        assert item.name == "B"
        assert item.description == "C"


class TestProductionChecklist:
    def test_defaults(self):
        cl = ProductionChecklist()
        assert cl.items == []
        assert cl.total == 0
        assert cl.passed == 0
        assert cl.failed == 0
        assert cl.warning == 0
        assert cl.skipped == 0

    def test_pass_rate_no_completed(self):
        cl = ProductionChecklist()
        assert cl.pass_rate == 0.0

    def test_pass_rate_some_passed(self):
        cl = ProductionChecklist(passed=3, failed=1)
        assert cl.pass_rate == 0.75

    def test_pass_rate_all_passed(self):
        cl = ProductionChecklist(passed=5, failed=0)
        assert cl.pass_rate == 1.0

    def test_ready_no_failures(self):
        cl = ProductionChecklist(failed=0)
        assert cl.ready is True

    def test_ready_with_failures(self):
        cl = ProductionChecklist(failed=1)
        assert cl.ready is False

    def test_with_items(self):
        items = [
            ChecklistItem(category="A", name="1", description="d1"),
            ChecklistItem(category="B", name="2", description="d2"),
        ]
        cl = ProductionChecklist(items=items, total=2)
        assert len(cl.items) == 2
        assert cl.total == 2
        assert cl.items[0].name == "1"


class TestPerformanceValidationResult:
    def test_defaults(self):
        p = PerformanceValidationResult()
        assert p.startup_time_ms == 0.0
        assert p.memory_usage_mb == 0.0
        assert p.cpu_usage_percent == 0.0
        assert p.request_latency_ms == 0.0
        assert p.knowledge_retrieval_latency_ms == 0.0
        assert p.embedding_latency_ms == 0.0
        assert p.workflow_latency_ms == 0.0

    def test_custom_values(self):
        p = PerformanceValidationResult(
            startup_time_ms=100.5, memory_usage_mb=256.0, cpu_usage_percent=45.0,
            request_latency_ms=50.0, knowledge_retrieval_latency_ms=150.0,
            embedding_latency_ms=200.0, workflow_latency_ms=500.0,
        )
        assert p.startup_time_ms == 100.5
        assert p.memory_usage_mb == 256.0
        assert p.request_latency_ms == 50.0


class TestReadinessReport:
    def test_defaults(self):
        r = ReadinessReport(report_id="test-123")
        assert r.report_id == "test-123"
        assert r.timestamp == 0.0
        assert r.overall_ready is False
        assert r.checklist is None
        assert r.architecture is None
        assert r.deployment is None
        assert r.backup is None
        assert r.recovery is None
        assert r.configuration is None
        assert r.environment is None
        assert r.infrastructure is None
        assert r.dependencies is None
        assert r.release is None
        assert r.performance is None
        assert r.summary == ""
        assert r.recommendations == []

    def test_with_all_sections(self):
        arch = ArchitectureValidationResult(validator_name="A", passed=True)
        config = ConfigurationValidationResult(validator_name="C", passed=False)
        checklist = ProductionChecklist(passed=5, total=10)
        r = ReadinessReport(
            report_id="r1", timestamp=123.0, overall_ready=True,
            checklist=checklist, architecture=arch, configuration=config,
            summary="Ready", recommendations=["Fix config"],
        )
        assert r.report_id == "r1"
        assert r.timestamp == 123.0
        assert r.overall_ready is True
        assert r.checklist == checklist
        assert r.architecture == arch
        assert r.configuration == config
        assert r.summary == "Ready"
        assert r.recommendations == ["Fix config"]

    def test_recommendations_mutable(self):
        r = ReadinessReport(report_id="r1")
        r.recommendations.append("New rec")
        assert len(r.recommendations) == 1
