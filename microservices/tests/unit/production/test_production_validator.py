import pytest

from production.models import (
    ArchitectureValidationResult,
    BackupValidationResult,
    ConfigurationValidationResult,
    DeploymentValidationResult,
    EnvironmentValidationResult,
    InfrastructureValidationResult,
    PerformanceValidationResult,
    ProductionChecklist,
    ReadinessReport,
    RecoveryValidationResult,
    ReleaseValidationResult,
    ValidationResult,
    ValidationStatus,
)
from production.validator import ProductionValidator


class TestProductionValidatorInitialization:
    def test_init_not_initialized(self):
        validator = ProductionValidator()
        assert validator.initialized is False

    def test_init_no_last_report(self):
        validator = ProductionValidator()
        assert validator.last_report is None

    @pytest.mark.asyncio
    async def test_initialize_sets_initialized(self):
        validator = ProductionValidator()
        await validator.initialize()
        assert validator.initialized is True

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self):
        validator = ProductionValidator()
        await validator.initialize()
        await validator.initialize()
        assert validator.initialized is True

    @pytest.mark.asyncio
    async def test_shutdown_resets_initialized(self):
        validator = ProductionValidator()
        await validator.initialize()
        await validator.shutdown()
        assert validator.initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_idempotent(self):
        validator = ProductionValidator()
        await validator.shutdown()
        assert validator.initialized is False


class TestProductionValidatorValidateAll:
    @pytest.mark.asyncio
    async def test_validate_all_returns_readiness_report(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert isinstance(result, ReadinessReport)

    @pytest.mark.asyncio
    async def test_validate_all_sets_last_report(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert validator.last_report == result

    @pytest.mark.asyncio
    async def test_validate_all_has_report_id(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert result.report_id.startswith("readiness_")
        assert len(result.report_id) > len("readiness_")

    @pytest.mark.asyncio
    async def test_validate_all_has_timestamp(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert result.timestamp > 0

    @pytest.mark.asyncio
    async def test_validate_all_has_configuration(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert isinstance(result.configuration, ConfigurationValidationResult)

    @pytest.mark.asyncio
    async def test_validate_all_has_environment(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert isinstance(result.environment, EnvironmentValidationResult)

    @pytest.mark.asyncio
    async def test_validate_all_has_dependencies(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert isinstance(result.dependencies, ValidationResult)

    @pytest.mark.asyncio
    async def test_validate_all_has_infrastructure(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert isinstance(result.infrastructure, InfrastructureValidationResult)

    @pytest.mark.asyncio
    async def test_validate_all_has_backup(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert isinstance(result.backup, BackupValidationResult)

    @pytest.mark.asyncio
    async def test_validate_all_has_recovery(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert isinstance(result.recovery, RecoveryValidationResult)

    @pytest.mark.asyncio
    async def test_validate_all_has_architecture(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert isinstance(result.architecture, ArchitectureValidationResult)

    @pytest.mark.asyncio
    async def test_validate_all_has_deployment(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert isinstance(result.deployment, DeploymentValidationResult)

    @pytest.mark.asyncio
    async def test_validate_all_has_release(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert isinstance(result.release, ReleaseValidationResult)

    @pytest.mark.asyncio
    async def test_validate_all_has_performance(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert isinstance(result.performance, PerformanceValidationResult)

    @pytest.mark.asyncio
    async def test_validate_all_has_checklist(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert isinstance(result.checklist, ProductionChecklist)
        assert result.checklist.total > 0

    @pytest.mark.asyncio
    async def test_validate_all_checklist_items_have_status(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        for item in result.checklist.items:
            assert item.status != ValidationStatus.PENDING

    @pytest.mark.asyncio
    async def test_validate_all_summary(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert len(result.summary) > 0

    @pytest.mark.asyncio
    async def test_validate_all_recommendations_is_list(self):
        validator = ProductionValidator()
        result = await validator.validate_all()
        assert isinstance(result.recommendations, list)


class TestProductionValidatorCounts:
    @pytest.mark.asyncio
    async def test_count_failures_all_passed(self):
        validator = ProductionValidator()
        arch = ArchitectureValidationResult(validator_name="A", passed=True)
        config = ConfigurationValidationResult(validator_name="C", passed=True)
        env = EnvironmentValidationResult(validator_name="E", passed=True)
        deps = ValidationResult(validator_name="D", passed=True)
        infra = InfrastructureValidationResult(validator_name="I", passed=True)
        backup = BackupValidationResult(validator_name="B", passed=True)
        recovery = RecoveryValidationResult(validator_name="R", passed=True)
        deploy = DeploymentValidationResult(validator_name="D", passed=True)
        release = ReleaseValidationResult(validator_name="R", passed=True)
        report = ReadinessReport(report_id="r", architecture=arch, configuration=config,
                                 environment=env, dependencies=deps, infrastructure=infra,
                                 backup=backup, recovery=recovery, deployment=deploy,
                                 release=release)
        assert validator._count_failures(report) == 0

    @pytest.mark.asyncio
    async def test_count_failures_some_failed(self):
        validator = ProductionValidator()
        arch = ArchitectureValidationResult(validator_name="A", passed=False)
        config = ConfigurationValidationResult(validator_name="C", passed=True)
        env = EnvironmentValidationResult(validator_name="E", passed=True)
        deps = ValidationResult(validator_name="D", passed=True)
        infra = InfrastructureValidationResult(validator_name="I", passed=False)
        backup = BackupValidationResult(validator_name="B", passed=True)
        recovery = RecoveryValidationResult(validator_name="R", passed=True)
        deploy = DeploymentValidationResult(validator_name="D", passed=True)
        release = ReleaseValidationResult(validator_name="R", passed=True)
        report = ReadinessReport(report_id="r", architecture=arch, configuration=config,
                                 environment=env, dependencies=deps, infrastructure=infra,
                                 backup=backup, recovery=recovery, deployment=deploy,
                                 release=release)
        assert validator._count_failures(report) == 2

    @pytest.mark.asyncio
    async def test_count_failures_with_none(self):
        validator = ProductionValidator()
        report = ReadinessReport(report_id="r")
        assert validator._count_failures(report) == 0

    @pytest.mark.asyncio
    async def test_count_warnings(self):
        validator = ProductionValidator()
        from production.models import ValidationItem, ValidationSeverity
        config = ConfigurationValidationResult(validator_name="C", passed=True)
        config.items = [
            ValidationItem(name="w1", status=ValidationStatus.WARNING, severity=ValidationSeverity.MEDIUM),
            ValidationItem(name="p1", status=ValidationStatus.PASSED, severity=ValidationSeverity.LOW),
        ]
        report = ReadinessReport(report_id="r", configuration=config)
        assert validator._count_warnings(report) == 1

    @pytest.mark.asyncio
    async def test_count_warnings_none(self):
        validator = ProductionValidator()
        config = ConfigurationValidationResult(validator_name="C", passed=True)
        report = ReadinessReport(report_id="r", configuration=config)
        assert validator._count_warnings(report) == 0

    @pytest.mark.asyncio
    async def test_count_warnings_with_none_sections(self):
        validator = ProductionValidator()
        report = ReadinessReport(report_id="r")
        assert validator._count_warnings(report) == 0


class TestProductionValidatorBuildSummary:
    @pytest.mark.asyncio
    async def test_build_summary_with_failures(self):
        validator = ProductionValidator()
        report = ReadinessReport(report_id="r")
        config = ConfigurationValidationResult(validator_name="C", passed=False)
        report.configuration = config
        summary = validator._build_summary(report, 1, 0)
        assert "1 failures" in summary
        assert "Configuration validation failed" in summary

    @pytest.mark.asyncio
    async def test_build_summary_with_env_failure(self):
        validator = ProductionValidator()
        report = ReadinessReport(report_id="r")
        env = EnvironmentValidationResult(validator_name="E", passed=False)
        report.environment = env
        summary = validator._build_summary(report, 1, 0)
        assert "Environment validation failed" in summary

    @pytest.mark.asyncio
    async def test_build_summary_with_infra_failure(self):
        validator = ProductionValidator()
        report = ReadinessReport(report_id="r")
        infra = InfrastructureValidationResult(validator_name="I", passed=False)
        report.infrastructure = infra
        summary = validator._build_summary(report, 1, 0)
        assert "Infrastructure validation failed" in summary

    @pytest.mark.asyncio
    async def test_build_summary_with_arch_failure(self):
        validator = ProductionValidator()
        report = ReadinessReport(report_id="r")
        arch = ArchitectureValidationResult(validator_name="A", passed=False)
        report.architecture = arch
        summary = validator._build_summary(report, 1, 0)
        assert "Architecture validation failed" in summary

    @pytest.mark.asyncio
    async def test_build_summary_no_failures(self):
        validator = ProductionValidator()
        report = ReadinessReport(report_id="r")
        summary = validator._build_summary(report, 0, 0)
        assert "0 failures" in summary
        assert "All validations passed" in summary

    @pytest.mark.asyncio
    async def test_build_summary_includes_warnings(self):
        validator = ProductionValidator()
        report = ReadinessReport(report_id="r")
        summary = validator._build_summary(report, 0, 3)
        assert "3 warnings" in summary


class TestProductionValidatorBuildRecommendations:
    @pytest.mark.asyncio
    async def test_recommend_database_backup(self):
        validator = ProductionValidator()
        backup = BackupValidationResult(validator_name="B", passed=True, database_backup_valid=False)
        report = ReadinessReport(report_id="r", backup=backup)
        recs = validator._build_recommendations(report)
        assert any("database backup" in r.lower() for r in recs)

    @pytest.mark.asyncio
    async def test_recommend_redis_backup(self):
        validator = ProductionValidator()
        backup = BackupValidationResult(validator_name="B", passed=True, redis_backup_valid=False)
        report = ReadinessReport(report_id="r", backup=backup)
        recs = validator._build_recommendations(report)
        assert any("redis" in r.lower() for r in recs)

    @pytest.mark.asyncio
    async def test_recommend_ai_provider(self):
        validator = ProductionValidator()
        config = ConfigurationValidationResult(validator_name="C", passed=True, ai_providers_configured=False)
        report = ReadinessReport(report_id="r", configuration=config)
        recs = validator._build_recommendations(report)
        assert any("ai provider" in r.lower() for r in recs)

    @pytest.mark.asyncio
    async def test_recommend_version_tag(self):
        validator = ProductionValidator()
        release = ReleaseValidationResult(validator_name="R", passed=True, version_tagged=False)
        report = ReadinessReport(report_id="r", release=release)
        recs = validator._build_recommendations(report)
        assert any("tag" in r.lower() for r in recs)

    @pytest.mark.asyncio
    async def test_recommend_slow_startup(self):
        validator = ProductionValidator()
        perf = PerformanceValidationResult(startup_time_ms=6000)
        report = ReadinessReport(report_id="r", performance=perf)
        recs = validator._build_recommendations(report)
        assert any("startup time" in r.lower() for r in recs)

    @pytest.mark.asyncio
    async def test_recommend_high_memory(self):
        validator = ProductionValidator()
        perf = PerformanceValidationResult(memory_usage_mb=600)
        report = ReadinessReport(report_id="r", performance=perf)
        recs = validator._build_recommendations(report)
        assert any("memory" in r.lower() for r in recs)

    @pytest.mark.asyncio
    async def test_no_recommendations_when_all_good(self):
        validator = ProductionValidator()
        backup = BackupValidationResult(validator_name="B", passed=True, database_backup_valid=True,
                                         redis_backup_valid=True)
        config = ConfigurationValidationResult(validator_name="C", passed=True, ai_providers_configured=True)
        release = ReleaseValidationResult(validator_name="R", passed=True, version_tagged=True)
        perf = PerformanceValidationResult(startup_time_ms=100, memory_usage_mb=100)
        report = ReadinessReport(report_id="r", backup=backup, configuration=config,
                                 release=release, performance=perf)
        recs = validator._build_recommendations(report)
        assert len(recs) == 0


class TestProductionValidatorEvaluateChecklistItem:
    @pytest.mark.asyncio
    async def test_evaluate_jwt_secret_passed(self):
        validator = ProductionValidator()
        config = ConfigurationValidationResult(validator_name="C", passed=True, secrets_configured=True)
        report = ReadinessReport(report_id="r", configuration=config)
        from production.models import ChecklistItem
        item = ChecklistItem(category="Configuration", name="JWT Secret", description="d")
        status = validator._evaluate_checklist_item(item, report)
        assert status == ValidationStatus.PASSED

    @pytest.mark.asyncio
    async def test_evaluate_jwt_secret_failed_required(self):
        validator = ProductionValidator()
        config = ConfigurationValidationResult(validator_name="C", passed=True, secrets_configured=False)
        report = ReadinessReport(report_id="r", configuration=config)
        from production.models import ChecklistItem
        item = ChecklistItem(category="Configuration", name="JWT Secret", description="d", required=True)
        status = validator._evaluate_checklist_item(item, report)
        assert status == ValidationStatus.FAILED

    @pytest.mark.asyncio
    async def test_evaluate_jwt_secret_warning_optional(self):
        validator = ProductionValidator()
        config = ConfigurationValidationResult(validator_name="C", passed=True, secrets_configured=False)
        report = ReadinessReport(report_id="r", configuration=config)
        from production.models import ChecklistItem
        item = ChecklistItem(category="Configuration", name="JWT Secret", description="d", required=False)
        status = validator._evaluate_checklist_item(item, report)
        assert status == ValidationStatus.WARNING

    @pytest.mark.asyncio
    async def test_evaluate_unmapped_item_returns_passed(self):
        validator = ProductionValidator()
        report = ReadinessReport(report_id="r")
        from production.models import ChecklistItem
        item = ChecklistItem(category="Unknown", name="Unknown Item", description="d")
        status = validator._evaluate_checklist_item(item, report)
        assert status == ValidationStatus.PASSED


class TestProductionValidatorRenderMethods:
    @pytest.mark.asyncio
    async def test_render_report_without_report(self):
        validator = ProductionValidator()
        result = validator.render_report()
        assert "No report available" in result

    @pytest.mark.asyncio
    async def test_render_report_with_report(self):
        validator = ProductionValidator()
        await validator.validate_all()
        result = validator.render_report()
        assert "GO FOR PRODUCTION" in result or "NO-GO" in result
        assert "# AI Platform Readiness Report" in result

    @pytest.mark.asyncio
    async def test_render_report_with_explicit_report(self):
        validator = ProductionValidator()
        report = ReadinessReport(report_id="custom-1", overall_ready=True, summary="ok")
        result = validator.render_report(report)
        assert "custom-1" in result
        assert "GO FOR PRODUCTION" in result

    @pytest.mark.asyncio
    async def test_render_checklist_without_report(self):
        validator = ProductionValidator()
        result = validator.render_checklist()
        assert "No checklist available" in result

    @pytest.mark.asyncio
    async def test_render_checklist_with_report(self):
        validator = ProductionValidator()
        await validator.validate_all()
        result = validator.render_checklist()
        assert "# Production Readiness Checklist" in result

    @pytest.mark.asyncio
    async def test_render_checklist_with_explicit_report(self):
        validator = ProductionValidator()
        from production.models import ProductionChecklist
        cl = ProductionChecklist(total=1, passed=1)
        report = ReadinessReport(report_id="r1", checklist=cl)
        result = validator.render_checklist(report)
        assert "# Production Readiness Checklist" in result


class TestProductionValidatorReadinessReport:
    @pytest.mark.asyncio
    async def test_readiness_report_before_validation(self):
        validator = ProductionValidator()
        result = validator.readiness_report()
        assert result["initialized"] is False
        assert result["last_report_id"] is None
        assert result["overall_ready"] is False

    @pytest.mark.asyncio
    async def test_readiness_report_after_validation(self):
        validator = ProductionValidator()
        await validator.validate_all()
        result = validator.readiness_report()
        assert result["initialized"] is False
        assert result["last_report_id"] is not None
        assert isinstance(result["overall_ready"], bool)
