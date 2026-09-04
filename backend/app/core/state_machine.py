from enum import Enum
from typing import Set, Dict

class MigrationState(str, Enum):
    CREATED = "CREATED"
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    QUEUED = "QUEUED"
    ANALYZING = "ANALYZING"
    SECURITY_SCANNING = "SECURITY_SCANNING"
    AIR_GENERATION = "AIR_GENERATION"
    PLANNING = "PLANNING"
    GENERATING = "GENERATING"
    REVIEWING = "REVIEWING"
    VALIDATING = "VALIDATING"
    BUILDING = "BUILDING"
    REMEDIATING = "REMEDIATING"
    FINAL_SECURITY_SCAN = "FINAL_SECURITY_SCAN"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class InvalidStateTransitionError(Exception):
    pass

# Explicit map of allowed transitions from a given state
VALID_TRANSITIONS: Dict[str, Set[str]] = {
    MigrationState.CREATED: {MigrationState.UPLOADING, MigrationState.CANCELLED},
    MigrationState.UPLOADING: {MigrationState.UPLOADED, MigrationState.FAILED, MigrationState.CANCELLED},
    MigrationState.UPLOADED: {MigrationState.QUEUED, MigrationState.FAILED},
    MigrationState.QUEUED: {MigrationState.ANALYZING, MigrationState.CANCELLED, MigrationState.FAILED},
    MigrationState.ANALYZING: {MigrationState.SECURITY_SCANNING, MigrationState.FAILED, MigrationState.QUEUED}, # QUEUED for retry
    MigrationState.SECURITY_SCANNING: {MigrationState.AIR_GENERATION, MigrationState.FAILED, MigrationState.QUEUED},
    MigrationState.AIR_GENERATION: {MigrationState.PLANNING, MigrationState.FAILED, MigrationState.QUEUED},
    MigrationState.PLANNING: {MigrationState.GENERATING, MigrationState.FAILED, MigrationState.QUEUED},
    MigrationState.GENERATING: {MigrationState.REVIEWING, MigrationState.FAILED, MigrationState.QUEUED},
    MigrationState.REVIEWING: {MigrationState.VALIDATING, MigrationState.FAILED, MigrationState.QUEUED},
    MigrationState.VALIDATING: {MigrationState.BUILDING, MigrationState.REMEDIATING, MigrationState.FAILED},
    MigrationState.BUILDING: {MigrationState.FINAL_SECURITY_SCAN, MigrationState.FAILED},
    MigrationState.REMEDIATING: {MigrationState.VALIDATING, MigrationState.FAILED},
    MigrationState.FINAL_SECURITY_SCAN: {MigrationState.COMPLETED, MigrationState.FAILED},
    MigrationState.COMPLETED: set(), # Terminal state
    MigrationState.FAILED: {MigrationState.QUEUED}, # Allow manual retry from failed
    MigrationState.CANCELLED: set(), # Terminal state
}

def validate_transition(current_state: str, new_state: str) -> bool:
    """
    Validates if a transition from current_state to new_state is allowed.
    Raises InvalidStateTransitionError if it is not allowed.
    """
    if current_state not in VALID_TRANSITIONS:
        raise InvalidStateTransitionError(f"Unknown current state: {current_state}")
    
    if new_state not in VALID_TRANSITIONS[current_state]:
        raise InvalidStateTransitionError(f"Invalid transition from {current_state} to {new_state}")
        
    return True
