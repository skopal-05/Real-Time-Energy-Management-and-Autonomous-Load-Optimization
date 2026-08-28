from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class TwinState:
    """
    Standard data structure used by every Digital Twin module.
    """

    system: str
    timestamp: str
    power: float
    status: str
    temperature: float = 0.0
    health: str = "NORMAL"

    def to_dict(self) -> Dict:
        """
        Convert TwinState object to dictionary.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict):
        """
        Create TwinState object from dictionary.
        """
        return cls(**data)