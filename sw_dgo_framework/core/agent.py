"""
Autonomous Trolley Agent for SW-DGO Framework.
Combines D* Lite incremental planning, V2V mesh telemetry, Gaussian human proxemics,
and spatiotemporal corridor locks.
"""

from __future__ import annotations
import math
from typing import Dict, List, Tuple, Optional, Any
from .graph import TopologicalGraph
from .dstar_lite import DStarLite
from .mesh_network import MeshNetwork, MessageType, MeshPacket
from .human import Human, ProxemicsField

class TrolleyAgent:
    """
    Autonomous Mobile Shopping Trolley (Int-Cart).
    Executes decentralized SW-DGO routing logic with local graph memory.
    """
    def __init__(self, agent_id: int, graph: TopologicalGraph, start_node: str, goal_node: str,
                 mesh_net: MeshNetwork, max_speed: float = 3.0, comm_radius: float = 300.0):
        self.agent_id = agent_id
        # Decentralized local graph memory
        self.graph = graph.clone()
        self.current_node = start_node
        self.goal_node = goal_node
        self.mesh_net = mesh_net

        # Kinematic state
        node_obj = self.graph.get_node(start_node)
        self.x: float = node_obj.x
        self.y: float = node_obj.y
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.max_speed = max_speed
        self.heading: float = 0.0

        # High-level planning
        self.planner = DStarLite(self.graph, start_node, goal_node)
        self.planner.compute_shortest_path()
        self.target_node: Optional[str] = self.planner.get_next_waypoint()

        # State machine: "NAVIGATING", "WAITING_LOCK", "DOCKED"
        self.state: str = "NAVIGATING"
        self.active_lock_edge: Optional[Tuple[str, str]] = None
        self.wait_timer: float = 0.0

        # Performance & Benchmark Metrics
        self.total_distance: float = 0.0
        self.travel_time: float = 0.0
        self.replan_count: int = 0
        self.deadlock_count: int = 0
        self.proxemic_violations: int = 0
        self.is_docked: bool = False

        # Register with mesh network
        self.mesh_net.register_agent(self.agent_id, self)

    @property
    def current_pos(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def process_inbound_mesh(self) -> bool:
        """Consumes V2V packets from mesh queue and updates local edge weights."""
        packets = self.mesh_net.fetch_inbound(self.agent_id)
        cost_changed = False

        for pkt in packets:
            u, v = pkt.edge
            if pkt.msg_type == MessageType.CONGESTION_ALERT:
                if self.graph.update_mesh_penalty(u, v, pkt.cost_penalty):
                    self.planner.notify_edge_cost_change(u, v)
                    cost_changed = True
            elif pkt.msg_type == MessageType.LOCK_REQUEST:
                # If opposing edge is locked by remote peer, mark directional lock in local graph
                edge = self.graph.get_edge(u, v)
                if edge and edge.is_single_file:
                    edge.r_lock = math.inf
                    edge.lock_owner = pkt.sender_id
                    edge.lock_expiry = pkt.timestamp + 10.0
                    self.planner.notify_edge_cost_change(u, v)
                    cost_changed = True
            elif pkt.msg_type == MessageType.LOCK_RELEASE:
                edge = self.graph.get_edge(u, v)
                if edge and edge.lock_owner == pkt.sender_id:
                    edge.r_lock = 0.0
                    edge.lock_owner = None
                    self.planner.notify_edge_cost_change(u, v)
                    cost_changed = True

        return cost_changed

    def update_human_proxemics(self, humans: List[Human], prox_field: ProxemicsField) -> bool:
        """Calculates Gaussian discomfort bubbles for nearby waypoints and updates graph."""
        cost_changed = False
        for node_id, node in self.graph.nodes.items():
            dist = math.hypot(self.x - node.x, self.y - node.y)
            # Sense within onboard sensor range (150 pixels)
            if dist <= 150.0:
                penalty = prox_field.compute_penalty_at_point(node.x, node.y, humans)
                changed_edges = self.graph.update_proxemic_penalty(node_id, penalty)
                for u, v in changed_edges:
                    self.planner.notify_edge_cost_change(u, v)
                    cost_changed = True
        return cost_changed

    def check_proxemic_violations(self, humans: List[Human], violation_dist: float = 25.0) -> None:
        """Records comfort violation metric if agent enters intimate shopper zone."""
        for human in humans:
            if math.hypot(self.x - human.x, self.y - human.y) < violation_dist:
                self.proxemic_violations += 1
                break

    def step(self, dt: float, humans: List[Human], prox_field: ProxemicsField,
             current_sim_time: float) -> None:
        """Main D2RO execution tick."""
        if self.is_docked:
            return

        self.travel_time += dt

        # 1. Process V2V Mesh Telemetry & Local Sensors
        mesh_changed = self.process_inbound_mesh()
        prox_changed = self.update_human_proxemics(humans, prox_field)
        self.check_proxemic_violations(humans)

        # 2. Incremental Replan if any edge costs changed
        if mesh_changed or prox_changed:
            self.planner.compute_shortest_path()
            self.replan_count += 1
            self.target_node = self.planner.get_next_waypoint()

        # 3. Check if reached goal
        if self.current_node == self.goal_node:
            self.is_docked = True
            self.state = "DOCKED"
            if self.active_lock_edge:
                self._release_lock(current_sim_time)
            return

        # 4. Waypoint & Corridor Lock Verification
        if self.target_node is None:
            self.planner.compute_shortest_path()
            self.target_node = self.planner.get_next_waypoint()
            if self.target_node is None:
                self.deadlock_count += 1
                return

        edge = self.graph.get_edge(self.current_node, self.target_node)
        if edge and edge.is_single_file:
            opp_edge = self.graph.get_edge(self.target_node, self.current_node)
            # Check if opposing direction is locked by another agent
            if opp_edge and opp_edge.lock_owner is not None and opp_edge.lock_owner != self.agent_id:
                # Opposing lock active: wait or force alternate path
                self.state = "WAITING_LOCK"
                self.wait_timer += dt
                if self.wait_timer > 3.0:
                    # Reroute via SW-DGO: temporarily inflate edge cost
                    edge.r_lock = math.inf
                    self.planner.notify_edge_cost_change(self.current_node, self.target_node)
                    self.planner.compute_shortest_path()
                    self.target_node = self.planner.get_next_waypoint()
                    self.wait_timer = 0.0
                return
            else:
                # Acquire lock if not already held
                if self.active_lock_edge != (self.current_node, self.target_node):
                    self._acquire_lock(self.current_node, self.target_node, current_sim_time)

        self.state = "NAVIGATING"
        self.wait_timer = 0.0

        # 5. Kinematic Motion towards target node
        target_obj = self.graph.get_node(self.target_node)
        dx = target_obj.x - self.x
        dy = target_obj.y - self.y
        dist = math.hypot(dx, dy)

        if dist < 6.0:  # Waypoint arrival threshold
            # Advance to next waypoint
            if self.active_lock_edge and self.active_lock_edge != (self.current_node, self.target_node):
                self._release_lock(current_sim_time)

            self.current_node = self.target_node
            self.planner.update_start(self.current_node)
            self.planner.compute_shortest_path()
            self.target_node = self.planner.get_next_waypoint()
        else:
            # Kinematic step
            self.heading = math.atan2(dy, dx)
            step_dist = min(dist, self.max_speed * dt * 30.0)
            self.vx = math.cos(self.heading) * (step_dist / (dt * 30.0))
            self.vy = math.sin(self.heading) * (step_dist / (dt * 30.0))
            self.x += math.cos(self.heading) * step_dist
            self.y += math.sin(self.heading) * step_dist
            self.total_distance += step_dist

    def broadcast_congestion(self, u: str, v: str, penalty: float, current_time: float) -> None:
        """Broadcasts localized blockage/congestion alert across V2V mesh."""
        self.graph.update_mesh_penalty(u, v, penalty)
        self.planner.notify_edge_cost_change(u, v)
        self.mesh_net.broadcast(
            sender_id=self.agent_id,
            msg_type=MessageType.CONGESTION_ALERT,
            edge=(u, v),
            cost_penalty=penalty,
            ttl=3,
            current_time=current_time
        )

    def _acquire_lock(self, u: str, v: str, current_time: float) -> None:
        edge = self.graph.get_edge(u, v)
        if edge:
            edge.lock_owner = self.agent_id
            edge.lock_expiry = current_time + 10.0
            self.active_lock_edge = (u, v)
            self.mesh_net.broadcast(
                sender_id=self.agent_id,
                msg_type=MessageType.LOCK_REQUEST,
                edge=(u, v),
                ttl=2,
                current_time=current_time
            )

    def _release_lock(self, current_time: float) -> None:
        if self.active_lock_edge:
            u, v = self.active_lock_edge
            edge = self.graph.get_edge(u, v)
            if edge and edge.lock_owner == self.agent_id:
                edge.lock_owner = None
                edge.r_lock = 0.0
                self.mesh_net.broadcast(
                    sender_id=self.agent_id,
                    msg_type=MessageType.LOCK_RELEASE,
                    edge=(u, v),
                    ttl=2,
                    current_time=current_time
                )
            self.active_lock_edge = None
