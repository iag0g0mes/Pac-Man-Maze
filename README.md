# Pac-Man Labyrinth in Python/Pygame

Didactic project derived from the modular **Mario Wumpus** structure, but reformulated as a **partially observable labyrinth** in a Pac-Man style. The main educational goal is to let students implement and compare search algorithms such as **BFS, Dijkstra, Greedy Best-First, and A\***.

The project remains modular:

1. **environment engine** (`pacman_labyrinth.core`)
2. **pluggable agents** (`pacman_labyrinth.agents`)
3. **search algorithms** (`pacman_labyrinth.search`)
4. **rendering/UI** (`pacman_labyrinth.render`)

## Educational formulation

- The maze is loaded from a text file with mostly `0` and `1` values.
- `0` means a free cell.
- `1` means a wall.
- The **first row can optionally define the start and exit coordinates**.

Supported map formats:

```text
START 8 1 EXIT 1 8
1111111111
1000000001
1011111101
1000000101
1110110101
1000100101
1011100101
1010000001
1001111101
1111111111
```

Coordinates are zero-based. `S` and `E` inside the grid are also supported.

## Important dynamic

The episode starts with the map **hidden**. The agent only knows what has been discovered so far. As Pac-Man moves, the environment reveals nearby cells. Students can therefore study both:

1. **exploration / frontier selection**
2. **path planning on the discovered subgraph**

The provided reference search agents use repeated replanning:
- if the exit is visible, plan to the exit;
- otherwise, plan to a frontier cell.

## Requirements

- Python 3.10+
- `pygame`
- `Pillow`

Installation:

```bash
pip install -r requirements.txt
```

## How to run

### Pygame application

```bash
python main.py
```

### Headless run for a chosen agent and map

```bash
python scripts/run_agent.py --map maps/maze_30x30.txt --agent astar --max-steps 3000
```

Supported agents:
- `astar`
- `bfs`
- `dijkstra`
- `greedy`
- `random`

## Controls

### Menu
- Mouse: click buttons
- `RIGHT` or `SPACE`: switch to the next map
- `ESC`: quit

### Game
- `WASD` or arrow keys: move Pac-Man
- `SPACE`: wait
- `TAB`: reveal/hide the full map
- `R`: restart current map
- `ESC`: return to menu

## Project structure

```text
pacman_labyrinth_project/
├── main.py
├── README.md
├── requirements.txt
├── maps/
│   ├── maze_10x10.txt
│   ├── maze_20x20.txt
│   ├── maze_30x30.txt
│   ├── maze_40x40.txt
│   ├── maze_50x50.txt
│   ├── maze_60x60.txt
│   └── maze_70x70.txt
├── scripts/
│   ├── play_manual.py
│   ├── run_agent.py
│   └── generate_benchmark_maps.py
└── pacman_labyrinth/
    ├── __init__.py
    ├── app.py
    ├── config.py
    ├── core/
    ├── agents/
    ├── search/
    ├── render/
    └── assets/
```

## Environment API

```python
from pacman_labyrinth.config import MazeConfig
from pacman_labyrinth.core.env import MazeEnv

env = MazeEnv(MazeConfig(map_path="maps/maze_20x20.txt"))
percept = env.reset()
```

## Search API

```python
from pacman_labyrinth.search.problems import GridPlanningProblem
from pacman_labyrinth.search.algorithms import astar_search

problem = GridPlanningProblem(
    grid=percept.known_grid,
    start=percept.position,
    goal=some_goal,
)
result = astar_search(problem)
```

## Suggested assignments

1. Implement Uniform-Cost Search and compare it against A*.
2. Replace Manhattan distance by an inadmissible heuristic and analyze the effect.
3. Implement a frontier strategy that prefers cells with more hidden neighbors.
4. Compare shortest path length vs explored area.
5. Move the start/goal positions by editing the metadata row of each map.

## Tests

```bash
pytest -q
```
