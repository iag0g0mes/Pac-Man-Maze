from __future__ import annotations

import pygame

from ..core.actions import Action


KEY_TO_ACTION = {
    pygame.K_w: Action.MOVE_UP,
    pygame.K_UP: Action.MOVE_UP,
    pygame.K_d: Action.MOVE_RIGHT,
    pygame.K_RIGHT: Action.MOVE_RIGHT,
    pygame.K_s: Action.MOVE_DOWN,
    pygame.K_DOWN: Action.MOVE_DOWN,
    pygame.K_a: Action.MOVE_LEFT,
    pygame.K_LEFT: Action.MOVE_LEFT,
    pygame.K_SPACE: Action.WAIT,
}


def key_to_action(key: int) -> Action | None:
    return KEY_TO_ACTION.get(key)
