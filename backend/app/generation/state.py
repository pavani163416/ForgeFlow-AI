from typing import Optional
from app.core.state_machine import validate_transition, InvalidStateTransitionError
from app.generation.repository import GenerationRepository
import logging

logger = logging.getLogger(__name__)

class StateTransitionService:
    """
    Authoritative state transition mechanism.
    Worker -> GenerationOrchestrator -> StateTransitionService -> GenerationRepository -> PostgreSQL
    """
    def __init__(self, repository: GenerationRepository):
        self.repo = repository
        
    def transition_generation_run(self, run_id: str, current_state: str, new_state: str, user_id: str) -> bool:
        """
        Validates the transition according to authoritative rules and persists it atomically.
        """
        try:
            # 1. Authoritative validation
            validate_transition(current_state, new_state)
            
            # 2. Persist to repository (which executes against PostgreSQL)
            # A true atomic update would ensure current_state matches DB state in the WHERE clause.
            success = self.repo.atomic_update_generation_status(run_id, current_state, new_state, user_id)
            if not success:
                logger.warning(f"Failed to transition {run_id} from {current_state} to {new_state}: atomic update failed.")
                return False
                
            return True
        except InvalidStateTransitionError as e:
            logger.error(f"Invalid state transition requested for {run_id}: {e}")
            raise
