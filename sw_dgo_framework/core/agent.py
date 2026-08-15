"""
Autonomous Trolley Agent for SW-DGO Framework.
Implements non-holonomic kinematics, dynamic inter-trolley safety clearance envelopes (S_trolley),
anti-tailgating following distances, expanded shelf margin collision solvers, and human proxemics.
"""

from __future__ import annotations
import math
from typing import Dict, List, Tuple, Optional, Any
from .graph import TopologicalGraph
from .dstar_lite import DStarLite
from .mesh_network import MeshNetwork, MessageType, MeshPacket
from .human import Human, ProxemicsField
from .units import (
    ROBOT_RADIUS_PX, SHELF_CLEARANCE_MARGIN_PX, FOLLOWING_DISTANCE_GAP_PX,
    V2V_MESH_COMM_RANGE_PX, ROBOT_VMAX_MPS, ROBOT_WMAX_RADPS, M_TO_PX
)

class TrolleyAgent:
    """
    Autonomous Mobile Shopping Trolley (Int-Cart).
    Executes decentralized SW-DGO routing logic with non-holonomic kinematics,
    active inter-trolley safety clearance envelopes, shelf-margin safety zones, and social yielding.
    """
    def __init__(self, agent_id: int, graph: TopologicalGraph, start_node: str, goal_node: str,
                 mesh_net: MeshNetwork, max_speed: float = 2.6, max_omega: float = ROBOT_WMAX_RADPS,
                 comm_radius: float = V2V_MESH_COMM_RANGE_PX):
        self.agent_id = agent_id
        self.graph = graph.clone()
        self.current_node = start_node
        self.goal_node = goal_node
        self.mesh_net = mesh_net

        # Non-holonomic Kinematics
        node_obj = self.graph.get_node(start_node)
        self.x: float = node_obj.x
        self.y: float = node_obj.y
        self.heading: float = 0.0
        self.speed: float = 0.0
        self.max_speed = max_speed
        self.max_omega = max_omega

        # Safety Envelopes (Physical Body Radius vs Kinetic Clearance Bubble in SI units)
        self.radius: float = ROBOT_RADIUS_PX                    # Physical chassis radius (0.40 m / 13.3 px)
        self.safety_bubble_radius: float = 26.0                 # Kinetic safety clearance envelope (0.78 m)
        self.shelf_margin: float = SHELF_CLEARANCE_MARGIN_PX    # Minimum distance maintained from shelf edges (0.54 m / 18 px)
        self.following_gap: float = FOLLOWING_DISTANCE_GAP_PX   # Anti-tailgating gap (1.08 m / 36 px)

        # High-level planning
        self.planner = DStarLite(self.graph, start_node, goal_node)
        self.planner.compute_shortest_path()
        self.target_node: Optional[str] = self.planner.get_next_waypoint()

        if self.target_node:
            t_obj = self.graph.get_node(self.target_node)
            self.heading = math.atan2(t_obj.y - self.y, t_obj.x - self.x)

        # State machine: "NAVIGATING", "WAITING_LOCK", "YIELDING_HUMAN", "FOLLOWING_CART", "DOCKED"
        self.state: str = "NAVIGATING"
        self.active_lock_edge: Optional[Tuple[str, str]] = None
        self.wait_timer: float = 0.0
        self.yield_timer: float = 0.0
        self.peer_block_timer: float = 0.0

        # Performance Metrics
        self.total_distance: float = 0.0
        self.travel_time: float = 0.0
        self.replan_count: int = 0
        self.deadlock_count: int = 0
        self.proxemic_violations: int = 0
        self.is_docked: bool = False

        self.mesh_net.register_agent(self.agent_id, self)

    @property
    def current_pos(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def process_inbound_mesh(self) -> bool:
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
        cost_changed = False
        for (u, v), edge in self.graph.edges.items():
            nu = self.graph.get_node(u)
            nv = self.graph.get_node(v)
            d_u = math.hypot(self.x - nu.x, self.y - nu.y)
            d_v = math.hypot(self.x - nv.x, self.y - nv.y)
            d_near = d_u if d_u < d_v else d_v
            if d_near <= 240.0:
                seg_penalty = prox_field.compute_edge_segment_penalty((nu.x, nu.y), (nv.x, nv.y), humans)
                if abs(edge.h_prox - seg_penalty) > 5.0:
                    edge.h_prox = seg_penalty
                    self.planner.notify_edge_cost_change(u, v)
                    cost_changed = True
        return cost_changed

    def resolve_shelf_collisions(self, shelves: Optional[List[Tuple[float, float, float, float]]]) -> None:
        """
        Hard collision & clearance buffer clamping against rectangular shelves.
        Enforces shelf_margin so trolley corners never scrape or slam into shelf walls.
        """
        if not shelves:
            return

        for min_sx, min_sy, max_sx, max_sy in shelves:
            expanded_min_x = min_sx - self.shelf_margin
            expanded_max_x = max_sx + self.shelf_margin
            expanded_min_y = min_sy - self.shelf_margin
            expanded_max_y = max_sy + self.shelf_margin

            if (expanded_min_x <= self.x <= expanded_max_x and
                expanded_min_y <= self.y <= expanded_max_y):
                d_left = self.x - expanded_min_x
                d_right = expanded_max_x - self.x
                d_top = self.y - expanded_min_y
                d_bottom = expanded_max_y - self.y

                min_d = min(d_left, d_right, d_top, d_bottom)
                if min_d == d_left:
                    self.x = expanded_min_x
                elif min_d == d_right:
                    self.x = expanded_max_x
                elif min_d == d_top:
                    self.y = expanded_min_y
                else:
                    self.y = expanded_max_y

    def check_inter_trolley_safety(self, peer_agents: Optional[List[TrolleyAgent]], dt: float) -> bool:
        """
        Inter-trolley safety clearance (S_trolley):
        - Prevents tailgating and inter-agent crowding.
        - Maintains smooth kinetic spacing without freezing.
        """
        if not peer_agents:
            return False

        must_slow_down = False
        for other in peer_agents:
            if other.agent_id == self.agent_id or other.is_docked:
                continue

            dist = math.hypot(self.x - other.x, self.y - other.y)

            # 1. Elastic Contact Repulsion (Ensure carts never overlap)
            if dist < 22.0 and dist > 0.1:
                push_dist = 22.0 - dist
                self.x -= ((other.x - self.x) / dist) * (push_dist * 0.4)
                self.y -= ((other.y - self.y) / dist) * (push_dist * 0.4)

            # 2. Anti-Tailgating Following Distance
            if dist < 36.0:
                dx = other.x - self.x
                dy = other.y - self.y
                dot = math.cos(self.heading) * dx + math.sin(self.heading) * dy
                if dot > 5.0:  # Lead cart is ahead in the forward vision cone
                    must_slow_down = True

        if must_slow_down:
            self.state = "FOLLOWING_CART"
            self.peer_block_timer += dt
            # Modulate speed to match safe following crawl rather than full dead stop
            self.speed = min(self.speed, 0.8)

            # If blocked behind a stalled cart for > 1.8s, trigger dynamic D* Lite reroute
            if self.peer_block_timer > 1.8 and self.target_node:
                self.graph.update_mesh_penalty(self.current_node, self.target_node, 300.0)
                self.planner.notify_edge_cost_change(self.current_node, self.target_node)
                self.planner.compute_shortest_path()
                self.target_node = self.planner.get_next_waypoint()
                self.peer_block_timer = 0.0
            return False  # Still allow forward crawl step

        self.peer_block_timer = 0.0
        return False

    def check_human_collision_and_yield(self, humans: List[Human], dt: float,
                                        current_sim_time: float) -> bool:
        yield_required = False
        for human in humans:
            dist = math.hypot(self.x - human.x, self.y - human.y)
            if dist < 26.0:
                self.proxemic_violations += 1
                if dist > 0.1:
                    push_dist = 26.0 - dist
                    self.x -= ((human.x - self.x) / dist) * (push_dist * 0.5)
                    self.y -= ((human.y - self.y) / dist) * (push_dist * 0.5)

            if dist < 38.0:
                dx = human.x - self.x
                dy = human.y - self.y
                dot = math.cos(self.heading) * dx + math.sin(self.heading) * dy
                if dot > 0.0:
                    yield_required = True

        if yield_required:
            self.state = "YIELDING_HUMAN"
            self.yield_timer += dt
            self.speed = 0.0

            if self.yield_timer > 0.8 and self.target_node:
                self.broadcast_congestion(self.current_node, self.target_node, penalty=500.0,
                                         current_time=current_sim_time)
                self.planner.compute_shortest_path()
                self.target_node = self.planner.get_next_waypoint()
                self.yield_timer = 0.0
            return True

        self.yield_timer = 0.0
        return False

    def step(self, dt: float, humans: List[Human], prox_field: ProxemicsField,
             current_sim_time: float = 0.0,
             shelves: Optional[List[Tuple[float, float, float, float]]] = None,
             peer_agents: Optional[List[TrolleyAgent]] = None) -> None:
        """Main non-holonomic kinematic D2RO execution tick."""
        if self.is_docked:
            return

        self.travel_time += dt

        # 1. Process V2V Mesh & Proxemics
        mesh_changed = self.process_inbound_mesh()
        prox_changed = self.update_human_proxemics(humans, prox_field)

        # 2. Incremental Replan
        if mesh_changed or prox_changed:
            self.planner.compute_shortest_path()
            self.replan_count += 1
            self.target_node = self.planner.get_next_waypoint()

        # 3. Check Docking Arrival (Multi-cart return bay queue)
        goal_obj = self.graph.get_node(self.goal_node)
        if self.current_node == self.goal_node or math.hypot(self.x - goal_obj.x, self.y - goal_obj.y) < 28.0:
            self.is_docked = True
            self.state = "DOCKED"
            if self.active_lock_edge:
                self._release_lock(current_sim_time)
            return

        # 4. Check Human Yielding
        if self.check_human_collision_and_yield(humans, dt, current_sim_time):
            self.resolve_shelf_collisions(shelves)
            return

        # 5. Check Inter-Trolley Kinetic Safety Clearance (Anti-Tailgating)
        self.check_inter_trolley_safety(peer_agents, dt)

        # 6. Waypoint & Corridor Lock Verification
        if self.target_node is None:
            self.planner.compute_shortest_path()
            self.target_node = self.planner.get_next_waypoint()
            if self.target_node is None:
                self.deadlock_count += 1
                return

        edge = self.graph.get_edge(self.current_node, self.target_node)
        if edge and edge.is_single_file:
            opp_edge = self.graph.get_edge(self.target_node, self.current_node)
            if opp_edge and opp_edge.lock_owner is not None and opp_edge.lock_owner != self.agent_id:
                self.state = "WAITING_LOCK"
                self.wait_timer += dt
                self.speed = 0.0
                if self.wait_timer > 1.8:
                    edge.r_lock = math.inf
                    self.planner.notify_edge_cost_change(self.current_node, self.target_node)
                    self.planner.compute_shortest_path()
                    self.target_node = self.planner.get_next_waypoint()
                    self.wait_timer = 0.0
                self.resolve_shelf_collisions(shelves)
                return
            else:
                if self.active_lock_edge != (self.current_node, self.target_node):
                    self._acquire_lock(self.current_node, self.target_node, current_sim_time)

        if self.state != "FOLLOWING_CART":
            self.state = "NAVIGATING"
        self.wait_timer = 0.0

        # 7. Non-Holonomic Kinematics (Bounded Steering Angle & Differential Turning)
        target_obj = self.graph.get_node(self.target_node)
        dx = target_obj.x - self.x
        dy = target_obj.y - self.y
        dist = math.hypot(dx, dy)

        if dist < 8.0:  # Waypoint arrived
            if self.active_lock_edge and self.active_lock_edge != (self.current_node, self.target_node):
                self._release_lock(current_sim_time)

            self.current_node = self.target_node
            if self.current_node == self.goal_node:
                self.is_docked = True
                self.state = "DOCKED"
                return

            self.planner.update_start(self.current_node)
            self.planner.compute_shortest_path()
            self.target_node = self.planner.get_next_waypoint()
        else:
            desired_heading = math.atan2(dy, dx)
            angle_diff = (desired_heading - self.heading + math.pi) % (2 * math.pi) - math.pi

            max_turn = self.max_omega * dt
            turn_step = max(-max_turn, min(max_turn, angle_diff))
            self.heading += turn_step

            # Unicycle forward motion with corner deceleration
            alignment = max(0.25, math.cos(angle_diff))
            target_speed = (self.speed if self.state == "FOLLOWING_CART" else self.max_speed) * alignment
            self.speed = min(dist / (dt * 30.0), target_speed)

            step_dist = self.speed * dt * 30.0
            self.x += math.cos(self.heading) * step_dist
            self.y += math.sin(self.heading) * step_dist
            self.total_distance += step_dist

        # 8. Clamp against solid shelf walls with safety margin
        self.resolve_shelf_collisions(shelves)

    def broadcast_congestion(self, u: str, v: str, penalty: float, current_time: float) -> None:
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
