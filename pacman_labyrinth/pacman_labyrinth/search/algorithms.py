from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import heapq
import itertools

from .problems import GridPlanningProblem
from ..core.actions import Action
from ..core.models import Position


@dataclass(slots=True)
class SearchResult:
    actions: list[Action]
    path: list[Position]
    cost: float
    expanded: int
    found: bool


def _reconstruct(
    parents: dict[tuple[int, int], tuple[tuple[int, int] | None, Action | None]],
    goal: Position,
) -> tuple[list[Action], list[Position]]:
    actions: list[Action] = []
    path: list[Position] = [goal]
    cur = goal.as_tuple()
    while True:
        parent, action = parents[cur]
        if parent is None:
            break
        assert action is not None
        actions.append(action)
        path.append(Position(*parent))
        cur = parent
    actions.reverse()
    path.reverse()
    return actions, path


def dijkstra_search(problem: GridPlanningProblem) -> SearchResult:
    counter = itertools.count()
    start = problem.start.as_tuple()
    heap: list[tuple[float, int, Position]] = [(0.0, next(counter), problem.start)]
    parents = {start: (None, None)}
    dist = {start: 0.0}
    expanded = 0

    while heap:
        cost, _, cur = heapq.heappop(heap)
        cur_key = cur.as_tuple()
        if cost > dist[cur_key]:
            continue
        expanded += 1
        if problem.is_goal(cur):
            actions, path = _reconstruct(parents, cur)
            return SearchResult(actions, path, cost, expanded, True)
        for action, nxt, step_cost in problem.successors(cur):
            nxt_key = nxt.as_tuple()
            new_cost = cost + step_cost
            if new_cost < dist.get(nxt_key, float("inf")):
                dist[nxt_key] = new_cost
                parents[nxt_key] = (cur_key, action)
                heapq.heappush(heap, (new_cost, next(counter), nxt))
    return SearchResult([], [problem.start], float("inf"), expanded, False)



SEARCH_REGISTRY = {
    "dijkstra": dijkstra_search,
}
