from __future__ import annotations


class ProductionError(Exception):
    pass


class ValidationError(ProductionError):
    pass


class ConfigurationValidationError(ValidationError):
    pass


class EnvironmentValidationError(ValidationError):
    pass


class DependencyValidationError(ValidationError):
    pass


class InfrastructureValidationError(ValidationError):
    pass


class DeploymentValidationError(ValidationError):
    pass


class BackupValidationError(ValidationError):
    pass


class RecoveryValidationError(ValidationError):
    pass


class ArchitectureValidationError(ValidationError):
    pass


class ReleaseValidationError(ValidationError):
    pass
