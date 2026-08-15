"""
Topological Graph Representation for SW-DGO Framework.
Models nodes (aisle junctions/waypoints) and directed edges with calibrated 5-component weighted costs:
C(u, v, t) = w_D * D(u, v) + w_M * W_mesh(u, v, t) + w_H * H_prox(v, t) + w_R * R_lock(u, v, t) + w_S * S_trolley(v, t)
"""

from __future__ import annotations
import math
import copy
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set

from sw_dgo_framework.core.units import (
    WEIGHT_DISTANCE_WD, WEIGHT_MESH_WM, WEIGHT_PROXEMIC_WH,
    WEIGHT_MUTEX_LOCK_WR, WEIGHT_TROLLEY_WS, PX_TO_M
)

@dataclass
class Node:
    """Represents a topological waypoint in the service environment."""
    id: str
    x: float
    y: float
    is_docking_bay: bool = False
    is_charging_station: bool = False

    @property
    def pos(self) -> Tuple[float, float]:
        return (self.x, self.y)

    @property
    def pos_m(self) -> Tuple[float, float]:
        """Returns coordinate in meters (SI metric)."""
        return (self.x * PX_TO_M, self.y * PX_TO_M)

@dataclass
class Edge:
    """
    Directed edge between two nodes with SW-DGO 5-component weighted traversal cost:
    C(u, v, t) = w_D * D(u, v) + w_M * W_mesh(u, v, t) + w_H * H_prox(v, t) + w_R * R_lock(u, v) + w_S * S_trolley
    """
    u: str
    v: str
    d: float  # Baseline physical Euclidean distance / traversal length
    is_single_file: bool = False  # True if corridor cannot accommodate bidirectional traffic
    w_mesh: float = 0.0      # Distributed mesh congestion penalty
    h_prox: float = 0.0      # Asymmetric human proxemic discomfort penalty
    r_lock: float = 0.0      # Directional corridor lock penalty (0.0 or math.inf)
    s_trolley: float = 0.0   # Kinetic vehicle clearance envelope penalty

    # Weight coefficients
    weight_d: float = WEIGHT_DISTANCE_WD
    weight_m: float = WEIGHT_MESH_WM
    weight_h: float = WEIGHT_PROXEMIC_WH
    weight_r: float = WEIGHT_MUTEX_LOCK_WR
    weight_s: float = WEIGHT_TROLLEY_WS

    # Active lock metadata
    lock_owner: Optional[int] = None  # Agent ID holding current lock
    lock_expiry: float = 0.0          # Simulation timestamp when lock expires

    @property
    def cost(self) -> float:
        """Returns total calibrated composite traversal cost."""
        if self.r_lock == math.inf:
            return math.inf
        total_cost = (
            self.weight_d * self.d +
            self.weight_m * self.w_mesh +
            self.weight_h * self.h_prox +
            self.weight_r * self.r_lock +
            self.weight_s * self.s_trolley
        )
        return max(0.001, total_cost)

class TopologicalGraph:
    """
    Directed graph modeling indoor facility topology with dynamic edge costs.
    Supports predecessor/successor lookups for incremental D* Lite heuristic search.
    """
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[Tuple[str, str], Edge] = {}
        self._succ: Dict[str, List[str]] = {}
        self._pred: Dict[str, List[str]] = {}

    def clone(self) -> TopologicalGraph:
        """Creates an independent deep copy of the topological graph for decentralized agent memory."""
        new_g = TopologicalGraph()
        for node_id, node in self.nodes.items():
            new_g.nodes[node_id] = Node(
                id=node.id, x=node.x, y=node.y,
                is_docking_bay=node.is_docking_bay,
                is_charging_station=node.is_charging_station
            )
            new_g._succ[node_id] = list(self._succ.get(node_id, []))
            new_g._pred[node_id] = list(self._pred.get(node_id, []))

        for key, edge in self.edges.items():
            new_g.edges[key] = Edge(
                u=edge.u, v=edge.v, d=edge.d,
                is_single_file=edge.is_single_file,
                w_mesh=edge.w_mesh, h_prox=edge.h_prox,
                r_lock=edge.r_lock, s_trolley=edge.s_trolley,
                weight_d=edge.weight_d, weight_m=edge.weight_m,
                weight_h=edge.weight_h, weight_r=edge.weight_r,
                weight_s=edge.weight_s, lock_owner=edge.lock_owner,
                lock_expiry=edge.lock_expiry
            )
        return new_g

    def add_node(self, node_id: str, x: float, y: float, is_docking_bay: bool = False) -> Node:
        node = Node(id=node_id, x=x, y=y, is_docking_bay=is_docking_bay)
        self.nodes[node_id] = node
        if node_id not in self._succ:
            self._succ[node_id] = []
        if node_id not in self._pred:
            self._pred[node_id] = []
        return node

    def add_edge(self, u: str, v: str, is_single_file: bool = False, bidirectional: bool = True) -> None:
        """Adds a directed edge (or bidirectional pair) between node u and node v."""
        if u not in self.nodes or v not in self.nodes:
            raise ValueError(f"Nodes {u} and {v} must exist before creating an edge.")

        p_u = self.nodes[u]
        p_v = self.nodes[v]
        dist = math.hypot(p_u.x - p_v.x, p_u.y - p_v.y)

        # Forward edge
        edge_uv = Edge(u=u, v=v, d=dist, is_single_file=is_single_file)
        self.edges[(u, v)] = edge_uv
        if v not in self._succ[u]:
            self._succ[u].append(v)
        if u not in self._pred[v]:
            self._pred[v].append(u)

        if bidirectional:
            edge_vu = Edge(u=v, v=u, d=dist, is_single_file=is_single_file)
            self.edges[(v, u)] = edge_vu
            if u not in self._succ[v]:
                self._succ[v].append(u)
            if v not in self._pred[u]:
                self._pred[u].append(v)

    def get_node(self, node_id: str) -> Node:
        return self.nodes[node_id]

    def get_edge(self, u: str, v: str) -> Optional[Edge]:
        return self.edges.get((u, v), None)

    def get_cost(self, u: str, v: str) -> float:
        edge = self.get_edge(u, v)
        if edge is None:
            return math.inf
        return edge.cost

    def successors(self, u: str) -> List[str]:
        return self._succ.get(u, [])

    def predecessors(self, v: str) -> List[str]:
        return self._pred.get(v, [])

    def distance(self, u: str, v: str) -> float:
        """Euclidean distance heuristic between two nodes."""
        n1 = self.nodes[u]
        n2 = self.nodes[v]
        return math.hypot(n1.x - n2.x, n1.y - n2.y)

    def update_mesh_penalty(self, u: str, v: str, penalty: float) -> bool:
        """Updates mesh congestion penalty on an edge. Returns True if modified."""
        edge = self.get_edge(u, v)
        if edge and edge.w_mesh != penalty:
            edge.w_mesh = penalty
            return True
        return False

    def update_proxemic_penalty(self, v: str, penalty: float) -> List[Tuple[str, str]]:
        """Updates human proxemic penalty for all incoming edges to node v."""
        changed_edges = []
        for u in self.predecessors(v):
            edge = self.get_edge(u, v)
            if edge and abs(edge.h_prox - penalty) > 1e-3:
                edge.h_prox = penalty
                changed_edges.append((u, v))
        return changed_edges

    def decay_mesh_penalties(self, dt: float, decay_rate: float = 2.0) -> List[Tuple[str, str]]:
        """Decays mesh congestion penalties over time."""
        changed_edges = []
        for key, edge in list(self.edges.items()):
            if isinstance(edge, Edge) and edge.w_mesh > 0.0:
                old_val = edge.w_mesh
                edge.w_mesh = max(0.0, edge.w_mesh - decay_rate * dt)
                if math.fabs(old_val - edge.w_mesh) > 0.1:
                    changed_edges.append((edge.u, edge.v))
        return changed_edges

    def clean_expired_locks(self, current_time: float) -> List[Tuple[str, str]]:
        """Releases expired corridor locks."""
        unlocked_edges = []
        for key, edge in list(self.edges.items()):
            if isinstance(edge, Edge) and edge.lock_owner is not None and current_time >= edge.lock_expiry:
                edge.lock_owner = None
                edge.r_lock = 0.0
                unlocked_edges.append((edge.u, edge.v))
        return unlocked_edges
