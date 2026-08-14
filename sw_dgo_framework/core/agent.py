"""
Autonomous Trolley Agent for SW-DGO Framework.
Combines D* Lite incremental planning, V2V mesh telemetry, continuous Gaussian human proxemics,
spatiotemporal corridor locks, and micro-kinematic social yielding/braking.
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
    Executes decentralized SW-DGO routing logic with social yielding and braking.
    """
    def __init__(self, agent_id: int, graph: TopologicalGraph, start_node: str, goal_node: str,
                 mesh_net: MeshNetwork, max_speed: float = 2.8, comm_radius: float = 350.0):
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
        self.radius: float = 12.0  # Physical trolley radius (pixels)

        # High-level planning
        self.planner = DStarLite(self.graph, start_node, goal_node)
        self.planner.compute_shortest_path()
        self.target_node: Optional[str] = self.planner.get_next_waypoint()

        # State machine: "NAVIGATING", "WAITING_LOCK", "YIELDING_HUMAN", "DOCKED"
        self.state: str = "NAVIGATING"
        self.active_lock_edge: Optional[Tuple[str, str]] = None
        self.wait_timer: float = 0.0
        self.yield_timer: float = 0.0

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
        """
        Samples continuous personal-space discomfort along all nearby corridor edges.
        Triggers incremental replan if any edge cost changes significantly.
        """
        cost_changed = False
        for (u, v), edge in self.graph.edges.items():
            nu = self.graph.get_node(u)
            nv = self.graph.get_node(v)
            # Check if edge is within onboard perception range (e.g. 200 pixels)
            d_u = math.hypot(self.x - nu.x, self.y - nu.y)
            d_v = math.hypot(self.x - nv.x, self.y - nv.y)
            if min(d_u, d_v) <= 220.0:
                seg_penalty = prox_field.compute_edge_segment_penalty((nu.x, nu.y), (nv.x, nv.y), humans)
                if abs(edge.h_prox - seg_penalty) > 5.0:
                    edge.h_prox = seg_penalty
                    self.planner.notify_edge_cost_change(u, v)
                    cost_changed = True
        return cost_changed

    def check_human_collision_and_yield(self, humans: List[Human], dt: float,
                                        current_sim_time: float) -> bool:
        """
        Micro-kinematic social yielding:
        If a human is within intimate distance (32 pixels) directly in front of the cart,
        the trolley immediately brakes to 0 and yields politely.
        If blocked for > 1.2s, broadcasts a mesh congestion alert to divert peer carts.
        """
        yield_required = False
        for human in humans:
            dist = math.hypot(self.x - human.x, self.y - human.y)
            if dist < 24.0:
                self.proxemic_violations += 1

            # Check if human is in immediate forward path (within 35 pixels)
            if dist < 36.0:
                dx = human.x - self.x
                dy = human.y - self.y
                dot = math.cos(self.heading) * dx + math.sin(self.heading) * dy
                if dot > 0:  # Human is in front
                    yield_required = True
                    break

        if yield_required:
            self.state = "YIELDING_HUMAN"
            self.yield_timer += dt
            self.vx = 0.0
            self.vy = 0.0

            # If persistently blocked by a browsing crowd in this aisle, trigger proactive reroute
            if self.yield_timer > 1.2 and self.target_node:
                # Mark current edge congested and alert peers
                curr_edge = (self.current_node, self.target_node)
                self.broadcast_congestion(self.current_node, self.target_node, penalty=400.0,
                                         current_time=current_sim_time)
                self.planner.compute_shortest_path()
                self.target_node = self.planner.get_next_waypoint()
                self.yield_timer = 0.0
            return True

        self.yield_timer = 0.0
        return False

    def step(self, dt: float, humans: List[Human], prox_field: ProxemicsField,
             current_sim_time: float) -> None:
        """Main D2RO execution tick."""
        if self.is_docked:
            return

        self.travel_time += dt

        # 1. Process V2V Mesh Telemetry & Local Proxemic Edge Sensing
        mesh_changed = self.process_inbound_mesh()
        prox_changed = self.update_human_proxemics(humans, prox_field)

        # 2. Incremental Replan if edge costs updated
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

        # 4. Check Micro-Kinematic Social Yielding (Stop if human is directly ahead)
        if self.check_human_collision_and_yield(humans, dt, current_sim_time):
            return

        # 5. Waypoint & Corridor Lock Verification
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
                self.state = "WAITING_LOCK"
                self.wait_timer += dt
                if self.wait_timer > 2.5:
                    # Reroute via SW-DGO: mark edge locked locally and choose parallel aisle
                    edge.r_lock = math.inf
                    self.planner.notify_edge_cost_change(self.current_node, self.target_node)
                    self.planner.compute_shortest_path()
                    self.target_node = self.planner.get_next_waypoint()
                    self.wait_timer = 0.0
                return
            else:
                if self.active_lock_edge != (self.current_node, self.target_node):
                    self._acquire_lock(self.current_node, self.target_node, current_sim_time)

        self.state = "NAVIGATING"
        self.wait_timer = 0.0

        # 6. Kinematic Motion towards target node
        target_obj = self.graph.get_node(self.target_node)
        dx = target_obj.x - self.x
        dy = target_obj.y - self.y
        dist = math.hypot(dx, dy)

        if dist < 6.0:  # Waypoint arrival threshold
            if self.active_lock_edge and self.active_lock_edge != (self.current_node, self.target_node):
                self._release_lock(current_sim_time)

            self.current_node = self.target_node
            self.planner.update_start(self.current_node)
            self.planner.compute_shortest_path()
            self.target_node = self.planner.get_next_waypoint()
        else:
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
