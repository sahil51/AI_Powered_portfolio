from __future__ import annotations


class MeetingAgentError(Exception):
    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class MeetingCollectionError(MeetingAgentError):
    pass


class MeetingValidationError(MeetingAgentError):
    pass


class MeetingSubmissionError(MeetingAgentError):
    pass
