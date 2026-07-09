import pytest

from domain.conversation.aggregate import Conversation, ConversationPolicyError
from domain.conversation.policies import ConversationPolicies
from domain.conversation.state import ConversationState, IllegalStateTransitionError
from domain.conversation.value_objects import (
    Attachment,
    ConversationId,
    Message,
    MessageType,
    Participant,
    ParticipantId,
    ParticipantRole,
)


class TestConversationAggregate:
    def test_create_conversation(self):
        conv = Conversation(
            conversation_id=ConversationId(),
            user_id="user-1",
            session_id="session-1",
            identity_source="anonymous",
        )
        assert conv.state == ConversationState.CREATED
        assert conv.user_id == "user-1"
        assert conv.message_count == 0
        assert conv.participant_count == 0
        assert not conv.is_terminal
        assert not conv.is_paused
        assert conv.version == 1

    def test_activate_conversation(self):
        conv = self._make_conversation()
        conv.activate()
        assert conv.state == ConversationState.ACTIVE
        assert conv.is_active
        assert conv.version == 2

    def test_add_user_message(self):
        conv = self._make_conversation()
        conv.activate()
        msg = Message(content="Hello", message_type=MessageType.USER)
        conv.add_message(msg)
        assert conv.message_count == 1
        assert conv.messages[0].content == "Hello"
        assert conv.version == 3

    def test_add_multiple_messages(self):
        conv = self._make_conversation()
        conv.activate()
        conv.add_message(Message(content="Hello", message_type=MessageType.USER))
        conv.add_message(Message(content="Hi there!", message_type=MessageType.ASSISTANT))
        conv.add_message(Message(content="How are you?", message_type=MessageType.USER))
        assert conv.message_count == 3

    def test_cannot_add_message_to_created(self):
        conv = self._make_conversation()
        msg = Message(content="Hello", message_type=MessageType.USER)
        with pytest.raises(IllegalStateTransitionError):
            conv.add_message(msg)

    def test_cannot_add_message_to_completed(self):
        conv = self._make_conversation()
        conv.activate()
        conv.complete()
        with pytest.raises(IllegalStateTransitionError):
            conv.add_message(Message(content="Hello", message_type=MessageType.USER))

    def test_cannot_add_message_to_cancelled(self):
        conv = self._make_conversation()
        conv.activate()
        conv.cancel()
        with pytest.raises(IllegalStateTransitionError):
            conv.add_message(Message(content="Hello", message_type=MessageType.USER))

    def test_exceeds_max_messages(self):
        policies = ConversationPolicies(max_messages_per_conversation=2)
        conv = self._make_conversation(policies=policies)
        conv.activate()
        conv.add_message(Message(content="1", message_type=MessageType.USER))
        conv.add_message(Message(content="2", message_type=MessageType.ASSISTANT))
        with pytest.raises(ConversationPolicyError):
            conv.add_message(Message(content="3", message_type=MessageType.USER))

    def test_exceeds_max_message_length(self):
        policies = ConversationPolicies(max_message_length=10)
        conv = self._make_conversation(policies=policies)
        conv.activate()
        with pytest.raises(ConversationPolicyError):
            conv.add_message(Message(content="x" * 11, message_type=MessageType.USER))

    def test_pause_and_resume(self):
        conv = self._make_conversation()
        conv.activate()
        conv.pause(reason="Need info")
        assert conv.is_paused
        assert conv.state == ConversationState.PAUSED
        assert conv.paused_at is not None

        conv.resume()
        assert conv.state == ConversationState.ACTIVE
        assert not conv.is_paused
        assert conv.paused_at is None

    def test_complete_conversation(self):
        conv = self._make_conversation()
        conv.activate()
        conv.add_message(Message(content="Hello", message_type=MessageType.USER))
        conv.complete(summary="Test summary")
        assert conv.state == ConversationState.COMPLETED
        assert conv.is_terminal
        assert conv.summary == "Test summary"
        assert conv.completed_at is not None

    def test_cancel_conversation(self):
        conv = self._make_conversation()
        conv.activate()
        conv.cancel(reason="User requested")
        assert conv.state == ConversationState.CANCELLED
        assert conv.is_terminal

    def test_archive_from_completed(self):
        conv = self._make_conversation()
        conv.activate()
        conv.complete()
        conv.archive()
        assert conv.state == ConversationState.ARCHIVED

    def test_archive_from_cancelled(self):
        conv = self._make_conversation()
        conv.activate()
        conv.cancel()
        conv.archive()
        assert conv.state == ConversationState.ARCHIVED

    def test_invalid_transition_raises(self):
        conv = self._make_conversation()
        with pytest.raises(IllegalStateTransitionError):
            conv.complete()

    def test_add_participant(self):
        conv = self._make_conversation()
        conv.activate()
        participant = Participant(
            participant_id=ParticipantId(value="user-2"),
            role=ParticipantRole.PARTICIPANT,
        )
        conv.add_participant(participant)
        assert conv.participant_count == 1

    def test_duplicate_participant_raises(self):
        conv = self._make_conversation()
        conv.activate()
        participant = Participant(
            participant_id=ParticipantId(value="user-2"),
            role=ParticipantRole.PARTICIPANT,
        )
        conv.add_participant(participant)
        with pytest.raises(ConversationPolicyError):
            conv.add_participant(participant)

    def test_remove_participant(self):
        conv = self._make_conversation()
        conv.activate()
        pid = ParticipantId(value="user-2")
        conv.add_participant(Participant(participant_id=pid))
        conv.remove_participant(pid)
        assert conv.participant_count == 0

    def test_get_messages_by_type(self):
        conv = self._make_conversation()
        conv.activate()
        conv.add_message(Message(content="Hello", message_type=MessageType.USER))
        conv.add_message(Message(content="Hi", message_type=MessageType.ASSISTANT))
        conv.add_message(Message(content="How are you?", message_type=MessageType.USER))
        user_msgs = conv.get_messages(MessageType.USER)
        assert len(user_msgs) == 2
        assistant_msgs = conv.get_messages(MessageType.ASSISTANT)
        assert len(assistant_msgs) == 1

    def test_drain_events(self):
        conv = self._make_conversation()
        conv.activate()
        events = conv.drain_events()
        assert len(events) >= 1
        assert conv.events == []

    def test_conversation_has_owner_participant(self):
        conv = self._make_conversation()
        conv.add_participant(
            Participant(
                participant_id=ParticipantId(value="user-1"),
                role=ParticipantRole.OWNER,
            )
        )
        assert conv.participant_count == 1

    def test_system_message(self):
        conv = self._make_conversation()
        conv.activate()
        msg = Message(content="System update", message_type=MessageType.SYSTEM)
        conv.add_message(msg)
        assert conv.message_count == 1
        assert conv.messages[0].is_system_message

    def test_message_with_attachment(self):
        conv = self._make_conversation()
        conv.activate()
        attachment = Attachment(filename="test.pdf", content_type="application/pdf", size_bytes=1024)
        msg = Message(content="Here is a file", message_type=MessageType.USER, attachments=[attachment])
        conv.add_message(msg)
        assert len(conv.messages[0].attachments) == 1
        assert conv.messages[0].attachments[0].filename == "test.pdf"

    def test_expire_conversation(self):
        conv = self._make_conversation()
        conv.expire()
        assert len(conv.events) == 1
        assert conv.events[0].__class__.__name__ == "ConversationExpired"

    def test_snapshot_immutability(self):
        conv = self._make_conversation()
        conv.activate()
        conv.add_message(Message(content="Hello", message_type=MessageType.USER))
        summary_dict = {
            "conversation_id": str(conv.conversation_id),
            "state": conv.state.value,
            "message_count": conv.message_count,
        }
        assert summary_dict["message_count"] == 1
        assert summary_dict["state"] == "active"

    @staticmethod
    def _make_conversation(policies: ConversationPolicies | None = None) -> Conversation:
        return Conversation(
            conversation_id=ConversationId(),
            user_id="test-user",
            session_id="test-session",
            identity_source="anonymous",
            policies=policies or ConversationPolicies(),
        )


class TestConversationStateMachine:
    def test_initial_state(self):
        from domain.conversation.state import ConversationStateMachine
        sm = ConversationStateMachine()
        assert sm.current_state == ConversationState.CREATED

    def test_allowed_transitions_from_created(self):
        from domain.conversation.state import ConversationStateMachine
        sm = ConversationStateMachine()
        allowed = sm.allowed_transitions()
        assert ConversationState.ACTIVE in allowed
        assert ConversationState.CANCELLED in allowed
        assert ConversationState.ARCHIVED in allowed
        assert ConversationState.PAUSED not in allowed

    def test_transition_to_active(self):
        from domain.conversation.state import ConversationStateMachine
        sm = ConversationStateMachine()
        sm.transition_to(ConversationState.ACTIVE)
        assert sm.current_state == ConversationState.ACTIVE

    def test_invalid_transition_raises(self):
        from domain.conversation.state import ConversationStateMachine, IllegalStateTransitionError
        sm = ConversationStateMachine()
        with pytest.raises(IllegalStateTransitionError):
            sm.transition_to(ConversationState.COMPLETED)

    def test_terminal_states(self):
        from domain.conversation.state import ConversationStateMachine
        sm = ConversationStateMachine(ConversationState.COMPLETED)
        assert sm.is_terminal()
        sm2 = ConversationStateMachine(ConversationState.CANCELLED)
        assert sm2.is_terminal()
        sm3 = ConversationStateMachine(ConversationState.ARCHIVED)
        assert sm3.is_terminal()
        sm4 = ConversationStateMachine(ConversationState.ACTIVE)
        assert not sm4.is_terminal()

    def test_can_accept_messages(self):
        from domain.conversation.state import ConversationStateMachine
        assert ConversationStateMachine(ConversationState.ACTIVE).can_accept_messages()
        assert ConversationStateMachine(ConversationState.COLLECTING_INFORMATION).can_accept_messages()
        assert ConversationStateMachine(ConversationState.CREATED).can_accept_messages() is False
        assert ConversationStateMachine(ConversationState.COMPLETED).can_accept_messages() is False
        assert ConversationStateMachine(ConversationState.CANCELLED).can_accept_messages() is False
        assert ConversationStateMachine(ConversationState.PAUSED).can_accept_messages() is False

    def test_full_lifecycle(self):
        from domain.conversation.state import ConversationStateMachine
        sm = ConversationStateMachine()
        sm.transition_to(ConversationState.ACTIVE)
        sm.transition_to(ConversationState.PAUSED)
        sm.transition_to(ConversationState.RESUMED)
        sm.transition_to(ConversationState.COMPLETED)
        sm.transition_to(ConversationState.ARCHIVED)
        assert sm.current_state == ConversationState.ARCHIVED

    def test_collecting_information_cycle(self):
        from domain.conversation.state import ConversationStateMachine
        sm = ConversationStateMachine()
        sm.transition_to(ConversationState.ACTIVE)
        sm.transition_to(ConversationState.COLLECTING_INFORMATION)
        sm.transition_to(ConversationState.WAITING_CONFIRMATION)
        sm.transition_to(ConversationState.ACTIVE)
        assert sm.current_state == ConversationState.ACTIVE

    def test_waiting_external_workflow(self):
        from domain.conversation.state import ConversationStateMachine
        sm = ConversationStateMachine()
        sm.transition_to(ConversationState.ACTIVE)
        sm.transition_to(ConversationState.WAITING_EXTERNAL_WORKFLOW)
        sm.transition_to(ConversationState.ACTIVE)
        assert sm.current_state == ConversationState.ACTIVE

    def test_cannot_archive_active(self):
        from domain.conversation.state import ConversationStateMachine, IllegalStateTransitionError
        sm = ConversationStateMachine(ConversationState.ACTIVE)
        with pytest.raises(IllegalStateTransitionError):
            sm.transition_to(ConversationState.ARCHIVED)

    def test_cannot_resume_from_active(self):
        from domain.conversation.state import ConversationStateMachine, IllegalStateTransitionError
        sm = ConversationStateMachine(ConversationState.ACTIVE)
        with pytest.raises(IllegalStateTransitionError):
            sm.transition_to(ConversationState.RESUMED)
