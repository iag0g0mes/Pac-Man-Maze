from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .actions import Action, Direction

UNKNOWN = -1
FREE = 0
WALL = 1
EXIT = 2


@dataclass(frozen=True, slots=True)
class Position:
    """2D grid position."""

    row: int
    col: int

    def as_tuple(self) -> tuple[int, int]:
        return (self.row, self.col)


@dataclass(slots=True)
class MazeMap:
    """Loaded map definition."""

    grid: list[list[int]]
    start: Position
    exit: Position
    name: str = "maze"

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    @property
    def shape(self) -> tuple[int, int]:
        return (self.rows, self.cols)


@dataclass(slots=True)
class Percept:
    position: Position
    facing: Direction
    bump: bool
    exit_visible: bool
    exit_position: Position | None
    known_grid: tuple[tuple[int, ...], ...]
    visited: frozenset[tuple[int, int]]
    step_count: int
    score: float
    success: bool
    terminal: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "position": self.position.as_tuple(),
            "facing": self.facing.name,
            "bump": self.bump,
            "exit_visible": self.exit_visible,
            "exit_position": None if self.exit_position is None else self.exit_position.as_tuple(),
            "visited": sorted(self.visited),
            "step_count": self.step_count,
            "score": self.score,
            "success": self.success,
            "terminal": self.terminal,
        }

    @property
    def known_count(self) -> int:
        return sum(cell != UNKNOWN for row in self.known_grid for cell in row)


@dataclass(slots=True)
class WorldState:
    true_grid: list[list[int]]
    known_grid: list[list[int]]
    pacman: Position
    pacman_facing: Direction
    start: Position
    exit: Position
    map_name: str
    visited: set[tuple[int, int]] = field(default_factory=set)
    terminal: bool = False
    success: bool = False
    step_count: int = 0
    score: float = 0.0
    visited_shortest_path: set[tuple[int, int]] = field(default_factory=set)
    visited_not_on_shortest_path: set[tuple[int, int]] = field(default_factory=set)
    return_path: list[Position] = field(default_factory=list)
    return_path_index: int = 0
    returning_home: bool = False
    return_complete: bool = False

    @property
    def rows(self) -> int:
        return len(self.true_grid)

    @property
    def cols(self) -> int:
        return len(self.true_grid[0]) if self.true_grid else 0


@dataclass(slots=True)
class Transition:
    percept: Percept
    reward: float
    done: bool
    info: dict[str, Any]
    action: Action
