from __future__ import annotations

from enum import Enum, auto


class Direction(Enum):
    UP = auto()
    RIGHT = auto()
    DOWN = auto()
    LEFT = auto()


class Action(Enum):
    MOVE_UP = auto()
    MOVE_RIGHT = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    WAIT = auto()


MOVE_ACTION_TO_DIRECTION = {
    Action.MOVE_UP: Direction.UP,
    Action.MOVE_RIGHT: Direction.RIGHT,
    Action.MOVE_DOWN: Direction.DOWN,
    Action.MOVE_LEFT: Direction.LEFT,
}

ACTION_TO_DELTA = {
    Action.MOVE_UP: (-1, 0),
    Action.MOVE_RIGHT: (0, 1),
    Action.MOVE_DOWN: (1, 0),
    Action.MOVE_LEFT: (0, -1),
}
