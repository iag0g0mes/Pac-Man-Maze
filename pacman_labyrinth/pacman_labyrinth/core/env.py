from __future__ import annotations

from collections import deque
from pathlib import Path

from ..config import MazeConfig
from .actions import ACTION_TO_DELTA, MOVE_ACTION_TO_DIRECTION, Action, Direction
from .map_loader import load_maze
from .models import EXIT, UNKNOWN, WALL, MazeMap, Percept, Position, Transition, WorldState


class MazeEnv:
    """
        Grid maze where the agent reveals the map incrementally while moving.
    """

    def __init__(self, config: MazeConfig | None = None):
        self.config = config or MazeConfig()
        self.state: WorldState | None = None
        self._last_bump = False
        self._maze_map: MazeMap | None = None

    def reset(
        self,
        maze: MazeMap | None = None,
        map_path: str | Path | None = None,
    ) -> Percept:
        if maze is None:
            path = Path(map_path or self.config.map_path or "")
            if not path:
                raise ValueError("A maze map or map_path must be provided to MazeEnv.reset().")
            maze = load_maze(path)

        self._maze_map = maze
        known = [[UNKNOWN for _ in range(maze.cols)] for _ in range(maze.rows)]
        self.state = WorldState(
            true_grid=[row[:] for row in maze.grid],
            known_grid=known,
            pacman=maze.start,
            pacman_facing=Direction.RIGHT,
            start=maze.start,
            exit=maze.exit,
            map_name=maze.name,
        )
        self.state.visited.add(maze.start.as_tuple())
        self._last_bump = False
        self._reveal_around(self.state.pacman)
        return self.get_percept()

    @property
    def legal_actions(self) -> list[Action]:
        return list(Action)

    def in_bounds(self, pos: Position) -> bool:
        assert self.state is not None
        return 0 <= pos.row < self.state.rows and 0 <= pos.col < self.state.cols

    def is_wall(self, pos: Position) -> bool:
        assert self.state is not None
        return self.state.true_grid[pos.row][pos.col] == WALL

    def neighbors(self, pos: Position) -> list[Position]:
        out: list[Position] = []
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = Position(pos.row + dr, pos.col + dc)
            if self.in_bounds(nxt):
                out.append(nxt)
        return out

    def _reveal_cell(self, pos: Position) -> None:
        assert self.state is not None
        if not self.in_bounds(pos):
            return
        if pos == self.state.exit:
            self.state.known_grid[pos.row][pos.col] = EXIT
        else:
            self.state.known_grid[pos.row][pos.col] = self.state.true_grid[pos.row][pos.col]

    def _reveal_around(self, pos: Position) -> None:
        radius = max(1, self.config.reveal_radius)
        self._reveal_cell(pos)
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if abs(dr) + abs(dc) > radius:
                    continue
                nxt = Position(pos.row + dr, pos.col + dc)
                self._reveal_cell(nxt)

    def _direction_between(self, src: Position, dst: Position) -> Direction:
        dr = dst.row - src.row
        dc = dst.col - src.col
        if dr < 0:
            return Direction.UP
        if dr > 0:
            return Direction.DOWN
        if dc < 0:
            return Direction.LEFT
        return Direction.RIGHT

    def _visited_neighbors(self, pos: Position) -> list[Position]:
        assert self.state is not None
        out: list[Position] = []
        for nxt in self.neighbors(pos):
            if nxt.as_tuple() in self.state.visited and not self.is_wall(nxt):
                out.append(nxt)
        return out

    def shortest_visited_path(self, start: Position, goal: Position) -> list[Position]:
        if self.state is None:
            raise RuntimeError("Environment not reset.")
        if start == goal:
            return [start]

        queue: deque[Position] = deque([start])
        parents: dict[tuple[int, int], tuple[int, int] | None] = {start.as_tuple(): None}

        while queue:
            cur = queue.popleft()
            if cur == goal:
                break
            for nxt in self._visited_neighbors(cur):
                key = nxt.as_tuple()
                if key in parents:
                    continue
                parents[key] = cur.as_tuple()
                queue.append(nxt)

        goal_key = goal.as_tuple()
        if goal_key not in parents:
            return []

        path_rev: list[Position] = []
        cur_key: tuple[int, int] | None = goal_key
        while cur_key is not None:
            path_rev.append(Position(*cur_key))
            cur_key = parents[cur_key]
        path_rev.reverse()
        return path_rev

    def prepare_return_to_start(self) -> list[Position]:
        """Compute the shortest return path over visited cells and store highlights."""
        if self.state is None:
            raise RuntimeError("Environment not reset.")

        path = self.shortest_visited_path(self.state.pacman, self.state.start)
        path_cells = {pos.as_tuple() for pos in path}
        self.state.visited_shortest_path = path_cells
        self.state.visited_not_on_shortest_path = set(self.state.visited) - path_cells
        self.state.return_path = path[1:] if len(path) > 1 else []
        self.state.return_path_index = 0
        self.state.returning_home = bool(self.state.return_path)
        self.state.return_complete = not self.state.returning_home
        return path

    def advance_return_step(self) -> bool:
        if self.state is None:
            raise RuntimeError("Environment not reset.")
        if not self.state.returning_home:
            return False
        if self.state.return_path_index >= len(self.state.return_path):
            self.state.returning_home = False
            self.state.return_complete = True
            return False

        nxt = self.state.return_path[self.state.return_path_index]
        self.state.pacman_facing = self._direction_between(self.state.pacman, nxt)
        self.state.pacman = nxt
        self.state.return_path_index += 1
        if self.state.return_path_index >= len(self.state.return_path):
            self.state.returning_home = False
            self.state.return_complete = True
        return True

    def get_percept(self) -> Percept:
        if self.state is None:
            raise RuntimeError("Environment not reset.")
        exit_visible = self.state.known_grid[self.state.exit.row][self.state.exit.col] == EXIT
        return Percept(
            position=self.state.pacman,
            facing=self.state.pacman_facing,
            bump=self._last_bump,
            exit_visible=exit_visible,
            exit_position=self.state.exit if exit_visible else None,
            known_grid=tuple(tuple(row) for row in self.state.known_grid),
            visited=frozenset(self.state.visited),
            step_count=self.state.step_count,
            score=self.state.score,
            success=self.state.success,
            terminal=self.state.terminal,
        )

    def step(self, action: Action) -> Transition:
        if self.state is None:
            raise RuntimeError("Environment not reset.")
        if self.state.terminal:
            return Transition(
                percept=self.get_percept(),
                reward=0.0,
                done=True,
                info={"message": "Episode already finished."},
                action=action,
            )

        reward = 0.0
        self._last_bump = False
        self.state.step_count += 1

        if action in MOVE_ACTION_TO_DIRECTION:
            self.state.pacman_facing = MOVE_ACTION_TO_DIRECTION[action]
            dr, dc = ACTION_TO_DELTA[action]
            target = Position(self.state.pacman.row + dr, self.state.pacman.col + dc)
            reward += self.config.step_cost

            if not self.in_bounds(target):
                self._last_bump = True
                reward += self.config.bump_cost
            elif self.is_wall(target):
                self._last_bump = True
                self._reveal_cell(target)
                reward += self.config.bump_cost
            else:
                self.state.pacman = target
                self.state.visited.add(target.as_tuple())
                self._reveal_around(target)
                if target == self.state.exit:
                    self.state.terminal = True
                    self.state.success = True
                    reward += self.config.success_reward

        elif action == Action.WAIT:
            reward += self.config.wait_cost

        self.state.score += reward
        percept = self.get_percept()
        info = {
            "map_name": self.state.map_name,
            "known_count": percept.known_count,
            "success": self.state.success,
        }
        return Transition(
            percept=percept,
            reward=reward,
            done=self.state.terminal,
            info=info,
            action=action,
        )
