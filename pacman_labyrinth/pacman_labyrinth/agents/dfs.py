from __future__ import annotations

from dataclasses import dataclass

from .base import BaseAgent
from ..core.actions import Action
from ..core.models import EXIT, FREE, UNKNOWN, Percept, Position
from ..search.algorithms import SEARCH_REGISTRY, SearchResult
from ..search.problems import GridPlanningProblem


class DFSAgent(BaseAgent):
    def __init__(self):
        super().__init__(algorithm="dfs")


    def reset(self) -> None:
        return None

    def act(self, percept: Percept, legal_actions: list[Action]) -> Action:
        raise NotImplementedError
