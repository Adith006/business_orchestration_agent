from enum import StrEnum


class AIEmployeeStatus(StrEnum):
    DRAFT = "draft"
    CONFIGURED = "configured"
    ACTIVE = "active"
    PAUSED = "paused"
    DEACTIVATED = "deactivated"


ALLOWED_STATUS_TRANSITIONS = {
    AIEmployeeStatus.DRAFT: {
        AIEmployeeStatus.CONFIGURED,
        AIEmployeeStatus.DEACTIVATED,
    },
    AIEmployeeStatus.CONFIGURED: {
        AIEmployeeStatus.ACTIVE,
        AIEmployeeStatus.DEACTIVATED,
    },
    AIEmployeeStatus.ACTIVE: {
        AIEmployeeStatus.PAUSED,
        AIEmployeeStatus.DEACTIVATED,
    },
    AIEmployeeStatus.PAUSED: {
        AIEmployeeStatus.ACTIVE,
        AIEmployeeStatus.DEACTIVATED,
    },
    AIEmployeeStatus.DEACTIVATED: set(),
}
