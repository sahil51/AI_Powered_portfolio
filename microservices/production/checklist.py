from __future__ import annotations

from production.models import ChecklistItem, ProductionChecklist


class ProductionChecklistBuilder:
    def build(self) -> ProductionChecklist:
        items = [
            ChecklistItem(category="Configuration", name="JWT Secret", description="JWT secret key is configured", required=True),  # noqa: E501
            ChecklistItem(category="Configuration", name="Database URL", description="Database connection string is configured", required=True),  # noqa: E501
            ChecklistItem(category="Configuration", name="Redis URL", description="Redis connection string is configured", required=True),  # noqa: E501
            ChecklistItem(category="Configuration", name="Celery Broker", description="Celery broker URL is configured", required=True),  # noqa: E501
            ChecklistItem(category="Configuration", name="AI Providers", description="At least one AI provider is configured", required=True),  # noqa: E501
            ChecklistItem(category="Configuration", name="Embedding Provider", description="Embedding provider is configured", required=True),  # noqa: E501
            ChecklistItem(category="Configuration", name="Logging", description="Logging is configured (JSON format, level)", required=True),  # noqa: E501
            ChecklistItem(category="Configuration", name="Monitoring", description="Monitoring stack is configured", required=False),  # noqa: E501
            ChecklistItem(category="Secrets", name="API Keys", description="All API keys are configured", required=True),  # noqa: E501
            ChecklistItem(category="Secrets", name="Webhook Secret", description="Webhook verification secret is configured", required=True),  # noqa: E501
            ChecklistItem(category="Database", name="Migrations", description="Database migrations are applied", required=True),  # noqa: E501
            ChecklistItem(category="Database", name="Connectivity", description="Database is reachable", required=True),
            ChecklistItem(category="Database", name="Backup", description="Database backup strategy is in place", required=True),  # noqa: E501
            ChecklistItem(category="Redis", name="Connectivity", description="Redis is reachable", required=True),
            ChecklistItem(category="Redis", name="Backup", description="Redis backup/ persistence is configured", required=False),  # noqa: E501
            ChecklistItem(category="Celery", name="Availability", description="Celery workers are available", required=True),  # noqa: E501
            ChecklistItem(category="Knowledge", name="Storage", description="Knowledge storage is accessible", required=True),  # noqa: E501
            ChecklistItem(category="Knowledge", name="Embedding Pipeline", description="Embedding pipeline is operational", required=True),  # noqa: E501
            ChecklistItem(category="AI", name="Provider Health", description="AI providers are healthy", required=True),
            ChecklistItem(category="AI", name="Fallback Providers", description="Fallback AI providers are configured", required=False),  # noqa: E501
            ChecklistItem(category="Workflow", name="n8n Connectivity", description="n8n webhook endpoint is reachable", required=True),  # noqa: E501
            ChecklistItem(category="Monitoring", name="Health Checks", description="Health check endpoints are operational", required=True),  # noqa: E501
            ChecklistItem(category="Monitoring", name="Metrics", description="Prometheus metrics are exposed", required=False),  # noqa: E501
            ChecklistItem(category="Monitoring", name="Tracing", description="Distributed tracing is configured", required=False),  # noqa: E501
            ChecklistItem(category="Security", name="Rate Limiting", description="Rate limiting is configured", required=True),  # noqa: E501
            ChecklistItem(category="Security", name="JWT Validation", description="JWT token validation is configured", required=True),  # noqa: E501
            ChecklistItem(category="Security", name="CORS", description="CORS is properly configured", required=True),
            ChecklistItem(category="Security", name="Security Headers", description="Security headers middleware is enabled", required=True),  # noqa: E501
            ChecklistItem(category="Backup", name="Database Backup", description="Automated database backup is scheduled", required=True),  # noqa: E501
            ChecklistItem(category="Backup", name="Configuration Backup", description="Configuration files are backed up", required=True),  # noqa: E501
            ChecklistItem(category="Backup", name="Restore Procedure", description="Restore procedure is documented and tested", required=True),  # noqa: E501
            ChecklistItem(category="Disaster Recovery", name="RTO", description="Recovery Time Objective is defined", required=True),  # noqa: E501
            ChecklistItem(category="Disaster Recovery", name="RPO", description="Recovery Point Objective is defined", required=True),  # noqa: E501
            ChecklistItem(category="Disaster Recovery", name="Graceful Degradation", description="Graceful degradation paths are configured", required=True),  # noqa: E501
            ChecklistItem(category="Infrastructure", name="Docker", description="Docker composition is ready", required=False),  # noqa: E501
            ChecklistItem(category="Infrastructure", name="Resource Limits", description="CPU/ memory limits are configured", required=False),  # noqa: E501
            ChecklistItem(category="Release", name="Version Tag", description="Release version is tagged", required=True),  # noqa: E501
            ChecklistItem(category="Release", name="Changelog", description="Changelog is updated", required=False),
            ChecklistItem(category="Release", name="Tests Passing", description="All tests pass", required=True),
            ChecklistItem(category="Release", name="Lint Passing", description="Lint checks pass", required=True),
            ChecklistItem(category="Release", name="Type Checks Passing", description="Type checks pass", required=True),  # noqa: E501
        ]
        return ProductionChecklist(items=items, total=len(items))
