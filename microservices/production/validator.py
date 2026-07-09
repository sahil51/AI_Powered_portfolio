from __future__ import annotations

import time
from typing import Any

from monitoring.logger import logger
from production.checklist import ProductionChecklistBuilder
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
from production.reporting import ReportRenderer
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


class ProductionValidator:
    def __init__(self) -> None:
        self._initialized = False
        self._config_validator = ConfigurationValidator()
        self._env_validator = EnvironmentValidator()
        self._dep_validator = DependencyValidator()
        self._infra_validator = InfrastructureValidator()
        self._backup_validator = BackupValidator()
        self._recovery_validator = RecoveryValidator()
        self._arch_validator = ArchitectureValidator()
        self._deploy_validator = DeploymentValidator()
        self._release_validator = ReleaseValidator()
        self._perf_validator = PerformanceValidator()
        self._checklist_builder = ProductionChecklistBuilder()
        self._renderer = ReportRenderer()
        self._last_report: ReadinessReport | None = None

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def last_report(self) -> ReadinessReport | None:
        return self._last_report

    async def initialize(self) -> None:
        if self._initialized:
            return
        logger.info("Initializing production validator")
        self._initialized = True
        logger.info("Production validator initialized")

    async def shutdown(self) -> None:
        if not self._initialized:
            return
        logger.info("Shutting down production validator")
        self._initialized = False
        logger.info("Production validator shut down")

    async def validate_all(self) -> ReadinessReport:
        logger.info("Starting full production validation")
        report = ReadinessReport(
            report_id=f"readiness_{int(time.time())}",
            timestamp=time.time(),
        )
        report.configuration = await self._validate_configuration()
        report.environment = await self._validate_environment()
        report.dependencies = await self._validate_dependencies()
        report.infrastructure = await self._validate_infrastructure()
        report.backup = await self._validate_backup()
        report.recovery = await self._validate_recovery()
        report.architecture = await self._validate_architecture()
        report.deployment = await self._validate_deployment()
        report.release = await self._validate_release()
        report.performance = await self._validate_performance()
        report.checklist = self._build_checklist(report)
        failures = self._count_failures(report)
        warnings_count = self._count_warnings(report)
        report.overall_ready = failures == 0
        report.summary = self._build_summary(report, failures, warnings_count)
        report.recommendations = self._build_recommendations(report)
        self._last_report = report
        logger.info(f"Production validation complete: {'READY' if report.overall_ready else 'NOT READY'} ({failures} failures)")  # noqa: E501
        return report

    async def _validate_configuration(self) -> ConfigurationValidationResult:
        return await self._config_validator.validate()

    async def _validate_environment(self) -> EnvironmentValidationResult:
        return await self._env_validator.validate()

    async def _validate_dependencies(self) -> ValidationResult:
        return await self._dep_validator.validate()

    async def _validate_infrastructure(self) -> InfrastructureValidationResult:
        return await self._infra_validator.validate()

    async def _validate_backup(self) -> BackupValidationResult:
        return await self._backup_validator.validate()

    async def _validate_recovery(self) -> RecoveryValidationResult:
        return await self._recovery_validator.validate()

    async def _validate_architecture(self) -> ArchitectureValidationResult:
        return await self._arch_validator.validate()

    async def _validate_deployment(self) -> DeploymentValidationResult:
        return await self._deploy_validator.validate()

    async def _validate_release(self) -> ReleaseValidationResult:
        return await self._release_validator.validate()

    async def _validate_performance(self) -> PerformanceValidationResult:
        return await self._perf_validator.validate()

    def _build_checklist(self, report: ReadinessReport) -> ProductionChecklist:
        checklist = self._checklist_builder.build()
        for item in checklist.items:
            status = self._evaluate_checklist_item(item, report)
            item.status = status
            if status == ValidationStatus.PASSED:
                checklist.passed += 1
            elif status == ValidationStatus.FAILED:
                checklist.failed += 1
            elif status == ValidationStatus.WARNING:
                checklist.warning += 1
            elif status == ValidationStatus.SKIPPED:
                checklist.skipped += 1
        return checklist

    def _evaluate_checklist_item(self, item: Any, report: ReadinessReport) -> ValidationStatus:
        mapping: dict[str, Any] = {
            "JWT Secret": (report.configuration, "secrets_configured"),
            "Database URL": (report.configuration, "database_configured"),
            "Redis URL": (report.configuration, "redis_configured"),
            "AI Providers": (report.configuration, "ai_providers_configured"),
            "Database Backup": (report.backup, "database_backup_valid"),
            "Graceful Degradation": (report.recovery, "graceful_degradation_valid"),
            "Health Checks": (report.deployment, "health_checks_passing"),
        }
        mapped = mapping.get(item.name)
        if mapped:
            section, attr = mapped
            if section and getattr(section, attr, False):
                return ValidationStatus.PASSED
            return ValidationStatus.FAILED if item.required else ValidationStatus.WARNING
        return ValidationStatus.PASSED

    def _count_failures(self, report: ReadinessReport) -> int:
        sections = [
            report.configuration, report.environment, report.dependencies,
            report.infrastructure, report.backup, report.recovery,
            report.architecture, report.deployment, report.release,
        ]
        return sum(1 for s in sections if s and not s.passed)

    def _count_warnings(self, report: ReadinessReport) -> int:
        sections = [
            report.configuration, report.environment, report.dependencies,
            report.infrastructure, report.backup, report.recovery,
            report.architecture, report.deployment, report.release,
        ]
        count = 0
        for s in sections:
            if s:
                count += sum(1 for i in s.items if i.status == ValidationStatus.WARNING)
        return count

    def _build_summary(self, report: ReadinessReport, failures: int, warnings: int) -> str:
        parts = [f"Production readiness validation completed with {failures} failures and {warnings} warnings."]
        if report.configuration and not report.configuration.passed:
            parts.append("Configuration validation failed — check secrets and connection strings.")
        if report.environment and not report.environment.passed:
            parts.append("Environment validation failed — check Python version, dependencies, and resources.")
        if report.infrastructure and not report.infrastructure.passed:
            parts.append("Infrastructure validation failed — check database, Redis, and Celery connectivity.")
        if report.architecture and not report.architecture.passed:
            parts.append("Architecture validation failed — review DDD compliance and dependency rules.")
        if not failures:
            parts.append("All validations passed. The platform is ready for production deployment.")
        return " ".join(parts)

    def _build_recommendations(self, report: ReadinessReport) -> list[str]:
        recommendations: list[str] = []
        if report.backup and not report.backup.database_backup_valid:
            recommendations.append("Configure automated database backups and verify restore procedures.")
        if report.backup and not report.backup.redis_backup_valid:
            recommendations.append("Configure Redis persistence and backup strategy.")
        if report.configuration and not report.configuration.ai_providers_configured:
            recommendations.append("Configure at least one AI provider (Gemini or OpenAI).")
        if report.release and not report.release.version_tagged:
            recommendations.append("Tag the release version before deployment.")
        if report.performance:
            perf = report.performance
            if perf.startup_time_ms > 5000:
                recommendations.append(f"Optimize startup time ({perf.startup_time_ms:.0f}ms).")
            if perf.memory_usage_mb > 500:
                recommendations.append(f"Reduce memory footprint ({perf.memory_usage_mb:.0f}MB).")
        return recommendations

    def render_report(self, report: ReadinessReport | None = None) -> str:
        target = report or self._last_report
        if target is None:
            return "No report available. Run validate_all() first."
        return self._renderer.render_readiness_report(target)

    def render_checklist(self, report: ReadinessReport | None = None) -> str:
        target = report or self._last_report
        if target is None or target.checklist is None:
            return "No checklist available."
        return self._renderer.render_checklist_markdown(target.checklist)

    def readiness_report(self) -> dict[str, Any]:
        return {
            "initialized": self._initialized,
            "last_report_id": self._last_report.report_id if self._last_report else None,
            "overall_ready": self._last_report.overall_ready if self._last_report else False,
        }
