from typing import Dict

from common.json_schema import TwinState
from common.utils import setup_logger, save_json
from common.config import STATE_DIRECTORY


class SyncEngine:
    """
    Handles synchronization of Digital Twin states.
    Maintains the latest state of each Digital Twin and
    saves it as a JSON file.
    """

    def __init__(self):
        self.logger = setup_logger("SyncEngine")
        self._latest_states: Dict[str, TwinState] = {}

    def update_state(self, state: TwinState) -> None:
        """
        Update the latest state of a Digital Twin and
        save it to a JSON file.
        """

        self._latest_states[state.system] = state

        filepath = STATE_DIRECTORY / f"{state.system}.json"

        save_json(
            state.to_dict(),
            filepath
        )

        self.logger.info(f"{state.system} synchronized successfully.")

    def get_state(self, system_name: str):
        """
        Return the latest state of a Digital Twin.
        """
        return self._latest_states.get(system_name)

    def get_all_states(self) -> Dict[str, TwinState]:
        """
        Return all synchronized states.
        """
        return self._latest_states

    def remove_state(self, system_name: str) -> None:
        """
        Remove a Digital Twin state from memory.
        """
        self._latest_states.pop(system_name, None)

    def clear(self) -> None:
        """
        Clear all synchronized states.
        """
        self._latest_states.clear()
        self.logger.info("All synchronized states cleared.")

    def count(self) -> int:
        """
        Return the number of synchronized Digital Twins.
        """
        return len(self._latest_states)