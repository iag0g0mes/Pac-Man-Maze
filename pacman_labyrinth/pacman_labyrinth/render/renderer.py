from __future__ import annotations

import time

import pygame

from ..config import RenderConfig
from ..core.actions import Direction
from ..core.models import UNKNOWN, WALL, Percept, WorldState
from .assets import AssetManager
from .ui import Button, Dropdown, draw_text


class GameRenderer:
    def __init__(self, screen: pygame.Surface, assets: AssetManager, render_cfg: RenderConfig):
        self.screen = screen
        self.assets = assets
        self.render_cfg = render_cfg
        self.font_title = pygame.font.SysFont("arial", 22, bold=True)
        self.font_ui = pygame.font.SysFont("arial", 16)
        self.font_small = pygame.font.SysFont("arial", 13)
        self.show_full_world = False

    def hud_rect(self) -> pygame.Rect:
        width, height = self.screen.get_size()
        return pygame.Rect(
            width - self.render_cfg.hud_width,
            0,
            self.render_cfg.hud_width,
            height,
        )

    def board_rect(self) -> pygame.Rect:
        hud = self.hud_rect()
        _width, height = self.screen.get_size()
        board_left = self.render_cfg.board_margin
        board_top = self.render_cfg.board_margin
        board_width = max(10, hud.left - self.render_cfg.board_gap - board_left)
        board_height = max(10, height - 2 * self.render_cfg.board_margin)
        return pygame.Rect(board_left, board_top, board_width, board_height)

    def cell_rect(self, rows: int, cols: int, row: int, col: int) -> pygame.Rect:
        board = self.board_rect()
        cell_w = board.width / cols
        cell_h = board.height / rows
        x = int(board.x + col * cell_w)
        y = int(board.y + row * cell_h)
        w = int(round(board.x + (col + 1) * cell_w)) - x
        h = int(round(board.y + (row + 1) * cell_h)) - y
        return pygame.Rect(x, y, w, h)

    def _sprite_size(self, cell: pygame.Rect, fraction: float, minimum: int = 4) -> int:
        side = min(cell.width, cell.height)
        return max(minimum, int(side * fraction))

    def _current_pacman_frame(self, facing: Direction, cell: pygame.Rect, now: float) -> pygame.Surface:
        folder = {
            Direction.UP: "pacman-up",
            Direction.RIGHT: "pacman-right",
            Direction.DOWN: "pacman-down",
            Direction.LEFT: "pacman-left",
        }[facing]
        frame_idx = 1 + int(now * 8) % 3
        side = min(cell.width, cell.height)
        if side >= 40:
            scale = 0.74
        elif side >= 24:
            scale = 0.68
        elif side >= 16:
            scale = 0.60
        else:
            scale = 0.52
        size = self._sprite_size(cell, scale, minimum=6)
        return self.assets.load_surface(f"{folder}/{frame_idx}.png", size=(size, size), trim=True)

    def _draw_wall(self, cell: pygame.Rect) -> None:
        inset = max(1, min(4, min(cell.width, cell.height) // 3))
        wall = cell.inflate(-2 * inset, -2 * inset)
        pygame.draw.rect(
            self.screen,
            self.render_cfg.wall_color,
            wall,
            border_radius=max(3, min(cell.width, cell.height) // 6),
        )
        inner_margin = max(2, min(cell.width, cell.height) // 4)
        inner = wall.inflate(-2 * inner_margin, -2 * inner_margin)
        if inner.width > 2 and inner.height > 2:
            pygame.draw.rect(
                self.screen,
                self.render_cfg.wall_inner_color,
                inner,
                width=max(1, min(cell.width, cell.height) // 12),
                border_radius=max(2, min(inner.width, inner.height) // 6),
            )

    def _draw_free_cell(self, cell: pygame.Rect) -> None:
        inset = max(1, min(2, min(cell.width, cell.height) // 5))
        radius = max(2, min(8, min(cell.width, cell.height) // 3))
        pygame.draw.rect(self.screen, self.render_cfg.known_floor_color, cell.inflate(-2 * inset, -2 * inset), border_radius=radius)

    def _draw_hidden(self, cell: pygame.Rect) -> None:
        inset = max(1, min(2, min(cell.width, cell.height) // 5))
        radius = max(2, min(8, min(cell.width, cell.height) // 3))
        hidden = cell.inflate(-2 * inset, -2 * inset)
        pygame.draw.rect(self.screen, self.render_cfg.hidden_color, hidden, border_radius=radius)
        outline_margin = max(2, min(8, min(cell.width, cell.height) // 3))
        outline = hidden.inflate(-outline_margin, -outline_margin)
        if outline.width > 3 and outline.height > 3:
            pygame.draw.rect(self.screen, self.render_cfg.hidden_outline_color, outline, width=1, border_radius=max(2, radius - 1))

    def _draw_path_overlay(self, cell: pygame.Rect) -> None:
        inset = max(1, min(2, min(cell.width, cell.height) // 6))
        rect = cell.inflate(-2 * inset, -2 * inset)
        glow = pygame.Surface((max(2, rect.width), max(2, rect.height)), pygame.SRCALPHA)
        pygame.draw.rect(
            glow,
            self.render_cfg.shortest_path_glow_color,
            glow.get_rect(),
            border_radius=max(2, min(rect.width, rect.height) // 4),
        )
        self.screen.blit(glow, rect.topleft)
        border = max(1, min(cell.width, cell.height) // 7)
        pygame.draw.rect(
            self.screen,
            self.render_cfg.shortest_path_color,
            rect,
            width=border,
            border_radius=max(2, min(rect.width, rect.height) // 4),
        )

    def _draw_visited_overlay(self, cell: pygame.Rect) -> None:
        inset = max(1, min(4, min(cell.width, cell.height) // 4))
        rect = cell.inflate(-2 * inset, -2 * inset)
        glow = pygame.Surface((max(2, rect.width), max(2, rect.height)), pygame.SRCALPHA)
        pygame.draw.rect(
            glow,
            self.render_cfg.visited_off_path_glow_color,
            glow.get_rect(),
            border_radius=max(2, min(rect.width, rect.height) // 4),
        )
        self.screen.blit(glow, rect.topleft)
        dot_radius = max(2, min(rect.width, rect.height) // 5)
        pygame.draw.circle(self.screen, self.render_cfg.visited_off_path_color, rect.center, dot_radius)

    def _draw_exit(self, cell: pygame.Rect) -> None:
        size = self._sprite_size(cell, 0.56, minimum=6)
        surf = self.assets.load_surface("other/strawberry.png", size=(size, size), trim=True)
        rect = surf.get_rect(center=cell.center)
        glow_pad = max(6, size // 3)
        glow = pygame.Surface((rect.width + glow_pad, rect.height + glow_pad), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 110, 120, 85), glow.get_rect().center, max(4, glow.get_width() // 3))
        self.screen.blit(glow, glow.get_rect(center=rect.center))
        self.screen.blit(surf, rect)

    def _draw_dot(self, cell: pygame.Rect) -> None:
        size = self._sprite_size(cell, 0.14, minimum=3)
        surf = self.assets.load_surface("other/dot.png", size=(size, size), trim=True)
        rect = surf.get_rect(center=cell.center)
        self.screen.blit(surf, rect)

    def _draw_start(self, cell: pygame.Rect) -> None:
        size = self._sprite_size(cell, 0.46, minimum=6)
        surf = self.assets.load_surface("ghosts/blue_ghost.png", size=(size, size), trim=True)
        rect = surf.get_rect(center=(cell.centerx, cell.centery + max(1, cell.height // 12)))
        self.screen.blit(surf, rect)

    def _draw_board(self, state: WorldState, percept: Percept) -> None:
        board = self.board_rect()
        pygame.draw.rect(self.screen, self.render_cfg.board_bg_color, board, border_radius=18)
        pygame.draw.rect(self.screen, self.render_cfg.grid_line_color, board, width=2, border_radius=18)

        visible_grid = state.true_grid if self.show_full_world else percept.known_grid
        rows, cols = state.rows, state.cols
        cell_radius = max(1, min(6, int(min(board.width / cols, board.height / rows) // 3)))
        current_pos = state.pacman.as_tuple()
        for r in range(rows):
            for c in range(cols):
                cell = self.cell_rect(rows, cols, r, c)
                cell_value = visible_grid[r][c]
                pos = (r, c)
                if not self.show_full_world and cell_value == UNKNOWN:
                    self._draw_hidden(cell)
                elif cell_value == WALL:
                    self._draw_wall(cell)
                else:
                    self._draw_free_cell(cell)
                    if pos in state.visited_not_on_shortest_path and pos != current_pos:
                        self._draw_visited_overlay(cell)
                    elif pos in state.visited and pos not in state.visited_shortest_path and pos != current_pos and pos != state.exit.as_tuple():
                        self._draw_dot(cell)
                    if pos in state.visited_shortest_path:
                        self._draw_path_overlay(cell)
                    if state.start.as_tuple() == pos and pos != current_pos:
                        self._draw_start(cell)
                    exit_known_or_reveal = self.show_full_world or percept.exit_visible
                    if exit_known_or_reveal and state.exit.as_tuple() == pos:
                        self._draw_exit(cell)
                pygame.draw.rect(self.screen, self.render_cfg.grid_line_color, cell, width=1, border_radius=cell_radius)

        now = time.time()
        pacman_cell = self.cell_rect(rows, cols, state.pacman.row, state.pacman.col)
        pacman = self._current_pacman_frame(state.pacman_facing, pacman_cell, now)
        pacman_rect = pacman.get_rect(center=pacman_cell.center)
        self.screen.blit(pacman, pacman_rect)

    def _draw_hud(self, state: WorldState, percept: Percept, agent_name: str, agent_debug: dict[str, object] | None = None) -> None:
        panel = self.hud_rect()
        overlay = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        overlay.fill((8, 12, 30, 160))
        self.screen.blit(overlay, panel.topleft)
        pygame.draw.line(self.screen, (255, 255, 255), (panel.left, 0), (panel.left, panel.bottom), 2)

        x = panel.x + 10
        y = 12
        draw_text(self.screen, self.font_title, "Info", self.render_cfg.accent_color, x, y)
        y += 32
        summary_lines = [
            f"Map: {state.map_name}",
            f"Agent: {agent_name}",
            f"Size: {state.rows}x{state.cols}",
            f"Steps: {state.step_count}",
            f"Score: {state.score:.1f}",
            f"Known: {percept.known_count}",
            f"Exit: {'visible' if percept.exit_visible else 'hidden'}",
        ]
        if state.visited_shortest_path:
            summary_lines.append(f"Best return: {max(0, len(state.visited_shortest_path) - 1)}")
        for text in summary_lines:
            draw_text(self.screen, self.font_ui, text, self.render_cfg.text_color, x, y)
            y += 21

        y += 8
        draw_text(self.screen, self.font_title, "Keys", self.render_cfg.accent_color, x, y)
        y += 28
        controls = [
            "Move: WASD / arrows",
            "Wait: space",
            "Restart: R",
            "Show full: TAB",
            "Menu: ESC",
        ]
        for text in controls:
            draw_text(self.screen, self.font_small, text, self.render_cfg.text_color, x, y)
            y += 18

        if agent_debug:
            y += 10
            draw_text(self.screen, self.font_title, "Search", self.render_cfg.accent_color, x, y)
            y += 28
            target = agent_debug.get("target", "-")
            debug_lines = [
                f"Algo: {agent_debug.get('algorithm', '-')}",
                f"Target: {target}",
                f"Frontiers: {agent_debug.get('frontier_count', 0)}",
                f"Expanded: {agent_debug.get('expanded', 0)}",
                f"Plan: {agent_debug.get('plan_length', 0)}",
                f"Path found: {'yes' if agent_debug.get('found', False) else 'no'}",
            ]
            for text in debug_lines:
                draw_text(self.screen, self.font_small, text, self.render_cfg.text_color, x, y)
                y += 18

        if state.terminal:
            y = panel.bottom - 94
            if state.returning_home:
                msg = "Returning"
                color = self.render_cfg.accent_color
                subtitle = "Shortest path over visited cells"
            elif state.return_complete and state.success:
                msg = "Returned"
                color = self.render_cfg.success_color
                subtitle = "Gold = best return | Blue = other visited"
            else:
                msg = "Exit reached" if state.success else "Stopped"
                color = self.render_cfg.success_color if state.success else self.render_cfg.warning_color
                subtitle = "R: restart | ESC: menu"
            draw_text(self.screen, self.font_title, msg, color, x, y)
            y += 24
            draw_text(self.screen, self.font_small, subtitle, self.render_cfg.text_color, x, y)
            if state.return_complete and state.success:
                y += 18
                draw_text(self.screen, self.font_small, "R: restart | ESC: menu", self.render_cfg.text_color, x, y)

    def render(self, state: WorldState, percept: Percept, agent_name: str, agent_debug: dict[str, object] | None = None) -> None:
        self.screen.fill(self.render_cfg.background_color)
        self._draw_board(state, percept)
        self._draw_hud(state, percept, agent_name, agent_debug)


class MenuRenderer:
    def __init__(self, screen: pygame.Surface, assets: AssetManager, render_cfg: RenderConfig):
        self.screen = screen
        self.assets = assets
        self.render_cfg = render_cfg
        self.font_ui = pygame.font.SysFont("arial", 26)
        self.font_small = pygame.font.SysFont("arial", 18)

    def draw(
        self,
        map_name: str,
        hovered: str | None,
        buttons: dict[str, Button],
        algorithm_dropdown: Dropdown,
        hovered_dropdown_header: bool,
        hovered_dropdown_option: int | None,
    ) -> None:
        width, height = self.screen.get_size()
        background = self.assets.load_surface("other/home_background.png", size=(width, height), trim=False)
        self.screen.blit(background, (0, 0))

        dimmer = pygame.Surface((width, height), pygame.SRCALPHA)
        dimmer.fill((5, 8, 22, 0))
        self.screen.blit(dimmer, (0, 0))

        panel = pygame.Rect(width // 2 - 300, 320, 600, 450)
        overlay = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        overlay.fill((8, 12, 30, 138))
        self.screen.blit(overlay, panel.topleft)
        pygame.draw.rect(self.screen, (255, 255, 255), panel, width=2, border_radius=20)

        label = map_name.replace("maze_", "").replace("x", " x ")
        draw_text(
            self.screen,
            self.font_ui,
            f"Selected map: {label}",
            self.render_cfg.text_color,
            panel.centerx,
            panel.y + 35,
            center=True,
        )

        for name, button in buttons.items():
            button.draw(self.screen, self.font_ui, hovered == name)
        algorithm_dropdown.draw(self.screen, self.font_ui, hovered_dropdown_header, hovered_dropdown_option)
