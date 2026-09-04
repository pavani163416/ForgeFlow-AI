import pytest
from app.core.state_machine import validate_transition, MigrationState, InvalidStateTransitionError

def test_valid_transitions():
    # Test a few explicitly allowed transitions
    assert validate_transition(MigrationState.CREATED.value, MigrationState.UPLOADING.value) is True
    assert validate_transition(MigrationState.UPLOADING.value, MigrationState.UPLOADED.value) is True
    assert validate_transition(MigrationState.ANALYZING.value, MigrationState.SECURITY_SCANNING.value) is True
    
    # Retry transitions
    assert validate_transition(MigrationState.ANALYZING.value, MigrationState.QUEUED.value) is True
    assert validate_transition(MigrationState.FAILED.value, MigrationState.QUEUED.value) is True

def test_invalid_transitions():
    # Test explicitly forbidden transitions
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(MigrationState.CREATED.value, MigrationState.COMPLETED.value)
        
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(MigrationState.UPLOADING.value, MigrationState.ANALYZING.value)
        
    # Cannot go backward in the pipeline normally
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(MigrationState.BUILDING.value, MigrationState.ANALYZING.value)

def test_terminal_states():
    # COMPLETED and CANCELLED cannot transition anywhere
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(MigrationState.COMPLETED.value, MigrationState.QUEUED.value)
        
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(MigrationState.CANCELLED.value, MigrationState.QUEUED.value)

def test_unknown_state():
    with pytest.raises(InvalidStateTransitionError, match="Unknown current state"):
        validate_transition("NON_EXISTENT_STATE", MigrationState.UPLOADING.value)
