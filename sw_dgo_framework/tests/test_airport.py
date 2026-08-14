"""
Unit Tests for Airport Terminal Layout & Autonomous Luggage Trolley Routing.
"""

import unittest
from sw_dgo_framework.environments.airport import AirportLayout, AirportScenarioSuite

class TestAirportFramework(unittest.TestCase):
    def test_airport_layout_graph_connectivity(self):
        """Verify that open check-in concourses, security lanes, plaza, and gate piers are connected."""
        layout = AirportLayout()
        self.assertIn("N_CHK_100_110", layout.graph.nodes)
        self.assertIn("N_SEC_NORTH", layout.graph.nodes)
        self.assertIn("N_PLAZA_480_160", layout.graph.nodes)
        self.assertIn("N_GATE_A1", layout.graph.nodes)
        self.assertIn("N_GATE_B3", layout.graph.nodes)
        self.assertIn("TROLLEY_DEPOT_MAIN", layout.graph.nodes)

    def test_airport_scenario_generation(self):
        """Verify airport scenario suites generate valid dynamic passenger crowds."""
        layout = AirportLayout()
        trolleys, humans, desc = AirportScenarioSuite.get_scenario("A", layout)
        self.assertEqual(len(humans), 18)
        self.assertEqual(len(trolleys), 4)

if __name__ == "__main__":
    unittest.main()
