"""
Randomised optimality validation for the incremental D* Lite implementation.

The theoretical claim the manuscript makes is that incremental repair yields the
same solution a fresh search would. That is only credible if it is tested against
an independent optimum after MULTIPLE start advances with intervening cost
changes -- a single move cannot expose an incorrect k_m accumulation.

Each trial: build a random connected graph, then repeatedly
  (1) perturb a random set of edge costs (both increases and decreases),
  (2) advance the start along the current plan,
  (3) compare the D* Lite cost-to-go against a fresh Dijkstra optimum.
"""

import heapq
import math
import random
import unittest

from d2ro.core.graph import TopologicalGraph
from d2ro.core.dstar_lite import DStarLite


def dijkstra_cost(graph: TopologicalGraph, start: str, goal: str) -> float:
    """Independent reference optimum over the graph's current edge costs."""
    dist = {start: 0.0}
    pq = [(0.0, start)]
    seen = set()
    while pq:
        d, u = heapq.heappop(pq)
        if u in seen:
            continue
        seen.add(u)
        if u == goal:
            return d
        for v in graph.successors(u):
            c = graph.get_cost(u, v)
            if c == math.inf:
                continue
            nd = d + c
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist.get(goal, math.inf)


def random_grid(rng, cols=4, rows=4, spacing=100.0):
    """A 4-connected grid: dense enough to have many competing routes."""
    g = TopologicalGraph()
    for i in range(cols):
        for j in range(rows):
            g.add_node(f"n{i}_{j}", i * spacing + rng.uniform(-8, 8),
                       j * spacing + rng.uniform(-8, 8))
    for i in range(cols):
        for j in range(rows):
            if i + 1 < cols:
                g.add_edge(f"n{i}_{j}", f"n{i+1}_{j}", bidirectional=True)
            if j + 1 < rows:
                g.add_edge(f"n{i}_{j}", f"n{i}_{j+1}", bidirectional=True)
    return g


class TestDStarLiteOptimality(unittest.TestCase):
    def test_matches_dijkstra_after_repeated_moves_and_cost_changes(self):
        rng = random.Random(20260815)
        goal = "n3_3"

        for trial in range(150):
            g = random_grid(rng)
            start = "n0_0"
            planner = DStarLite(g, start, goal)
            planner.compute_shortest_path()

            for move in range(5):
                # (1) Perturb a handful of edges, both upward and downward.
                for _ in range(rng.randint(1, 5)):
                    key = rng.choice(list(g.edges.keys()))
                    edge = g.edges[key]
                    edge.w_mesh = rng.choice([0.0, rng.uniform(5.0, 120.0)])
                    planner.notify_edge_cost_change(*key)

                planner.compute_shortest_path()

                # (2) Compare against an independent optimum from the current start.
                reference = dijkstra_cost(g, planner.s_start, goal)
                incremental = planner._get_g(planner.s_start)

                self.assertAlmostEqual(
                    incremental, reference, delta=1e-6,
                    msg=(f"trial {trial} move {move}: D* Lite g={incremental:.4f} "
                         f"but Dijkstra optimum={reference:.4f} "
                         f"from {planner.s_start}")
                )

                # (3) Advance the start one step along the current plan.
                nxt = planner.get_next_waypoint()
                if nxt is None or nxt == goal:
                    break
                planner.update_start(nxt)

    def test_extracted_path_cost_equals_optimum(self):
        """The path actually followed must cost what the optimum costs."""
        rng = random.Random(4242)
        goal = "n3_3"

        for trial in range(80):
            g = random_grid(rng)
            planner = DStarLite(g, "n0_0", goal)
            planner.compute_shortest_path()

            for _ in range(rng.randint(1, 6)):
                key = rng.choice(list(g.edges.keys()))
                g.edges[key].w_mesh = rng.uniform(0.0, 90.0)
                planner.notify_edge_cost_change(*key)
            planner.compute_shortest_path()

            path = planner.extract_full_path()
            self.assertEqual(path[-1], goal, "extracted path must reach the goal")

            walked = sum(g.get_cost(path[i], path[i + 1])
                         for i in range(len(path) - 1))
            self.assertAlmostEqual(
                walked, dijkstra_cost(g, "n0_0", goal), delta=1e-6,
                msg=f"trial {trial}: followed path is not the optimum"
            )

    def test_recovers_when_blocked_edge_reopens(self):
        """Cost decreases must be repaired, not only cost increases."""
        g = random_grid(random.Random(7))
        planner = DStarLite(g, "n0_0", "n3_3")
        planner.compute_shortest_path()

        key = ("n0_0", "n1_0")
        g.edges[key].w_mesh = 10_000.0
        planner.notify_edge_cost_change(*key)
        planner.compute_shortest_path()
        self.assertAlmostEqual(planner._get_g("n0_0"),
                               dijkstra_cost(g, "n0_0", "n3_3"), delta=1e-6)

        g.edges[key].w_mesh = 0.0
        planner.notify_edge_cost_change(*key)
        planner.compute_shortest_path()
        self.assertAlmostEqual(planner._get_g("n0_0"),
                               dijkstra_cost(g, "n0_0", "n3_3"), delta=1e-6)


if __name__ == "__main__":
    unittest.main()
