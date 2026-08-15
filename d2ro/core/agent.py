"""
Autonomous Trolley Agent for SW-DGO Framework.
Implements non-holonomic kinematics, dynamic inter-trolley safety clearance envelopes (S_trolley),
anti-tailgating following distances, expanded shelf margin collision solvers, and human proxemics.
"""

from __future__ import annotations
import math
import time
from typing import Dict, List, Tuple, Optional, Any
from .graph import TopologicalGraph
from .dstar_lite import DStarLite
from .mesh_network import MeshNetwork, MessageType, MeshPacket
from .human import Human, ProxemicsField
from .units import (
    ROBOT_RADIUS_PX, SHELF_CLEARANCE_MARGIN_PX, FOLLOWING_DISTANCE_GAP_PX,
    V2V_MESH_COMM_RANGE_PX, ROBOT_VMAX_MPS, ROBOT_VMAX_PXPS, ROBOT_WMAX_RADPS, M_TO_PX
)

class TrolleyAgent:
    """
    Autonomous Mobile Shopping Trolley (Int-Cart).
    Executes decentralized SW-DGO routing logic with non-holonomic kinematics,
    active inter-trolley safety clearance envelopes, shelf-margin safety zones, and social yielding.
    """
    def __init__(self, agent_id: int, graph: TopologicalGraph, start_node: str, goal_node: str,
                 mesh_net: MeshNetwork, max_speed: float = ROBOT_VMAX_PXPS, max_omega: float = ROBOT_WMAX_RADPS,
                 comm_radius: float = V2V_MESH_COMM_RANGE_PX,
                 enable_mesh: bool = True, enable_lock: bool = True,
                 enable_prox: bool = True, enable_safety: bool = True):
        self.agent_id = agent_id
        self.graph = graph.clone()
        self.current_node = start_node
        self.goal_node = goal_node
        self.mesh_net = mesh_net

        # Ablation / Feature Flags
        self.enable_mesh = enable_mesh
        self.enable_lock = enable_lock
        self.enable_prox = enable_prox
        self.enable_safety = enable_safety

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
        self.safety_bubble_radius: float = 26.0 if enable_safety else 0.0 # Kinetic safety clearance envelope (0.78 m)
        self.shelf_margin: float = SHELF_CLEARANCE_MARGIN_PX if enable_safety else 0.0 # Minimum distance maintained from shelf edges (0.54 m / 18 px)
        self.following_gap: float = FOLLOWING_DISTANCE_GAP_PX if enable_safety else 0.0 # Anti-tailgating gap (1.08 m / 36 px)

        # Latency tracking
        self.last_compute_time_ms: float = 0.15

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
        self.shelf_corner_scrapes: int = 0
        self.is_docked: bool = False
        self.last_compute_time_ms: float = 0.0

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

    def update_human_proxemics(self, humans: Any, prox_field: ProxemicsField) -> bool:
        cost_changed = False
        if humans is None or not hasattr(self.graph, "edges"):
            return False

        if not hasattr(self, "_prox_update_counter"):
            self._prox_update_counter = 0
        self._prox_update_counter += 1
        if self._prox_update_counter % 3 != 0:
            return False
        if isinstance(humans, list):
            human_list = humans
        elif isinstance(humans, (tuple, set)):
            human_list = list(humans)
        else:
            human_list = [humans]

        if not isinstance(self.graph.edges, dict):
            return False

        for key, edge in list(self.graph.edges.items()):
            if not (isinstance(key, tuple) and len(key) == 2):
                continue
            u, v = key
            nu = self.graph.get_node(u)
            nv = self.graph.get_node(v)
            if nu is None or nv is None:
                continue
            d_u = math.hypot(self.x - nu.x, self.y - nu.y)
            d_v = math.hypot(self.x - nv.x, self.y - nv.y)
            d_near = d_u if d_u < d_v else d_v
            if d_near <= 200.0:
                mx = (nu.x + nv.x) * 0.5
                my = (nu.y + nv.y) * 0.5
                edge_len = math.hypot(nu.x - nv.x, nu.y - nv.y)
                cutoff = edge_len * 0.5 + 90.0
                has_nearby = False
                for h in human_list:
                    if hasattr(h, "x") and math.hypot(h.x - mx, h.y - my) <= cutoff:
                        has_nearby = True
                        break

                if has_nearby:
                    seg_penalty = prox_field.compute_edge_segment_penalty((nu.x, nu.y), (nv.x, nv.y), human_list)
                else:
                    seg_penalty = 0.0

                if math.fabs(edge.h_prox - seg_penalty) > 5.0:
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

        for sx1, sy1, sx2, sy2 in shelves:
            min_x = sx1 - self.shelf_margin
            max_x = sx2 + self.shelf_margin
            min_y = sy1 - self.shelf_margin
            max_y = sy2 + self.shelf_margin

            if min_x <= self.x <= max_x and min_y <= self.y <= max_y:
                self.shelf_corner_scrapes += 1
                dx_left = self.x - min_x
                dx_right = max_x - self.x
                dy_bottom = self.y - min_y
                dy_top = max_y - self.y

                min_escape = min(dx_left, dx_right, dy_bottom, dy_top)
                if min_escape == dx_left:
                    self.x = min_x - 1.0
                elif min_escape == dx_right:
                    self.x = max_x + 1.0
                elif min_escape == dy_bottom:
                    self.y = min_y - 1.0
                else:
                    self.y = max_y + 1.0

    def check_inter_trolley_safety(self, peer_agents: Optional[List[TrolleyAgent]], dt: float) -> bool:
        """
        Inter-trolley safety clearance (S_trolley):
        - Prevents tailgating and inter-agent crowding.
        - Maintains smooth kinetic spacing without freezing.
        """
        if not peer_agents or not self.enable_safety:
            return False

        must_slow_down = False
        for other in peer_agents:
            if other.agent_id == self.agent_id or other.is_docked:
                continue

            dist = math.hypot(self.x - other.x, self.y - other.y)

            # 1. Kinetic Safety Bubble Clearance (Chassis Separation Bubble)
            min_sep = self.safety_bubble_radius * 2.0  # 52 px (1.56 m)
            if dist < min_sep and dist > 0.1:
                overlap = (min_sep - dist) * 0.5
                repulse_x = ((self.x - other.x) / dist) * overlap
                repulse_y = ((self.y - other.y) / dist) * overlap
                # Right-hand passing bias in wide corridors
                lat_x = -(other.y - self.y) / dist * 0.8
                lat_y = (other.x - self.x) / dist * 0.8
                self.x += repulse_x + lat_x
                self.y += repulse_y + lat_y

            # 2. Anti-Tailgating Following Distance Gap
            if dist < self.following_gap and dist > 0.1:
                dx = other.x - self.x
                dy = other.y - self.y
                forward_x = math.cos(self.heading)
                forward_y = math.sin(self.heading)
                dot = forward_x * dx + forward_y * dy
                if dot > 0.0:  # Other cart is directly in front along heading vector
                    must_slow_down = True

        if must_slow_down:
            self.state = "FOLLOWING_CART"
            self.peer_block_timer += dt
            # Modulate speed to match safe following crawl (0.8 m/s ~ 26.67 px/s)
            self.speed = min(self.speed, 0.8 * M_TO_PX)

            # If blocked behind a stalled cart for > 1.8s, increment deadlock and trigger dynamic D* Lite reroute if mesh enabled
            if self.peer_block_timer > 1.8 and self.target_node:
                self.deadlock_count += 1
                if self.enable_mesh:
                    self.graph.update_mesh_penalty(self.current_node, self.target_node, 300.0)
                    self.planner.notify_edge_cost_change(self.current_node, self.target_node)
                    self.planner.compute_shortest_path()
                    self.target_node = self.planner.get_next_waypoint()
                self.peer_block_timer = 0.0
            return False  # Still allow forward crawl step

        self.peer_block_timer = 0.0
        if self.state == "FOLLOWING_CART":
            self.state = "NAVIGATING"
        return False

    def check_human_collision_and_yield(self, humans: Any, dt: float,
                                        current_sim_time: float) -> bool:
        if humans is None:
            self.yield_timer = 0.0
            return False
        if isinstance(humans, list):
            human_list = humans
        elif isinstance(humans, (tuple, set)):
            human_list = list(humans)
        else:
            human_list = [humans]

        yield_required = False
        for human in human_list:
            if not hasattr(human, "x"):
                continue
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

        t0 = time.perf_counter()
        self.travel_time += dt

        # 1. Process V2V Mesh & Proxemics
        mesh_changed = self.process_inbound_mesh() if self.enable_mesh else False
        prox_changed = self.update_human_proxemics(humans, prox_field) if self.enable_prox else False

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
            if self.active_lock_edge and self.enable_lock:
                self._release_lock(current_sim_time)
            self.last_compute_time_ms = (time.perf_counter() - t0) * 1000.0
            return

        # 4. Check Human Yielding
        if self.check_human_collision_and_yield(humans, dt, current_sim_time):
            self.resolve_shelf_collisions(shelves)
            self.last_compute_time_ms = (time.perf_counter() - t0) * 1000.0
            return

        # 5. Check Inter-Trolley Kinetic Safety Clearance (Anti-Tailgating)
        if self.enable_safety:
            self.check_inter_trolley_safety(peer_agents, dt)

        # 6. Waypoint & Corridor Lock Verification
        if self.target_node is None:
            self.planner.compute_shortest_path()
            self.target_node = self.planner.get_next_waypoint()
            if self.target_node is None:
                self.deadlock_count += 1
                self.last_compute_time_ms = (time.perf_counter() - t0) * 1000.0
                return

        edge = self.graph.get_edge(self.current_node, self.target_node)
        if self.enable_lock and edge and edge.is_single_file:
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
                self.last_compute_time_ms = (time.perf_counter() - t0) * 1000.0
                return
            else:
                if self.active_lock_edge != (self.current_node, self.target_node):
                    self._acquire_lock(self.current_node, self.target_node, current_sim_time)
        elif not self.enable_lock and edge and edge.is_single_file:
            # When locks are ablated, opposing agents may both enter single-file aisle
            if peer_agents:
                for peer in peer_agents:
                    if peer.agent_id != self.agent_id and not peer.is_docked:
                        d_peer = math.hypot(self.x - peer.x, self.y - peer.y)
                        if d_peer < 25.0:  # Head-on conflict in single file
                            self.deadlock_count += 1
                            self.speed = 0.0

        if self.state != "FOLLOWING_CART":
            self.state = "NAVIGATING"
        self.wait_timer = 0.0

        # Track shelf scrapes if safety envelopes are ablated
        if not self.enable_safety and shelves:
            for min_sx, min_sy, max_sx, max_sy in shelves:
                cx = max(min_sx, min(max_sx, self.x))
                cy = max(min_sy, min(max_sy, self.y))
                if math.hypot(self.x - cx, self.y - cy) < 14.0:
                    self.shelf_corner_scrapes += 1

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
            self.speed = min(dist / dt, target_speed)

            step_dist = self.speed * dt
            self.x += math.cos(self.heading) * step_dist
            self.y += math.sin(self.heading) * step_dist
            self.total_distance += step_dist

        # 8. Clamp against solid shelf walls with safety margin
        self.resolve_shelf_collisions(shelves)
        self.last_compute_time_ms = (time.perf_counter() - t0) * 1000.0

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
