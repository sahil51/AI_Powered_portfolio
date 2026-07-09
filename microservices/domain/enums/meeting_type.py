from enum import Enum


class MeetingType(str, Enum):
    GOOGLE_MEET = "google_meet"
    PHONE_CALL = "phone_call"
    IN_PERSON = "in_person"
