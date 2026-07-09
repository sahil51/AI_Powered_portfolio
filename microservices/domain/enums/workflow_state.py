from enum import Enum


class WorkflowState(str, Enum):
    IDLE = "idle"
    COLLECTING = "collecting"
    VALIDATING = "validating"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
