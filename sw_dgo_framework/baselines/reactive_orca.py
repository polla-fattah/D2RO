"""
Baseline 2: Purely Reactive Potential Field / Local Avoidance Agent.
Models the legacy reactive steering approach without global topological graph awareness.
Prone to corridor live-locks and concave obstacle traps.
"""

from __future__ import annotations
import math
from typing import List, Tuple, Optional
from ..core.human import Human, ProxemicsField

class ReactiveLocalAgent:
    """
    Reactive agent using local potential field / Reynolds separation forces.
    Demonstrates the live-lock and concave obstacle failure modes.
    """
    def __init__(self, agent_id: int, start_pos: Tuple[float, float], goal_pos: Tuple[float, float],
                 max_speed: float = 3.0):
        self.agent_id = agent_id
        self.x, self.y = start_pos
        self.goal_x, self.goal_y = goal_pos
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.max_speed = max_speed
        self.heading: float = 0.0

        # Metrics
        self.total_distance: float = 0.0
        self.travel_time: float = 0.0
        self.deadlock_count: int = 0
        self.proxemic_violations: int = 0
        self.is_docked: bool = False

    @property
    def current_pos(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def step(self, dt: float, peer_positions: List[Tuple[float, float]],
             humans: List[Human], shelf_bounds: List[Tuple[float, float, float, float]]) -> None:
        if self.is_docked:
            return

        self.travel_time += dt

        # 1. Goal attraction force
        dx = self.goal_x - self.x
        dy = self.goal_y - self.y
        dist_to_goal = math.hypot(dx, dy)

        if dist_to_goal < 10.0:
            self.is_docked = True
            return

        fx = (dx / dist_to_goal) * self.max_speed
        fy = (dy / dist_to_goal) * self.max_speed

        # 2. Peer repulsion force (Reynolds separation)
        for px, py in peer_positions:
            p_dist = math.hypot(self.x - px, self.y - py)
            if 0.0 < p_dist < 40.0:
                rep_force = (40.0 - p_dist) / 40.0
                fx -= ((px - self.x) / p_dist) * rep_force * 4.0
                fy -= ((py - self.y) / p_dist) * rep_force * 4.0

        # 3. Shelf obstacle repulsion
        for min_x, min_y, max_x, max_y in shelf_bounds:
            # Check if close to bounding box
            cx = max(min_x, min(max_x, self.x))
            cy = max(min_y, min(max_y, self.y))
            obs_dist = math.hypot(self.x - cx, self.y - cy)
            if 0.0 < obs_dist < 25.0:
                rep_force = (25.0 - obs_dist) / 25.0
                fx -= ((cx - self.x) / obs_dist) * rep_force * 5.0
                fy -= ((cy - self.y) / obs_dist) * rep_force * 5.0

        # Check proximity violations with humans
        for human in humans:
            if math.hypot(self.x - human.x, self.y - human.y) < 25.0:
                self.proxemic_violations += 1
                break

        # Kinematic update
        speed = math.hypot(fx, fy)
        if speed > self.max_speed:
            fx = (fx / speed) * self.max_speed
            fy = (fy / speed) * self.max_speed

        self.vx = fx
        self.vy = fy
        step_len = math.hypot(self.vx * dt * 30.0, self.vy * dt * 30.0)

        # Detect oscillation / deadlock (trapped with low net velocity despite distance from goal)
        if speed < 0.2 and dist_to_goal > 30.0:
            self.deadlock_count += 1

        self.x += self.vx * dt * 30.0
        self.y += self.vy * dt * 30.0
        self.total_distance += step_len
