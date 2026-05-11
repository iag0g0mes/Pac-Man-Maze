from __future__ import annotations

from abc import ABC, abstractmethod

from ..core.actions import Action
from ..core.models import Percept


class BaseAgent(ABC):

    name: str = "BaseAgent"

    def __init__(self, algorithm):
        name = algorithm

    def reset(self) -> None:
        return None

    @abstractmethod
    def act(self, percept: Percept, legal_actions: list[Action]) -> Action:
        raise NotImplementedError
