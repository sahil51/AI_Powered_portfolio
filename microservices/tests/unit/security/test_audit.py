import pytest

from security.audit_logger import AuditLogger
from security.models import AuditAction


class TestAuditLogger:
    @pytest.fixture
    def logger(self):
        return AuditLogger()

    def test_record(self, logger):
        entry = logger.record("test_action", actor_id="user-1", resource_type="document")
        assert entry.action == "test_action"
        assert entry.actor_id == "user-1"
        assert entry.resource_type == "document"

    def test_record_authentication(self, logger):
        entry = logger.record_authentication("user-1")
        assert entry.action == AuditAction.AUTHENTICATION.value

    def test_record_authorization(self, logger):
        entry = logger.record_authorization("user-1", "document", "doc-1")
        assert entry.action == AuditAction.AUTHORIZATION.value
        assert entry.resource_id == "doc-1"

    def test_record_workflow_execution(self, logger):
        entry = logger.record_workflow_execution("wf-1", outcome="success")
        assert entry.action == AuditAction.WORKFLOW_EXECUTION.value
        assert entry.resource_id == "wf-1"

    def test_record_knowledge_change(self, logger):
        entry = logger.record_knowledge_change("doc-1")
        assert entry.action == AuditAction.KNOWLEDGE_CHANGE.value

    def test_record_meeting_request(self, logger):
        entry = logger.record_meeting_request("mtg-1", actor_id="user-1")
        assert entry.action == AuditAction.MEETING_REQUEST.value

    def test_record_configuration_change(self, logger):
        entry = logger.record_configuration_change("rate_limit", actor_id="admin")
        assert entry.action == AuditAction.CONFIGURATION_CHANGE.value

    def test_record_security_event(self, logger):
        entry = logger.record_security_event("unauthorized_access", actor_id="user-1")
        assert entry.action == AuditAction.SECURITY_EVENT.value

    def test_get_entries(self, logger):
        logger.record("action1")
        logger.record("action2")
        entries = logger.get_entries(limit=10)
        assert len(entries) == 2

    def test_get_entries_by_action(self, logger):
        logger.record("login", actor_id="u1")
        logger.record("logout", actor_id="u1")
        login_entries = logger.get_entries_by_action("login")
        assert len(login_entries) == 1

    def test_get_entries_by_actor(self, logger):
        logger.record("action1", actor_id="user-a")
        logger.record("action2", actor_id="user-b")
        user_a_entries = logger.get_entries_by_actor("user-a")
        assert len(user_a_entries) == 1

    def test_disable_enable(self, logger):
        logger.disable()
        logger.record("silent_action")
        assert len(logger.get_entries()) == 0
        logger.enable()
        logger.record("audible_action")
        assert len(logger.get_entries()) == 1

    def test_audit_report(self, logger):
        logger.record("action1", actor_id="u1", resource_type="type1")
        report = logger.audit_report()
        assert len(report) == 1
        assert report[0]["action"] == "action1"

    def test_clear(self, logger):
        logger.record("test")
        logger.clear()
        assert len(logger.get_entries()) == 0
