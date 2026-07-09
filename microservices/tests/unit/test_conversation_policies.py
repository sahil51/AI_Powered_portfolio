
from domain.conversation.policies import ConversationPolicies


class TestConversationPolicies:
    def test_default_policies(self):
        policies = ConversationPolicies()
        assert policies.conversation_timeout_minutes == 30
        assert policies.archive_after_days == 90
        assert policies.max_messages_per_conversation == 1000
        assert policies.max_message_length == 10000

    def test_should_timeout(self):
        policies = ConversationPolicies(conversation_timeout_minutes=30)
        assert policies.should_timeout(31)
        assert not policies.should_timeout(29)

    def test_should_archive(self):
        policies = ConversationPolicies(archive_after_days=90)
        assert policies.should_archive(91)
        assert not policies.should_archive(89)

    def test_can_resume(self):
        policies = ConversationPolicies(resume_after_pause_max_minutes=60)
        assert policies.can_resume(30)
        assert policies.can_resume(60)
        assert not policies.can_resume(61)

    def test_should_expire_retention(self):
        policies = ConversationPolicies(retention_days=365)
        assert policies.should_expire_retention(366)
        assert not policies.should_expire_retention(364)

    def test_exceeds_max_messages(self):
        policies = ConversationPolicies(max_messages_per_conversation=100)
        assert policies.exceeds_max_messages(100)
        assert not policies.exceeds_max_messages(99)

    def test_exceeds_max_message_length(self):
        policies = ConversationPolicies(max_message_length=100)
        assert policies.exceeds_max_message_length(101)
        assert not policies.exceeds_max_message_length(100)

    def test_exceeds_max_participants(self):
        policies = ConversationPolicies(max_participants=5)
        assert policies.exceeds_max_participants(6)
        assert not policies.exceeds_max_participants(5)

    def test_timeout_seconds(self):
        policies = ConversationPolicies(conversation_timeout_minutes=30)
        assert policies.timeout_seconds == 1800

    def test_resume_timeout_seconds(self):
        policies = ConversationPolicies(resume_after_pause_max_minutes=60)
        assert policies.resume_timeout_seconds == 3600
