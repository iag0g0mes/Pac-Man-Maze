from __future__ import annotations

import random

from .base import BaseAgent
from ..core.actions import Action
from ..core.models import Percept


class RandomAgent(BaseAgent):
    name = "Random"

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def act(self, percept: Percept, legal_actions: list[Action]) -> Action:
        choices = [a for a in legal_actions if a != Action.WAIT]
        return self.rng.choice(choices or legal_actions)
