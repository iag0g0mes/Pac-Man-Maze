from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pacman_labyrinth.agents.random_agent import RandomAgent
from pacman_labyrinth.agents.a_star import AStarAgent 
from pacman_labyrinth.agents.bfs import BFSAgent
from pacman_labyrinth.agents.dfs import  DFSAgent
from pacman_labyrinth.agents.greedy import GreedyBestFirstAgent
from pacman_labyrinth.agents.ucs import UCSAgent
from pacman_labyrinth.config import MazeConfig
from pacman_labyrinth.core.env import MazeEnv


AGENTS = {
    "bfs": BFSAgent,
    "dfs": BFSAgent,
    "ucs": BFSAgent,
    "greedy": GreedyBestFirstAgent,
    "astar": AStarAgent,
    "random": RandomAgent,
}

def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a labyrinth agent without the GUI.")
    parser.add_argument("--map", required=True, help="Path to a maze .txt file.")
    parser.add_argument("--agent", default="astar", choices=sorted(AGENTS), help="Agent to run.")
    parser.add_argument("--max-steps", type=int, default=3000, help="Episode step limit.")
    return parser


def main() -> None:
    args = build_argparser().parse_args()
    env = MazeEnv(MazeConfig(map_path=Path(args.map)))
    percept = env.reset()
    agent = AGENTS[args.agent]()
    agent.reset()

    done = False
    steps = 0
    total_reward = 0.0
    while not done and steps < args.max_steps:
        action = agent.act(percept, env.legal_actions)
        transition = env.step(action)
        percept = transition.percept
        total_reward += transition.reward
        done = transition.done
        steps += 1

    print(f"map={env.state.map_name}")
    print(f"agent={args.agent}")
    print(f"steps={steps}")
    print(f"score={env.state.score:.2f}")
    print(f"reward_sum={total_reward:.2f}")
    print(f"success={env.state.success}")
    if hasattr(agent, "last_debug"):
        print(f"search_debug={asdict(agent.last_debug)}")


if __name__ == "__main__":
    main()
