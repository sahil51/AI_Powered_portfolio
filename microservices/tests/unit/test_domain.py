from domain.enums.intent import IntentType
from domain.enums.meeting_type import MeetingType
from domain.enums.workflow_state import WorkflowState
from domain.models.conversation import ConversationState, Message
from domain.models.meeting import MeetingRequest
from domain.models.user import UserProfile


class TestEnums:
    def test_intent_values(self):
        assert IntentType.GREETING.value == "greeting"
        assert IntentType.SCHEDULE_CONSULTATION.value == "schedule_consultation"

    def test_meeting_type_values(self):
        assert MeetingType.GOOGLE_MEET.value == "google_meet"
        assert MeetingType.PHONE_CALL.value == "phone_call"
        assert MeetingType.IN_PERSON.value == "in_person"

    def test_workflow_state_values(self):
        assert WorkflowState.IDLE.value == "idle"
        assert WorkflowState.COLLECTING.value == "collecting"
        assert WorkflowState.CONFIRMING.value == "confirming"
        assert WorkflowState.COMPLETED.value == "completed"


class TestUserModel:
    def test_user_creation(self):
        user = UserProfile(id="test-id", name="John Doe", email="john@example.com")
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.user_type == "visitor"


class TestMeetingModel:
    def test_meeting_request_creation(self):
        meeting = MeetingRequest(
            full_name="John Doe",
            email="john@example.com",
            contact_number="+1234567890",
            company_name="ACME Inc",
            company_address="123 Main St",
            meeting_purpose="Discuss project",
            preferred_date="2024-01-15",
            preferred_time="10:00",
            timezone="America/New_York",
            meeting_type="google_meet",
        )
        assert meeting.full_name == "John Doe"
        assert meeting.meeting_type == "google_meet"


class TestConversationState:
    def test_conversation_creation(self):
        msg = Message(role="user", content="Hello")
        conv = ConversationState(conversation_id="conv-1", user_id="user-1", messages=[msg])
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "Hello"
        assert conv.workflow_state == "idle"
