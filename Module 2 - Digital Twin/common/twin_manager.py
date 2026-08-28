from typing import Dict, Any


class TwinManager:
    """
    Central registry and manager for all Digital Twin modules.
    """

    def __init__(self):
        self._twins: Dict[str, Any] = {}

    def register_twin(self, system_name: str, twin: Any) -> None:
        """
        Register a Digital Twin.
        """
        self._twins[system_name] = twin

    def remove_twin(self, system_name: str) -> None:
        """
        Remove a registered Digital Twin.
        """
        self._twins.pop(system_name, None)

    def get_twin(self, system_name: str):
        """
        Get a specific Digital Twin.
        """
        return self._twins.get(system_name)

    def get_all_twins(self) -> Dict[str, Any]:
        """
        Return all registered Digital Twins.
        """
        return self._twins

    def is_registered(self, system_name: str) -> bool:
        """
        Check whether a Digital Twin is registered.
        """
        return system_name in self._twins

    def count(self) -> int:
        """
        Return the total number of registered Digital Twins.
        """
        return len(self._twins)

    def clear(self) -> None:
        """
        Remove all registered Digital Twins.
        """
        self._twins.clear()

    def update_all(self) -> None:
        """
        Update every registered Digital Twin.
        """
        for twin in self._twins.values():
            if hasattr(twin, "update_state"):
                twin.update_state()

    def __repr__(self) -> str:
        """
        String representation of TwinManager.
        """
        return f"TwinManager(registered_twins={list(self._twins.keys())})"