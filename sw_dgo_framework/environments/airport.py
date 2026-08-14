"""
Realistic Airport Terminal Layout & Autonomous Luggage Trolley Fleet Routing.
Models international airport terminal architecture featuring:
- Massive Open-Plan Check-in Concourse
- Security Checkpoint Chokepoint Corridors
- Duty-Free & Food Court Central Plaza (Open Space with Island Pods)
- Long Narrow Boarding Gate Piers (Gates A1-A4 & Gates B1-B4)
- Arrivals Baggage Reclaim & Multi-Bay Trolley Stacking Depot
- Heavy dynamic passenger crowds with Gaussian proxemic repulsion
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from ..core.graph import TopologicalGraph
from ..core.human import Human

@dataclass
class AirportStructure:
    """Represents a terminal fixture (check-in counters, duty-free stores, security lanes)."""
    x: float
    y: float
    w: float
    h: float
    name: str = "Structure"
    zone_type: str = "checkin"  # "checkin", "security", "retail", "gate", "depot"

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.x + self.w, self.y + self.h)

class AirportLayout:
    """
    Airport Terminal Layout combining wide open concourses with narrow gate corridors.
    """
    def __init__(self):
        self.graph = TopologicalGraph()
        self.structures: List[AirportStructure] = []
        self.trolley_depots: List[str] = []

        self.width = 1200.0
        self.height = 880.0
        self.bounds = (0.0, 0.0, self.width, self.height)

        # Key X Coordinates
        self.x_checkin_hall = 160.0       # Wide Open Check-in Concourse
        self.x_security_choke = 380.0     # Narrow Security Screening
        self.x_dutyfree_plaza = 620.0     # Wide Open Central Plaza
        self.x_gate_pier_a = 920.0        # Pier A (Gates A1-A4)
        self.x_gate_pier_b = 1080.0       # Pier B (Gates B1-B4)

        # Key Y Coordinates
        self.y_north_concourse = 110.0
        self.y_central_axis = 440.0
        self.y_south_concourse = 740.0
        self.y_depot = 800.0

        self._build_airport_topology()

    def _build_airport_topology(self) -> None:
        # 1. WAYPOINT ROADMAP
        # Check-in Concourse Open Grid (Wide Open Space)
        for gx in [100.0, 180.0, 260.0]:
            for gy in [110.0, 270.0, 440.0, 600.0, 740.0]:
                self.graph.add_node(f"N_CHK_{int(gx)}_{int(gy)}", gx, gy)

        # Interconnect Open Check-in Concourse (Multi-Directional Mesh)
        chk_xs = [100.0, 180.0, 260.0]
        chk_ys = [110.0, 270.0, 440.0, 600.0, 740.0]
        for i, gx in enumerate(chk_xs):
            for j, gy in enumerate(chk_ys):
                # Horizontal open edges
                if i < len(chk_xs) - 1:
                    self.graph.add_edge(f"N_CHK_{int(gx)}_{int(gy)}", f"N_CHK_{int(chk_xs[i+1])}_{int(gy)}", is_single_file=False, bidirectional=True)
                # Vertical open edges
                if j < len(chk_ys) - 1:
                    self.graph.add_edge(f"N_CHK_{int(gx)}_{int(gy)}", f"N_CHK_{int(gx)}_{int(chk_ys[j+1])}", is_single_file=False, bidirectional=True)
                # Diagonal open shortcuts
                if i < len(chk_xs) - 1 and j < len(chk_ys) - 1:
                    self.graph.add_edge(f"N_CHK_{int(gx)}_{int(gy)}", f"N_CHK_{int(chk_xs[i+1])}_{int(chk_ys[j+1])}", is_single_file=False, bidirectional=True)

        # Security Checkpoint Chokepoints (Narrow Bottlenecks)
        self.graph.add_node("N_SEC_NORTH", self.x_security_choke, 240.0)
        self.graph.add_node("N_SEC_MID", self.x_security_choke, 440.0)
        self.graph.add_node("N_SEC_SOUTH", self.x_security_choke, 640.0)

        # Connect Check-in to Security
        self.graph.add_edge("N_CHK_260_270", "N_SEC_NORTH", is_single_file=False, bidirectional=True)
        self.graph.add_edge("N_CHK_260_440", "N_SEC_MID", is_single_file=False, bidirectional=True)
        self.graph.add_edge("N_CHK_260_600", "N_SEC_SOUTH", is_single_file=False, bidirectional=True)

        # Duty-Free & Retail Central Plaza (Open Space Grid)
        for px in [480.0, 620.0, 760.0]:
            for py in [160.0, 300.0, 440.0, 580.0, 720.0]:
                self.graph.add_node(f"N_PLAZA_{int(px)}_{int(py)}", px, py)

        plz_xs = [480.0, 620.0, 760.0]
        plz_ys = [160.0, 300.0, 440.0, 580.0, 720.0]
        for i, px in enumerate(plz_xs):
            for j, py in enumerate(plz_ys):
                if i < len(plz_xs) - 1:
                    self.graph.add_edge(f"N_PLAZA_{int(px)}_{int(py)}", f"N_PLAZA_{int(plz_xs[i+1])}_{int(py)}", is_single_file=False, bidirectional=True)
                if j < len(plz_ys) - 1:
                    self.graph.add_edge(f"N_PLAZA_{int(px)}_{int(py)}", f"N_PLAZA_{int(px)}_{int(plz_ys[j+1])}", is_single_file=False, bidirectional=True)
                if i < len(plz_xs) - 1 and j < len(plz_ys) - 1:
                    self.graph.add_edge(f"N_PLAZA_{int(px)}_{int(py)}", f"N_PLAZA_{int(plz_xs[i+1])}_{int(plz_ys[j+1])}", is_single_file=False, bidirectional=True)

        # Connect Security to Plaza
        self.graph.add_edge("N_SEC_NORTH", "N_PLAZA_480_300", is_single_file=False, bidirectional=True)
        self.graph.add_edge("N_SEC_MID", "N_PLAZA_480_440", is_single_file=False, bidirectional=True)
        self.graph.add_edge("N_SEC_SOUTH", "N_PLAZA_480_580", is_single_file=False, bidirectional=True)

        # Boarding Gate Piers (Long Narrow Corridors with Single-File Gate Walks)
        # Pier A (North Gate Corridors)
        self.graph.add_node("N_GATE_A1", self.x_gate_pier_a, 110.0)
        self.graph.add_node("N_GATE_A2", self.x_gate_pier_a, 230.0)
        self.graph.add_node("N_GATE_A3", self.x_gate_pier_a, 350.0)
        self.graph.add_node("N_PIER_A_HUB", self.x_gate_pier_a, 440.0)

        self.graph.add_edge("N_GATE_A1", "N_GATE_A2", is_single_file=True, bidirectional=True)
        self.graph.add_edge("N_GATE_A2", "N_GATE_A3", is_single_file=True, bidirectional=True)
        self.graph.add_edge("N_GATE_A3", "N_PIER_A_HUB", is_single_file=True, bidirectional=True)

        # Pier B (South Gate Corridors)
        self.graph.add_node("N_PIER_B_HUB", self.x_gate_pier_b, 440.0)
        self.graph.add_node("N_GATE_B1", self.x_gate_pier_b, 530.0)
        self.graph.add_node("N_GATE_B2", self.x_gate_pier_b, 650.0)
        self.graph.add_node("N_GATE_B3", self.x_gate_pier_b, 770.0)

        self.graph.add_edge("N_PIER_B_HUB", "N_GATE_B1", is_single_file=True, bidirectional=True)
        self.graph.add_edge("N_GATE_B1", "N_GATE_B2", is_single_file=True, bidirectional=True)
        self.graph.add_edge("N_GATE_B2", "N_GATE_B3", is_single_file=True, bidirectional=True)

        # Connect Plaza to Piers
        self.graph.add_edge("N_PLAZA_760_300", "N_GATE_A3", is_single_file=False, bidirectional=True)
        self.graph.add_edge("N_PLAZA_760_440", "N_PIER_A_HUB", is_single_file=False, bidirectional=True)
        self.graph.add_edge("N_PIER_A_HUB", "N_PIER_B_HUB", is_single_file=False, bidirectional=True)
        self.graph.add_edge("N_PLAZA_760_580", "N_GATE_B1", is_single_file=False, bidirectional=True)

        # Trolley Return Depots (Baggage Claim / Ground Transport)
        self.graph.add_node("TROLLEY_DEPOT_MAIN", 180.0, self.y_depot, is_docking_bay=True)
        self.graph.add_node("TROLLEY_DEPOT_PIER", 620.0, self.y_depot, is_docking_bay=True)
        self.trolley_depots.extend(["TROLLEY_DEPOT_MAIN", "TROLLEY_DEPOT_PIER"])

        self.graph.add_edge("N_CHK_180_740", "TROLLEY_DEPOT_MAIN", is_single_file=False, bidirectional=True)
        self.graph.add_edge("N_PLAZA_620_720", "TROLLEY_DEPOT_PIER", is_single_file=False, bidirectional=True)

        # 2. SOLID TERMINAL STRUCTURES & FIXTURES
        # Check-in Islands (Rows of airline counter desks)
        self.structures.append(AirportStructure(40, 150, 45, 80, name="Emirates Desks", zone_type="checkin"))
        self.structures.append(AirportStructure(40, 330, 45, 80, name="Qatar Airways", zone_type="checkin"))
        self.structures.append(AirportStructure(40, 500, 45, 80, name="Lufthansa Desks", zone_type="checkin"))

        # Security Scanner Blocks (Walls separating checkin and airside)
        self.structures.append(AirportStructure(330, 80, 25, 120, name="Security Wall N", zone_type="security"))
        self.structures.append(AirportStructure(330, 280, 25, 120, name="Body Scanners", zone_type="security"))
        self.structures.append(AirportStructure(330, 480, 25, 120, name="X-Ray Lanes", zone_type="security"))
        self.structures.append(AirportStructure(330, 680, 25, 120, name="Security Wall S", zone_type="security"))

        # Duty-Free Retail Islands (Central Plaza)
        self.structures.append(AirportStructure(520, 200, 65, 60, name="Perfume & Cosmetics", zone_type="retail"))
        self.structures.append(AirportStructure(680, 200, 65, 60, name="Luxury Watches", zone_type="retail"))
        self.structures.append(AirportStructure(520, 500, 65, 60, name="Electronics Hub", zone_type="retail"))
        self.structures.append(AirportStructure(680, 500, 65, 60, name="Café & Bakery", zone_type="retail"))

        # Boarding Gate Lounges (Pier Seating)
        self.structures.append(AirportStructure(960, 80, 60, 70, name="Gate A1 Lounge", zone_type="gate"))
        self.structures.append(AirportStructure(960, 200, 60, 70, name="Gate A2 Lounge", zone_type="gate"))
        self.structures.append(AirportStructure(1120, 500, 60, 70, name="Gate B1 Lounge", zone_type="gate"))
        self.structures.append(AirportStructure(1120, 620, 60, 70, name="Gate B2 Lounge", zone_type="gate"))


class AirportScenarioSuite:
    """
    Airport benchmark scenarios with dense dynamic pedestrian flows and narrow pier bottlenecks.
    """
    @staticmethod
    def get_scenario(scenario_id: str, layout: AirportLayout) -> Tuple[List[Dict], List[Human], str]:
        if scenario_id == "A" or scenario_id == "open_concourse_crowd":
            desc = "Airport Scenario A: High-Density Check-in Concourse. Abandoned trolleys navigate through a dense crowd of 18 roving passengers in the open concourse using Gaussian proxemics."
            trolleys = [
                {"id": 1, "start": "N_CHK_100_110", "goal": "TROLLEY_DEPOT_MAIN"},
                {"id": 2, "start": "N_CHK_260_110", "goal": "TROLLEY_DEPOT_MAIN"},
                {"id": 3, "start": "N_PLAZA_620_160", "goal": "TROLLEY_DEPOT_PIER"},
                {"id": 4, "start": "N_GATE_A1", "goal": "TROLLEY_DEPOT_PIER"},
            ]
            # 18 dynamic passengers roving the open check-in and plaza
            random.seed(303)
            humans = []
            for i in range(18):
                humans.append(Human(
                    id=i + 1,
                    x=random.uniform(80.0, 300.0),
                    y=random.uniform(120.0, 700.0),
                    speed=random.uniform(0.6, 1.3),
                    state="walking"
                ))
            return trolleys, humans, desc

        elif scenario_id == "B" or scenario_id == "pier_head_on":
            desc = "Airport Scenario B: Head-On Passenger Surge in Narrow Gate Pier A. Trolley 1 returns down Pier A while deplaning flight passengers surge up. Trolley 1 detects lock and holds at Pier Hub."
            trolleys = [
                {"id": 1, "start": "N_GATE_A1", "goal": "TROLLEY_DEPOT_PIER"},
                {"id": 2, "start": "N_PIER_A_HUB", "goal": "N_GATE_A1"},
                {"id": 3, "start": "N_GATE_B3", "goal": "TROLLEY_DEPOT_PIER"},
            ]
            humans = [
                Human(1, layout.x_gate_pier_a, 170.0, speed=0.4, state="browsing"),
                Human(2, layout.x_gate_pier_a, 290.0, speed=0.3, state="browsing"),
                Human(3, 580.0, 440.0, speed=0.9, state="walking"),
            ]
            return trolleys, humans, desc

        elif scenario_id == "C" or scenario_id == "security_bottleneck":
            desc = "Airport Scenario C: Security Checkpoint Surge Alert. Security Middle Lane is overwhelmed; leading trolley broadcasts V2V CONGESTION_ALERT diverting fleet via North Lane."
            trolleys = [
                {"id": 1, "start": "N_CHK_100_440", "goal": "TROLLEY_DEPOT_PIER"},
                {"id": 2, "start": "N_CHK_180_440", "goal": "TROLLEY_DEPOT_PIER"},
                {"id": 3, "start": "N_CHK_100_270", "goal": "TROLLEY_DEPOT_MAIN"},
                {"id": 4, "start": "N_GATE_A2", "goal": "TROLLEY_DEPOT_PIER"},
            ]
            humans = [
                Human(1, layout.x_security_choke, 420.0, speed=0.0, state="browsing"),
                Human(2, layout.x_security_choke, 450.0, speed=0.0, state="browsing"),
                Human(3, layout.x_security_choke, 480.0, speed=0.0, state="browsing"),
            ]
            return trolleys, humans, desc

        elif scenario_id == "D" or scenario_id == "duty_free_meandering":
            desc = "Airport Scenario D: Duty-Free Shopping Meander. Shoppers wander randomly between perfume and watch boutiques; autonomous trolleys dynamically yield and calculate open fluid paths."
            trolleys = [
                {"id": 1, "start": "N_SEC_NORTH", "goal": "TROLLEY_DEPOT_PIER"},
                {"id": 2, "start": "N_SEC_SOUTH", "goal": "N_GATE_B3"},
                {"id": 3, "start": "N_GATE_A1", "goal": "TROLLEY_DEPOT_MAIN"},
            ]
            humans = [
                Human(1, 550.0, 300.0, speed=1.1, state="walking"),
                Human(2, 680.0, 350.0, speed=1.0, state="walking"),
                Human(3, 620.0, 480.0, speed=1.2, state="walking"),
                Human(4, 500.0, 580.0, speed=0.9, state="walking"),
                Human(5, 720.0, 600.0, speed=1.0, state="walking"),
            ]
            return trolleys, humans, desc

        else:
            desc = "Airport Scenario E: International Peak Rush Hour. 6 autonomous luggage trolleys collecting across Terminals amid 20 dynamic passengers with heavy luggage."
            trolleys = [
                {"id": 1, "start": "N_CHK_100_110", "goal": "TROLLEY_DEPOT_MAIN"},
                {"id": 2, "start": "N_CHK_260_600", "goal": "TROLLEY_DEPOT_MAIN"},
                {"id": 3, "start": "N_PLAZA_480_160", "goal": "TROLLEY_DEPOT_PIER"},
                {"id": 4, "start": "N_GATE_A1", "goal": "TROLLEY_DEPOT_PIER"},
                {"id": 5, "start": "N_GATE_B3", "goal": "TROLLEY_DEPOT_PIER"},
                {"id": 6, "start": "N_PLAZA_760_720", "goal": "TROLLEY_DEPOT_MAIN"},
            ]
            random.seed(404)
            humans = []
            for i in range(20):
                humans.append(Human(
                    id=i + 1,
                    x=random.uniform(80.0, layout.width - 80.0),
                    y=random.uniform(80.0, layout.height - 120.0),
                    speed=random.uniform(0.6, 1.4)
                ))
            return trolleys, humans, desc
