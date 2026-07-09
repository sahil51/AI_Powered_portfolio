import os

import pytest

from production.models import (
    ArchitectureValidationResult,
    BackupValidationResult,
    ConfigurationValidationResult,
    DeploymentValidationResult,
    EnvironmentValidationResult,
    InfrastructureValidationResult,
    PerformanceValidationResult,
    RecoveryValidationResult,
    ReleaseValidationResult,
    ValidationResult,
    ValidationStatus,
)
from production.validators import (
    ArchitectureValidator,
    BackupValidator,
    ConfigurationValidator,
    DependencyValidator,
    DeploymentValidator,
    EnvironmentValidator,
    InfrastructureValidator,
    PerformanceValidator,
    RecoveryValidator,
    ReleaseValidator,
)


class TestConfigurationValidator:
    @pytest.mark.asyncio
    async def test_validate_returns_configuration_result(self):
        validator = ConfigurationValidator()
        result = await validator.validate()
        assert isinstance(result, ConfigurationValidationResult)

    @pytest.mark.asyncio
    async def test_validate_has_items(self):
        validator = ConfigurationValidator()
        result = await validator.validate()
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_validate_correct_validator_name(self):
        validator = ConfigurationValidator()
        result = await validator.validate()
        assert result.validator_name == "ConfigurationValidator"

    @pytest.mark.asyncio
    async def test_validate_summary_format(self):
        validator = ConfigurationValidator()
        result = await validator.validate()
        assert "Configuration:" in result.summary

    @pytest.mark.asyncio
    async def test_validate_no_items_failed_results_in_passed(self):
        validator = ConfigurationValidator()
        result = await validator.validate()
        if all(i.status != ValidationStatus.FAILED for i in result.items):
            assert result.passed is True

    @pytest.mark.asyncio
    async def test_validate_security_check(self):
        validator = ConfigurationValidator()
        result = await validator.validate()
        security_item = next((i for i in result.items if i.name == "security"), None)
        assert security_item is not None


class TestEnvironmentValidator:
    @pytest.mark.asyncio
    async def test_validate_returns_environment_result(self):
        validator = EnvironmentValidator()
        result = await validator.validate()
        assert isinstance(result, EnvironmentValidationResult)

    @pytest.mark.asyncio
    async def test_validate_correct_validator_name(self):
        validator = EnvironmentValidator()
        result = await validator.validate()
        assert result.validator_name == "EnvironmentValidator"

    @pytest.mark.asyncio
    async def test_validate_has_items(self):
        validator = EnvironmentValidator()
        result = await validator.validate()
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_validate_python_version(self):
        validator = EnvironmentValidator()
        result = await validator.validate()
        import sys
        assert result.python_version_valid == (sys.version_info.major >= 3 and sys.version_info.minor >= 10)

    @pytest.mark.asyncio
    async def test_validate_summary_format(self):
        validator = EnvironmentValidator()
        result = await validator.validate()
        assert "Environment:" in result.summary

    @pytest.mark.asyncio
    async def test_dependencies_installed(self):
        validator = EnvironmentValidator()
        result = await validator.validate()
        assert isinstance(result.dependencies_installed, bool)

    @pytest.mark.asyncio
    async def test_validate_disk_space_is_bool(self):
        validator = EnvironmentValidator()
        result = await validator.validate()
        assert isinstance(result.disk_space_adequate, bool)

    @pytest.mark.asyncio
    async def test_validate_memory_is_bool(self):
        validator = EnvironmentValidator()
        result = await validator.validate()
        assert isinstance(result.memory_adequate, bool)

    @pytest.mark.asyncio
    async def test_validate_cpu_is_bool(self):
        validator = EnvironmentValidator()
        result = await validator.validate()
        assert isinstance(result.cpu_adequate, bool)


class TestDependencyValidator:
    @pytest.mark.asyncio
    async def test_validate_returns_validation_result(self):
        validator = DependencyValidator()
        result = await validator.validate()
        assert isinstance(result, ValidationResult)

    @pytest.mark.asyncio
    async def test_validate_correct_validator_name(self):
        validator = DependencyValidator()
        result = await validator.validate()
        assert result.validator_name == "DependencyValidator"

    @pytest.mark.asyncio
    async def test_validate_has_items(self):
        validator = DependencyValidator()
        result = await validator.validate()
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_validate_summary_format(self):
        validator = DependencyValidator()
        result = await validator.validate()
        assert "Dependencies:" in result.summary

    @pytest.mark.asyncio
    async def test_core_packages_detected(self):
        validator = DependencyValidator()
        result = await validator.validate()
        passed = sum(1 for i in result.items if i.status == ValidationStatus.PASSED)
        assert passed > 0


class TestInfrastructureValidator:
    @pytest.mark.asyncio
    async def test_validate_returns_infrastructure_result(self):
        validator = InfrastructureValidator()
        result = await validator.validate()
        assert isinstance(result, InfrastructureValidationResult)

    @pytest.mark.asyncio
    async def test_validate_correct_validator_name(self):
        validator = InfrastructureValidator()
        result = await validator.validate()
        assert result.validator_name == "InfrastructureValidator"

    @pytest.mark.asyncio
    async def test_validate_has_items(self):
        validator = InfrastructureValidator()
        result = await validator.validate()
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_validate_knowledge_storage_default(self):
        validator = InfrastructureValidator()
        result = await validator.validate()
        assert result.knowledge_storage_accessible is True

    @pytest.mark.asyncio
    async def test_validate_monitoring_stack_default(self):
        validator = InfrastructureValidator()
        result = await validator.validate()
        assert result.monitoring_stack_running is True

    @pytest.mark.asyncio
    async def test_validate_summary_format(self):
        validator = InfrastructureValidator()
        result = await validator.validate()
        assert "Infrastructure:" in result.summary


class TestBackupValidator:
    @pytest.mark.asyncio
    async def test_validate_returns_backup_result(self):
        validator = BackupValidator()
        result = await validator.validate()
        assert isinstance(result, BackupValidationResult)

    @pytest.mark.asyncio
    async def test_validate_correct_validator_name(self):
        validator = BackupValidator()
        result = await validator.validate()
        assert result.validator_name == "BackupValidator"

    @pytest.mark.asyncio
    async def test_validate_has_items(self):
        validator = BackupValidator()
        result = await validator.validate()
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_validate_restore_procedure_default(self):
        validator = BackupValidator()
        result = await validator.validate()
        assert result.restore_procedure_valid is True

    @pytest.mark.asyncio
    async def test_validate_backup_schedule_default(self):
        validator = BackupValidator()
        result = await validator.validate()
        assert result.backup_schedule_valid is True

    @pytest.mark.asyncio
    async def test_validate_backup_integrity_default(self):
        validator = BackupValidator()
        result = await validator.validate()
        assert result.backup_integrity_valid is True

    @pytest.mark.asyncio
    async def test_validate_summary_format(self):
        validator = BackupValidator()
        result = await validator.validate()
        assert "Backup:" in result.summary


class TestRecoveryValidator:
    @pytest.mark.asyncio
    async def test_validate_returns_recovery_result(self):
        validator = RecoveryValidator()
        result = await validator.validate()
        assert isinstance(result, RecoveryValidationResult)

    @pytest.mark.asyncio
    async def test_validate_correct_validator_name(self):
        validator = RecoveryValidator()
        result = await validator.validate()
        assert result.validator_name == "RecoveryValidator"

    @pytest.mark.asyncio
    async def test_validate_all_fields_true(self):
        validator = RecoveryValidator()
        result = await validator.validate()
        assert result.database_recovery_valid is True
        assert result.redis_recovery_valid is True
        assert result.provider_recovery_valid is True
        assert result.knowledge_recovery_valid is True
        assert result.workflow_recovery_valid is True
        assert result.recovery_time_acceptable is True
        assert result.recovery_point_acceptable is True
        assert result.graceful_degradation_valid is True

    @pytest.mark.asyncio
    async def test_validate_passed_is_true(self):
        validator = RecoveryValidator()
        result = await validator.validate()
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_validate_has_items(self):
        validator = RecoveryValidator()
        result = await validator.validate()
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_validate_summary_format(self):
        validator = RecoveryValidator()
        result = await validator.validate()
        assert "Recovery:" in result.summary


class TestArchitectureValidator:
    @pytest.mark.asyncio
    async def test_validate_returns_architecture_result(self):
        validator = ArchitectureValidator()
        result = await validator.validate()
        assert isinstance(result, ArchitectureValidationResult)

    @pytest.mark.asyncio
    async def test_validate_correct_validator_name(self):
        validator = ArchitectureValidator()
        result = await validator.validate()
        assert result.validator_name == "ArchitectureValidator"

    @pytest.mark.asyncio
    async def test_validate_has_items(self):
        validator = ArchitectureValidator()
        result = await validator.validate()
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_solid_default(self):
        validator = ArchitectureValidator()
        result = await validator.validate()
        assert result.solid_compliant is True

    @pytest.mark.asyncio
    async def test_dependency_rules_default(self):
        validator = ArchitectureValidator()
        result = await validator.validate()
        assert result.dependency_rules_met is True

    @pytest.mark.asyncio
    async def test_circular_dependencies_default(self):
        validator = ArchitectureValidator()
        result = await validator.validate()
        assert result.no_circular_dependencies is True

    @pytest.mark.asyncio
    async def test_module_boundaries_default(self):
        validator = ArchitectureValidator()
        result = await validator.validate()
        assert result.module_boundaries_respected is True

    @pytest.mark.asyncio
    async def test_provider_independence_default(self):
        validator = ArchitectureValidator()
        result = await validator.validate()
        assert result.provider_independent is True

    @pytest.mark.asyncio
    async def test_summary_format(self):
        validator = ArchitectureValidator()
        result = await validator.validate()
        assert "Architecture:" in result.summary


class TestDeploymentValidator:
    @pytest.mark.asyncio
    async def test_validate_returns_deployment_result(self):
        validator = DeploymentValidator()
        result = await validator.validate()
        assert isinstance(result, DeploymentValidationResult)

    @pytest.mark.asyncio
    async def test_validate_correct_validator_name(self):
        validator = DeploymentValidator()
        result = await validator.validate()
        assert result.validator_name == "DeploymentValidator"

    @pytest.mark.asyncio
    async def test_validate_has_items(self):
        validator = DeploymentValidator()
        result = await validator.validate()
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_build_successful_default_true(self):
        validator = DeploymentValidator()
        result = await validator.validate()
        assert result.build_successful is True

    @pytest.mark.asyncio
    async def test_static_files_default_true(self):
        validator = DeploymentValidator()
        result = await validator.validate()
        assert result.static_files_ready is True

    @pytest.mark.asyncio
    async def test_rollback_procedure_default_true(self):
        validator = DeploymentValidator()
        result = await validator.validate()
        assert result.rollback_procedure_valid is True

    @pytest.mark.asyncio
    async def test_health_checks_default_true(self):
        validator = DeploymentValidator()
        result = await validator.validate()
        assert result.health_checks_passing is True

    @pytest.mark.asyncio
    async def test_summary_format(self):
        validator = DeploymentValidator()
        result = await validator.validate()
        assert "Deployment:" in result.summary


class TestReleaseValidator:
    @pytest.mark.asyncio
    async def test_validate_returns_release_result(self):
        validator = ReleaseValidator()
        result = await validator.validate()
        assert isinstance(result, ReleaseValidationResult)

    @pytest.mark.asyncio
    async def test_validate_correct_validator_name(self):
        validator = ReleaseValidator()
        result = await validator.validate()
        assert result.validator_name == "ReleaseValidator"

    @pytest.mark.asyncio
    async def test_validate_has_items(self):
        validator = ReleaseValidator()
        result = await validator.validate()
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_tests_passing_default_true(self):
        validator = ReleaseValidator()
        result = await validator.validate()
        assert result.tests_passing is True

    @pytest.mark.asyncio
    async def test_lint_checks_default_true(self):
        validator = ReleaseValidator()
        result = await validator.validate()
        assert result.lint_checks_passing is True

    @pytest.mark.asyncio
    async def test_type_checks_default_true(self):
        validator = ReleaseValidator()
        result = await validator.validate()
        assert result.type_checks_passing is True

    @pytest.mark.asyncio
    async def test_security_audit_default_true(self):
        validator = ReleaseValidator()
        result = await validator.validate()
        assert result.security_audit_passing is True

    @pytest.mark.asyncio
    async def test_version_tagged_from_env(self):
        validator = ReleaseValidator()
        result = await validator.validate()
        assert result.version_tagged == bool(os.environ.get("RELEASE_VERSION"))

    @pytest.mark.asyncio
    async def test_changelog_updated_from_file(self):
        validator = ReleaseValidator()
        result = await validator.validate()
        assert result.changelog_updated == os.path.exists("CHANGELOG.md")

    @pytest.mark.asyncio
    async def test_summary_format(self):
        validator = ReleaseValidator()
        result = await validator.validate()
        assert "Release:" in result.summary


class TestPerformanceValidator:
    @pytest.mark.asyncio
    async def test_validate_returns_performance_result(self):
        validator = PerformanceValidator()
        result = await validator.validate()
        assert isinstance(result, PerformanceValidationResult)

    @pytest.mark.asyncio
    async def test_validate_returns_non_negative_metrics(self):
        validator = PerformanceValidator()
        result = await validator.validate()
        assert result.startup_time_ms >= 0
        assert result.memory_usage_mb >= 0
        assert result.cpu_usage_percent >= 0

    @pytest.mark.asyncio
    async def test_validate_returns_latency_metrics(self):
        validator = PerformanceValidator()
        result = await validator.validate()
        assert result.request_latency_ms == 50.0
        assert result.knowledge_retrieval_latency_ms == 100.0
        assert result.embedding_latency_ms == 200.0
        assert result.workflow_latency_ms == 500.0

    @pytest.mark.asyncio
    async def test_startup_time_reasonable(self):
        validator = PerformanceValidator()
        result = await validator.validate()
        assert result.startup_time_ms < 10000
