"""
Unit Tests for Directional Corridor Lock and Deadlock Prevention.
"""

import unittest
from d2ro.core.graph import TopologicalGraph
from d2ro.core.mesh_network import MeshNetwork
from d2ro.core.agent import TrolleyAgent
from d2ro.core.human import ProxemicsField

class TestCorridorLock(unittest.TestCase):
    def test_corridor_lock_mutual_exclusion(self):
        """
        Verify that two agents approaching a single-file corridor in opposite directions
        do not enter simultaneously; the first acquires lock and the second waits/reroutes.
        """
        g = TopologicalGraph()
        # A --- (single-file aisle) --- B
        # |                             |
        # C ------- (parallel) -------- D
        g.add_node("A", 0.0, 0.0)
        g.add_node("B", 100.0, 0.0)
        g.add_node("C", 0.0, 50.0)
        g.add_node("D", 100.0, 50.0)

        g.add_edge("A", "B", is_single_file=True, bidirectional=True)
        g.add_edge("A", "C", is_single_file=False, bidirectional=True)
        g.add_edge("C", "D", is_single_file=False, bidirectional=True)
        g.add_edge("D", "B", is_single_file=False, bidirectional=True)

        mesh = MeshNetwork(comm_radius=300.0)
        prox = ProxemicsField()

        # Agent 1 starts at A heading to B
        agent1 = TrolleyAgent(agent_id=1, graph=g, start_node="A", goal_node="B", mesh_net=mesh)
        # Agent 2 starts at B heading to A
        agent2 = TrolleyAgent(agent_id=2, graph=g, start_node="B", goal_node="A", mesh_net=mesh)

        # Step Agent 1 -> acquires lock on (A, B)
        agent1.step(dt=0.1, humans=[], prox_field=prox, current_sim_time=0.1)
        self.assertEqual(agent1.active_lock_edge, ("A", "B"))

        # Step Agent 2 -> receives lock notice -> enters WAITING_LOCK
        agent2.step(dt=0.1, humans=[], prox_field=prox, current_sim_time=0.1)
        self.assertEqual(agent2.state, "WAITING_LOCK")

        # Step Agent 2 until wait_timer > 3.0 triggers D* Lite reroute to alternate route
        for _ in range(32):
            agent2.step(dt=0.1, humans=[], prox_field=prox, current_sim_time=0.1)

        # Agent 2 should now have rerouted away from (A, B)
        self.assertIn(agent2.target_node, ["D", "C"])
        self.assertNotEqual(agent2.target_node, "A")

if __name__ == "__main__":
    unittest.main()
