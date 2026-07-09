from __future__ import annotations

import time
from typing import Any

from monitoring.logger import logger
from security.models import AuditAction, AuditEntry

AuditEvent = AuditAction


class AuditLogger:
    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def record(
        self,
        action: str | AuditAction,
        actor_id: str = "",
        resource_type: str = "",
        resource_id: str = "",
        outcome: str = "success",
        metadata: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> AuditEntry:
        action_str = action.value if isinstance(action, AuditAction) else action
        entry = AuditEntry(
            action=action_str,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            timestamp=time.time(),
            metadata=metadata or {},
            correlation_id=correlation_id,
        )
        if self._enabled:
            self._entries.append(entry)
            logger.info(
                f"AUDIT: {action_str} on {resource_type}",
                extra={
                    "audit": True,
                    "action": action_str,
                    "actor_id": actor_id,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "outcome": outcome,
                    "correlation_id": correlation_id,
                    "metadata": metadata or {},
                },
            )
        return entry

    def record_authentication(
        self,
        user_id: str,
        outcome: str = "success",
        metadata: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> AuditEntry:
        return self.record(
            action=AuditAction.AUTHENTICATION,
            actor_id=user_id,
            resource_type="session",
            outcome=outcome,
            metadata=metadata,
            correlation_id=correlation_id,
        )

    def record_authorization(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str = "",
        outcome: str = "success",
        metadata: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> AuditEntry:
        return self.record(
            action=AuditAction.AUTHORIZATION,
            actor_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            metadata=metadata,
            correlation_id=correlation_id,
        )

    def record_workflow_execution(
        self,
        workflow_id: str,
        outcome: str = "success",
        metadata: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> AuditEntry:
        return self.record(
            action=AuditAction.WORKFLOW_EXECUTION,
            resource_type="workflow",
            resource_id=workflow_id,
            outcome=outcome,
            metadata=metadata,
            correlation_id=correlation_id,
        )

    def record_knowledge_change(
        self,
        document_id: str,
        outcome: str = "success",
        metadata: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> AuditEntry:
        return self.record(
            action=AuditAction.KNOWLEDGE_CHANGE,
            resource_type="knowledge",
            resource_id=document_id,
            outcome=outcome,
            metadata=metadata,
            correlation_id=correlation_id,
        )

    def record_meeting_request(
        self,
        meeting_id: str,
        actor_id: str = "",
        outcome: str = "success",
        metadata: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> AuditEntry:
        return self.record(
            action=AuditAction.MEETING_REQUEST,
            actor_id=actor_id,
            resource_type="meeting",
            resource_id=meeting_id,
            outcome=outcome,
            metadata=metadata,
            correlation_id=correlation_id,
        )

    def record_configuration_change(
        self,
        config_key: str,
        actor_id: str = "",
        outcome: str = "success",
        metadata: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> AuditEntry:
        return self.record(
            action=AuditAction.CONFIGURATION_CHANGE,
            actor_id=actor_id,
            resource_type="configuration",
            resource_id=config_key,
            outcome=outcome,
            metadata=metadata,
            correlation_id=correlation_id,
        )

    def record_security_event(
        self,
        event_type: str,
        actor_id: str = "",
        outcome: str = "blocked",
        metadata: dict[str, Any] | None = None,
        correlation_id: str = "",
    ) -> AuditEntry:
        return self.record(
            action=AuditAction.SECURITY_EVENT,
            actor_id=actor_id,
            resource_type="security",
            resource_id=event_type,
            outcome=outcome,
            metadata=metadata,
            correlation_id=correlation_id,
        )

    def get_entries(self, limit: int = 100) -> list[AuditEntry]:
        return list(self._entries[-limit:])

    def get_entries_by_action(self, action: str, limit: int = 100) -> list[AuditEntry]:
        return [e for e in self._entries[-limit:] if e.action == action]

    def get_entries_by_actor(self, actor_id: str, limit: int = 100) -> list[AuditEntry]:
        return [e for e in self._entries[-limit:] if e.actor_id == actor_id]

    def audit_report(self, limit: int = 100) -> list[dict[str, Any]]:
        entries = self._entries[-limit:]
        return [
            {
                "action": e.action,
                "actor_id": e.actor_id,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "outcome": e.outcome,
                "timestamp": e.timestamp,
                "metadata": e.metadata,
                "correlation_id": e.correlation_id,
            }
            for e in entries
        ]

    def clear(self) -> None:
        self._entries.clear()
