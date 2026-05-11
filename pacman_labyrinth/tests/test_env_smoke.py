from pathlib import Path

from pacman_labyrinth.config import MazeConfig
from pacman_labyrinth.core.actions import Action
from pacman_labyrinth.core.env import MazeEnv
from pacman_labyrinth.core.map_loader import load_maze
from pacman_labyrinth.search.algorithms import dijkstra_search
from pacman_labyrinth.search.problems import GridPlanningProblem


def test_partial_observation_at_reset():
    env = MazeEnv(MazeConfig(map_path=Path("maps/maze_10x10.txt")))
    percept = env.reset()
    total_cells = len(percept.known_grid) * len(percept.known_grid[0])
    assert 0 < percept.known_count < total_cells


def test_reaching_exit_with_metadata_coordinates(tmp_path):
    maze_path = tmp_path / "tiny.txt"
    maze_path.write_text(
        "START 2 1 EXIT 1 2\n"
        "1111\n"
        "1001\n"
        "1001\n"
        "1111\n",
        encoding="utf-8",
    )
    env = MazeEnv(MazeConfig(map_path=maze_path))
    env.reset()
    env.step(Action.MOVE_UP)
    transition = env.step(Action.MOVE_RIGHT)
    assert transition.done is True
    assert transition.percept.success is True


def test_dijkstra_search_on_known_grid():
    maze = load_maze(Path("maps/maze_20x20.txt"))
    known_grid = tuple(tuple(row) for row in maze.grid)
    problem = GridPlanningProblem(known_grid, maze.start, maze.exit)
    dijkstra = dijkstra_search(problem)
    assert dijkstra.found
