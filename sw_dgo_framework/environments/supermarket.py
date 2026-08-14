"""
Supermarket Environment Topology Generator.
Constructs realistic supermarket layouts with narrow single-file aisles,
cross-corridors, shelf blocks, and cart return docking bays.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Dict
from ..core.graph import TopologicalGraph

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
            # Top half of aisle
            self.graph.add_edge(f"N_top_{i}", f"N_mid_{i}", is_single_file=True, bidirectional=True)
            # Bottom half of aisle
            self.graph.add_edge(f"N_mid_{i}", f"N_bot_{i}", is_single_file=True, bidirectional=True)

        # 3. Add Horizontal Cross-Aisles (Wide/Bidirectional, not single-file)
        for i in range(self.num_aisles - 1):
            self.graph.add_edge(f"N_top_{i}", f"N_top_{i+1}", is_single_file=False, bidirectional=True)
            self.graph.add_edge(f"N_mid_{i}", f"N_mid_{i+1}", is_single_file=False, bidirectional=True)
            self.graph.add_edge(f"N_bot_{i}", f"N_bot_{i+1}", is_single_file=False, bidirectional=True)

        # 4. Add Cart Return Docking Station
        dock_x = self.start_x + (self.num_aisles // 2) * self.aisle_spacing
        self.graph.add_node("DOCK_BAY", dock_x, y_dock, is_docking_bay=True)
        self.docking_bays.append("DOCK_BAY")

        # Connect Docking Bay to bottom cross-aisle
        for i in range(self.num_aisles):
            self.graph.add_edge(f"N_bot_{i}", "DOCK_BAY", is_single_file=False, bidirectional=True)

        # 5. Build Shelf Obstacles Between Aisles
        shelf_width = self.aisle_spacing - 45.0
        shelf_h1 = (self.aisle_length / 2.0) - 30.0

        for i in range(self.num_aisles - 1):
            shelf_x = self.start_x + i * self.aisle_spacing + 22.5
            # Top shelf block
            self.shelves.append(ShelfObstacle(shelf_x, y_top + 15.0, shelf_width, shelf_h1, name=f"Shelf_T_{i}"))
            # Bottom shelf block
            self.shelves.append(ShelfObstacle(shelf_x, y_mid + 15.0, shelf_width, shelf_h1, name=f"Shelf_B_{i}"))
