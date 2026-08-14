"""
Supermarket Environment Topology and Multi-Scenario Suite.
Constructs realistic retail layouts and scenario configurations for D²RO evaluation.
"""

from __future__ import annotations
import random
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from ..core.graph import TopologicalGraph
from ..core.human import Human

@dataclass
class ShelfObstacle:
    """Rectangular shelf obstacle for collision checks and rendering."""
    x: float
    y: float
    w: float
    h: float
    name: str = "Shelf"

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        return (self.x, self.y, self.x + self.w, self.y + self.h)

class SupermarketLayout:
    """
    Creates an orthogonal retail layout with:
    - Multiple parallel single-file aisles
    - Top, middle, and bottom cross-aisles
    - Cart return docking bays
    """
    def __init__(self, num_aisles: int = 5, aisle_length: float = 350.0,
                 aisle_spacing: float = 140.0, start_x: float = 150.0, start_y: float = 120.0):
        self.num_aisles = num_aisles
        self.aisle_length = aisle_length
        self.aisle_spacing = aisle_spacing
        self.start_x = start_x
        self.start_y = start_y

        self.graph = TopologicalGraph()
        self.shelves: List[ShelfObstacle] = []
        self.docking_bays: List[str] = []
        self.bounds = (0.0, 0.0, start_x + (num_aisles + 1) * aisle_spacing + 100.0, start_y + aisle_length + 180.0)

        self._build_layout()

    def _build_layout(self) -> None:
        """Constructs nodes, single-file aisle edges, cross-aisles, and shelf obstacles."""
        y_top = self.start_y
        y_mid = self.start_y + (self.aisle_length / 2.0)
        y_bot = self.start_y + self.aisle_length
        y_dock = y_bot + 80.0

        # 1. Create Nodes at Aisle Junctions
        for i in range(self.num_aisles):
            x = self.start_x + i * self.aisle_spacing
            self.graph.add_node(f"N_top_{i}", x, y_top)
            self.graph.add_node(f"N_mid_{i}", x, y_mid)
            self.graph.add_node(f"N_bot_{i}", x, y_bot)

        # 2. Add Vertical Aisle Edges (Marked Single-File)
        for i in range(self.num_aisles):
            self.graph.add_edge(f"N_top_{i}", f"N_mid_{i}", is_single_file=True, bidirectional=True)
            self.graph.add_edge(f"N_mid_{i}", f"N_bot_{i}", is_single_file=True, bidirectional=True)

        # 3. Add Horizontal Cross-Aisles (Wide/Bidirectional)
        for i in range(self.num_aisles - 1):
            self.graph.add_edge(f"N_top_{i}", f"N_top_{i+1}", is_single_file=False, bidirectional=True)
            self.graph.add_edge(f"N_mid_{i}", f"N_mid_{i+1}", is_single_file=False, bidirectional=True)
            self.graph.add_edge(f"N_bot_{i}", f"N_bot_{i+1}", is_single_file=False, bidirectional=True)

        # 4. Add Cart Return Docking Station
        dock_x = self.start_x + (self.num_aisles // 2) * self.aisle_spacing
        self.graph.add_node("DOCK_BAY", dock_x, y_dock, is_docking_bay=True)
        self.docking_bays.append("DOCK_BAY")

        for i in range(self.num_aisles):
            self.graph.add_edge(f"N_bot_{i}", "DOCK_BAY", is_single_file=False, bidirectional=True)

        # 5. Build Shelf Obstacles Between Aisles
        shelf_width = self.aisle_spacing - 45.0
        shelf_h1 = (self.aisle_length / 2.0) - 30.0

        for i in range(self.num_aisles - 1):
            shelf_x = self.start_x + i * self.aisle_spacing + 22.5
            self.shelves.append(ShelfObstacle(shelf_x, y_top + 15.0, shelf_width, shelf_h1, name=f"Shelf_T_{i}"))
            self.shelves.append(ShelfObstacle(shelf_x, y_mid + 15.0, shelf_width, shelf_h1, name=f"Shelf_B_{i}"))


class ScenarioSuite:
    """
    Generates distinct benchmark scenarios evaluating specific capabilities of SW-DGO.
    """
    @staticmethod
    def get_scenario(scenario_id: str, layout: SupermarketLayout) -> Tuple[List[Dict], List[Human], str]:
        """
        Returns (trolley_configs, humans_list, description)
        """
        if scenario_id == "A" or scenario_id == "crowded_aisle":
            # Scenario A: Dense crowd blocking Aisle 2 -> Trolleys proactively divert to Aisles 0, 1, 3, 4
            desc = "Scenario A: Dense Shopper Crowd in Aisle 2. Trolleys detect Gaussian proxemics and proactively detour via adjacent aisles."
            trolleys = [
                {"id": 1, "start": "N_top_2", "goal": "DOCK_BAY"},
                {"id": 2, "start": "N_top_2", "goal": "DOCK_BAY"},
                {"id": 3, "start": "N_top_1", "goal": "DOCK_BAY"},
                {"id": 4, "start": "N_top_3", "goal": "DOCK_BAY"},
            ]
            x_aisle2 = layout.start_x + 2 * layout.aisle_spacing
            humans = [
                Human(1, x_aisle2, 220.0, speed=0.3, state="browsing"),
                Human(2, x_aisle2 + 10, 260.0, speed=0.4, state="browsing"),
                Human(3, x_aisle2 - 8, 300.0, speed=0.3, state="browsing"),
                Human(4, x_aisle2, 340.0, speed=0.2, state="browsing"),
                Human(5, layout.start_x + 3 * layout.aisle_spacing, 420.0, speed=0.8),
            ]
            return trolleys, humans, desc

        elif scenario_id == "B" or scenario_id == "head_on_lock":
            # Scenario B: Corridor Lock & Head-on Negotiation in Single-File Aisle 1
            desc = "Scenario B: Head-On Encounter in Single-File Aisle 1. Mutual exclusion lock (R_lock) prevents live-lock; opposing trolley reroutes to Aisle 2."
            trolleys = [
                {"id": 1, "start": "N_top_1", "goal": "N_bot_1"},
                {"id": 2, "start": "N_bot_1", "goal": "N_top_1"},
                {"id": 3, "start": "N_top_3", "goal": "DOCK_BAY"},
            ]
            humans = [
                Human(1, layout.start_x + 0 * layout.aisle_spacing, 250.0, speed=0.9),
                Human(2, layout.start_x + 4 * layout.aisle_spacing, 350.0, speed=0.9),
            ]
            return trolleys, humans, desc

        elif scenario_id == "C" or scenario_id == "mesh_blockage":
            # Scenario C: Sudden Physical Blockage & V2V Mesh Broadcast
            desc = "Scenario C: Sudden Blockage in Aisle 0. Trolley 1 broadcasts CONGESTION_ALERT over V2V mesh; rear trolleys divert before entering."
            trolleys = [
                {"id": 1, "start": "N_top_0", "goal": "DOCK_BAY"},
                {"id": 2, "start": "N_top_0", "goal": "DOCK_BAY"},
                {"id": 3, "start": "N_top_1", "goal": "DOCK_BAY"},
                {"id": 4, "start": "N_top_4", "goal": "DOCK_BAY"},
            ]
            # Dense blockage in Aisle 0
            x_aisle0 = layout.start_x + 0 * layout.aisle_spacing
            humans = [
                Human(1, x_aisle0, 240.0, speed=0.0, state="browsing"),
                Human(2, x_aisle0, 270.0, speed=0.0, state="browsing"),
                Human(3, x_aisle0, 310.0, speed=0.0, state="browsing"),
            ]
            return trolleys, humans, desc

        elif scenario_id == "D" or scenario_id == "social_crossing":
            # Scenario D: Pedestrian Cross-Traffic & Social Yielding/Braking
            desc = "Scenario D: Pedestrian Cross-Traffic. Dynamic shoppers cross aisles; trolleys politely brake/yield without colliding."
            trolleys = [
                {"id": 1, "start": "N_top_0", "goal": "DOCK_BAY"},
                {"id": 2, "start": "N_top_2", "goal": "DOCK_BAY"},
                {"id": 3, "start": "N_top_4", "goal": "DOCK_BAY"},
            ]
            humans = [
                Human(1, 200.0, 295.0, speed=1.3, state="walking"),
                Human(2, 600.0, 295.0, speed=1.1, state="walking"),
                Human(3, 350.0, 470.0, speed=1.0, state="walking"),
                Human(4, 500.0, 470.0, speed=1.2, state="walking"),
            ]
            return trolleys, humans, desc

        else:
            # Scenario E: High-Density Supermarket Rush Hour
            desc = "Scenario E: Supermarket Rush Hour. 6 autonomous trolleys navigating alongside 10 dynamic shoppers."
            trolleys = [
                {"id": 1, "start": "N_top_0", "goal": "DOCK_BAY"},
                {"id": 2, "start": "N_top_1", "goal": "DOCK_BAY"},
                {"id": 3, "start": "N_top_2", "goal": "DOCK_BAY"},
                {"id": 4, "start": "N_top_3", "goal": "DOCK_BAY"},
                {"id": 5, "start": "N_top_4", "goal": "DOCK_BAY"},
                {"id": 6, "start": "N_mid_2", "goal": "DOCK_BAY"},
            ]
            random.seed(42)
            humans = []
            min_x, min_y, max_x, max_y = layout.bounds
            for i in range(10):
                humans.append(Human(
                    id=i + 1,
                    x=random.uniform(min_x + 80, max_x - 80),
                    y=random.uniform(min_y + 80, max_y - 80),
                    speed=random.uniform(0.7, 1.3)
                ))
            return trolleys, humans, desc
