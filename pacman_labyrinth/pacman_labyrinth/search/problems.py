from __future__ import annotations

from dataclasses import dataclass

from ..core.actions import ACTION_TO_DELTA, Action
from ..core.models import EXIT, FREE, UNKNOWN, Position


@dataclass(slots=True)
class GridPlanningProblem:
    """Shortest-path problem on the currently known grid."""

    grid: tuple[tuple[int, ...], ...]
    start: Position
    goal: Position
    allow_unknown: bool = False

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols

    def traversable(self, pos: Position) -> bool:
        cell = self.grid[pos.row][pos.col]
        if cell in (FREE, EXIT):
            return True
        return self.allow_unknown and cell == UNKNOWN

    def is_goal(self, pos: Position) -> bool:
        return pos == self.goal

    def heuristic(self, pos: Position) -> int:
        return abs(pos.row - self.goal.row) + abs(pos.col - self.goal.col)

    def successors(self, pos: Position) -> list[tuple[Action, Position, float]]:
        out: list[tuple[Action, Position, float]] = []
        for action, (dr, dc) in ACTION_TO_DELTA.items():
            nxt = Position(pos.row + dr, pos.col + dc)
            if self.in_bounds(nxt) and self.traversable(nxt):
                out.append((action, nxt, 1.0))
        return out
