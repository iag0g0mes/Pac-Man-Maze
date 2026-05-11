from __future__ import annotations

from pathlib import Path
import time
from typing import Callable

import pygame

from .agents.manual import key_to_action
from .agents.random_agent import RandomAgent
from .agents.a_star import AStarAgent 
from .agents.bfs import BFSAgent
from .agents.dfs import  DFSAgent
from .agents.greedy import GreedyBestFirstAgent
from .agents.ucs import UCSAgent
from .config import MazeConfig, RenderConfig
from .core.env import MazeEnv
from .core.map_loader import list_map_files
from .render.assets import AssetManager
from .render.renderer import GameRenderer, MenuRenderer
from .render.ui import Button, Dropdown


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = Path(__file__).resolve().parent / "assets"
MAPS_DIR = PROJECT_ROOT / "maps"


ALGORITHM_OPTIONS: list[tuple[str, Callable[[], object]]] = [
    ("BFS", BFSAgent),
    ("DFS", BFSAgent),
    ("UCS", BFSAgent),
    ("Greedy", GreedyBestFirstAgent),
    ("A*", AStarAgent),
    ("Random", lambda: RandomAgent()),
]


def _make_buttons(width: int, height: int) -> dict[str, Button]:
    center_x = width // 2
    top = 400
    button_w = 360
    button_h = 50
    left = center_x - button_w // 2
    return {
        "next_map": Button(pygame.Rect(left, top-5, button_w, button_h), "Next map >", (52, 74, 116), (74, 96, 144)),
        "run_selected": Button(pygame.Rect(left, top + 154, button_w, button_h), "Run selected", (84, 74, 126), (104, 92, 158)),
        "manual": Button(pygame.Rect(left, top + 222, button_w, button_h), "Manual", (45, 120, 80), (58, 150, 100)),
        "quit": Button(pygame.Rect(left, top + 290, button_w, button_h), "Quit", (150, 70, 70), (180, 88, 88)),
    }


def _make_algorithm_dropdown(width: int, height: int) -> Dropdown:
    center_x = width // 2
    top = 486
    button_w = 360
    button_h = 50
    left = center_x - button_w // 2
    return Dropdown(
        rect=pygame.Rect(left, top, button_w, button_h),
        options=[name for name, _factory in ALGORITHM_OPTIONS],
        selected_index=0,
    )


def run_app() -> None:
    pygame.init()
    pygame.display.set_caption("Pac-Man Labyrinth")
    render_cfg = RenderConfig()
    screen = pygame.display.set_mode((render_cfg.window_width, render_cfg.window_height))
    clock = pygame.time.Clock()

    map_files = list_map_files(MAPS_DIR)
    if not map_files:
        raise RuntimeError(f"No maze files found in {MAPS_DIR}")

    assets = AssetManager(ASSET_DIR)
    menu_renderer = MenuRenderer(screen, assets, render_cfg)
    game_renderer = GameRenderer(screen, assets, render_cfg)
    buttons = _make_buttons(*screen.get_size())
    algorithm_dropdown = _make_algorithm_dropdown(*screen.get_size())

    mode = "menu"
    hovered: str | None = None
    hovered_dropdown_header = False
    hovered_dropdown_option: int | None = None
    selected_map_idx = 0

    env: MazeEnv | None = None
    percept = None
    agent = None
    agent_name = "Manual"
    last_agent_step = 0.0
    agent_step_period = 0.17
    last_return_step = 0.0
    return_step_period = 0.11

    def make_selected_agent():
        name, factory = ALGORITHM_OPTIONS[algorithm_dropdown.selected_index]
        if name == "Random":
            return RandomAgent(seed=selected_map_idx), name
        return factory(), name

    def maybe_start_return_animation() -> None:
        nonlocal env
        if env is None or env.state is None:
            return
        if env.state.success and not env.state.returning_home and not env.state.return_complete:
            env.prepare_return_to_start()

    def start_game(selected_agent=None, selected_name: str = "Manual") -> None:
        nonlocal env, percept, agent, agent_name, mode, last_agent_step, last_return_step
        cfg = MazeConfig(map_path=map_files[selected_map_idx])
        env = MazeEnv(cfg)
        percept = env.reset()
        agent = selected_agent
        if agent is not None:
            agent.reset()
        agent_name = selected_name
        game_renderer.show_full_world = False
        mode = "game"
        last_agent_step = 0.0
        last_return_step = 0.0
        algorithm_dropdown.close()

    running = True
    while running:
        now = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif mode == "menu":
                if event.type == pygame.MOUSEMOTION:
                    hovered = None
                    hovered_dropdown_header = algorithm_dropdown.contains_header(event.pos)
                    hovered_dropdown_option = algorithm_dropdown.hovered_option_index(event.pos)
                    for name, button in buttons.items():
                        if button.contains(event.pos):
                            hovered = name
                            break
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    option_idx = algorithm_dropdown.hovered_option_index(event.pos)
                    if option_idx is not None:
                        algorithm_dropdown.selected_index = option_idx
                        algorithm_dropdown.close()
                    elif algorithm_dropdown.contains_header(event.pos):
                        algorithm_dropdown.toggle()
                    elif buttons["next_map"].contains(event.pos):
                        selected_map_idx = (selected_map_idx + 1) % len(map_files)
                        algorithm_dropdown.close()
                    elif buttons["run_selected"].contains(event.pos):
                        selected_agent, selected_name = make_selected_agent()
                        start_game(selected_agent, selected_name)
                    elif buttons["manual"].contains(event.pos):
                        start_game(None, "Manual")
                    elif buttons["quit"].contains(event.pos):
                        running = False
                    else:
                        algorithm_dropdown.close()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_RIGHT, pygame.K_SPACE):
                        selected_map_idx = (selected_map_idx + 1) % len(map_files)
                        algorithm_dropdown.close()
                    elif event.key == pygame.K_RETURN:
                        selected_agent, selected_name = make_selected_agent()
                        start_game(selected_agent, selected_name)

            elif mode == "game":
                assert env is not None and env.state is not None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        mode = "menu"
                    elif event.key == pygame.K_TAB:
                        game_renderer.show_full_world = not game_renderer.show_full_world
                    elif event.key == pygame.K_r:
                        percept = env.reset()
                        if agent is not None:
                            agent.reset()
                    elif agent is None and not env.state.terminal:
                        action = key_to_action(event.key)
                        if action is not None:
                            transition = env.step(action)
                            percept = transition.percept
                            if transition.done:
                                maybe_start_return_animation()
                                last_return_step = now

        if mode == "menu":
            menu_renderer.draw(
                map_files[selected_map_idx].stem,
                hovered,
                buttons,
                algorithm_dropdown,
                hovered_dropdown_header,
                hovered_dropdown_option,
            )

        elif mode == "game":
            assert env is not None and env.state is not None and percept is not None
            if env.state.returning_home and now - last_return_step >= return_step_period:
                env.advance_return_step()
                percept = env.get_percept()
                last_return_step = now
            elif agent is not None and not env.state.terminal and now - last_agent_step >= agent_step_period:
                action = agent.act(percept, env.legal_actions)
                if action not in env.legal_actions:
                    action = env.legal_actions[-1]
                transition = env.step(action)
                percept = transition.percept
                if transition.done:
                    maybe_start_return_animation()
                    last_return_step = now
                last_agent_step = now

            debug_info = None
            if agent is not None and hasattr(agent, "last_debug"):
                from dataclasses import asdict
                debug_info = asdict(agent.last_debug)
            game_renderer.render(env.state, percept, agent_name, debug_info)

        pygame.display.flip()
        clock.tick(render_cfg.fps)

    pygame.quit()
