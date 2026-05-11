from __future__ import annotations

from collections import deque
from pathlib import Path
import re

from .models import EXIT, FREE, WALL, MazeMap, Position

_TOKEN_TO_CELL = {
    "0": FREE,
    "1": WALL,
    "S": FREE,
    "E": EXIT,
    "2": EXIT,
}


def _tokenize_line(line: str) -> list[str]:
    cleaned = line.strip()
    if not cleaned or cleaned.startswith("#"):
        return []
    if " " in cleaned or "," in cleaned:
        cleaned = cleaned.replace(",", " ")
        return [tok for tok in cleaned.split() if tok]
    return list(cleaned)


def _parse_metadata_line(line: str) -> tuple[Position | None, Position | None] | None:
    cleaned = line.strip()
    if not cleaned:
        return None
    upper = cleaned.upper()
    if not any(keyword in upper for keyword in ("START", "EXIT", "GOAL")):
        return None
    numbers = [int(x) for x in re.findall(r"-?\d+", cleaned)]
    if len(numbers) < 4:
        raise ValueError(
            "Metadata line must provide four integers: START row col EXIT row col."
        )
    start = Position(numbers[0], numbers[1])
    exit_pos = Position(numbers[2], numbers[3])
    return start, exit_pos


def _pick_default_start(grid: list[list[int]]) -> Position:
    rows, cols = len(grid), len(grid[0])
    for r in range(rows - 1, -1, -1):
        for c in range(cols):
            if grid[r][c] != WALL:
                return Position(r, c)
    raise ValueError("Maze has no free cell for start.")


def _pick_default_exit(grid: list[list[int]], start: Position) -> Position:
    rows, cols = len(grid), len(grid[0])
    for r in range(rows):
        for c in range(cols - 1, -1, -1):
            if grid[r][c] != WALL and (r, c) != start.as_tuple():
                return Position(r, c)
    raise ValueError("Maze has no free cell for exit.")


def _neighbors(grid: list[list[int]], pos: Position) -> list[Position]:
    rows, cols = len(grid), len(grid[0])
    out: list[Position] = []
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        rr, cc = pos.row + dr, pos.col + dc
        if 0 <= rr < rows and 0 <= cc < cols and grid[rr][cc] != WALL:
            out.append(Position(rr, cc))
    return out


def _has_path(grid: list[list[int]], start: Position, goal: Position) -> bool:
    queue: deque[Position] = deque([start])
    seen = {start.as_tuple()}
    while queue:
        cur = queue.popleft()
        if cur == goal:
            return True
        for nxt in _neighbors(grid, cur):
            key = nxt.as_tuple()
            if key in seen:
                continue
            seen.add(key)
            queue.append(nxt)
    return False


def load_maze(path: str | Path) -> MazeMap:
    """Load a maze from a text file.

    Supported formats:
    - A grid of 0/1 cells, optionally using S and E inside the grid.
    - A first metadata row such as: ``START 8 1 EXIT 1 8`` followed by the 0/1 grid.

    Semantics:
    - 0: free cell
    - 1: wall
    - S: optional start cell inside the grid
    - E or 2: optional exit cell inside the grid
    """

    path = Path(path)
    rows: list[list[int]] = []
    start: Position | None = None
    exit_pos: Position | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        metadata = _parse_metadata_line(raw_line)
        if metadata is not None:
            start, exit_pos = metadata
            continue

        tokens = _tokenize_line(raw_line)
        if not tokens:
            continue
        parsed_row: list[int] = []
        for c, token in enumerate(tokens):
            if token not in _TOKEN_TO_CELL:
                raise ValueError(f"Unsupported token {token!r} in {path}.")
            cell = _TOKEN_TO_CELL[token]
            if token == "S":
                start = Position(len(rows), c)
                cell = FREE
            elif token in {"E", "2"}:
                exit_pos = Position(len(rows), c)
                cell = FREE
            parsed_row.append(cell)
        rows.append(parsed_row)

    if not rows:
        raise ValueError(f"Maze file {path} is empty.")

    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError(f"Maze file {path} has inconsistent row sizes.")

    if start is None:
        start = _pick_default_start(rows)
    if exit_pos is None:
        exit_pos = _pick_default_exit(rows, start)

    if not (0 <= start.row < len(rows) and 0 <= start.col < width):
        raise ValueError("Start metadata is outside the maze bounds.")
    if not (0 <= exit_pos.row < len(rows) and 0 <= exit_pos.col < width):
        raise ValueError("Exit metadata is outside the maze bounds.")
    if rows[start.row][start.col] == WALL:
        raise ValueError("Start position is inside a wall.")
    if rows[exit_pos.row][exit_pos.col] == WALL:
        raise ValueError("Exit position is inside a wall.")
    if not _has_path(rows, start, exit_pos):
        raise ValueError(f"Maze {path.name} has no path from start to exit.")

    return MazeMap(grid=rows, start=start, exit=exit_pos, name=path.stem)


def list_map_files(directory: str | Path) -> list[Path]:
    directory = Path(directory)
    return sorted([p for p in directory.glob("*.txt") if p.is_file()])
