"""
Human Pedestrian Model and Shelf-Aware Navigation.
Models dynamic shoppers that strictly respect supermarket shelf boundaries,
navigate through aisles/crossways, and possess continuous Gaussian proxemic fields.
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class Human:
    """Represents a human shopper navigating retail aisles."""
    id: int
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    speed: float = 1.0
    state: str = "browsing"  # "browsing" or "walking"
    state_timer: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    radius: float = 12.0     # Physical body radius (pixels)

    @property
    def pos(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def update(self, dt: float, bounds: Tuple[float, float, float, float],
               shelves: Optional[List[Tuple[float, float, float, float]]] = None,
               aisle_x_coords: Optional[List[float]] = None,
               crossway_y_coords: Optional[List[float]] = None) -> None:
        """
        Updates pedestrian state and ensures pedestrians strictly navigate within open aisles
        and never penetrate solid shelves.
        """
        self.state_timer -= dt
        min_x, min_y, max_x, max_y = bounds

        if self.state_timer <= 0:
            if self.state == "browsing":
                self.state = "walking"
                self.state_timer = random.uniform(3.0, 7.0)
                if aisle_x_coords and crossway_y_coords and random.random() < 0.6:
                    self.target_x = random.choice(aisle_x_coords)
                    self.target_y = random.uniform(crossway_y_coords[0], crossway_y_coords[-1])
                elif aisle_x_coords and crossway_y_coords:
                    self.target_x = random.uniform(aisle_x_coords[0], aisle_x_coords[-1])
                    self.target_y = random.choice(crossway_y_coords)
                else:
                    self.target_x = random.uniform(min_x + 50, max_x - 50)
                    self.target_y = random.uniform(min_y + 50, max_y - 50)
            else:
                self.state = "browsing"
                self.state_timer = random.uniform(2.0, 5.0)
                self.vx = 0.0
                self.vy = 0.0

        if self.state == "walking":
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 6.0:
                self.vx = (dx / dist) * self.speed
                self.vy = (dy / dist) * self.speed
                self.x += self.vx * dt * 30.0
                self.y += self.vy * dt * 30.0
            else:
                self.state = "browsing"
                self.state_timer = random.uniform(2.0, 4.0)

        # 1. Hard Shelf Collision Resolution (Pedestrians cannot walk through shelves)
        if shelves:
            for min_sx, min_sy, max_sx, max_sy in shelves:
                expanded_min_x = min_sx - self.radius
                expanded_max_x = max_sx + self.radius
                expanded_min_y = min_sy - self.radius
                expanded_max_y = max_sy + self.radius

                if (expanded_min_x <= self.x <= expanded_max_x and
                    expanded_min_y <= self.y <= expanded_max_y):
                    d_left = self.x - expanded_min_x
                    d_right = expanded_max_x - self.x
                    d_top = self.y - expanded_min_y
                    d_bottom = expanded_max_y - self.y

                    min_d = min(d_left, d_right, d_top, d_bottom)
                    if min_d == d_left:
                        self.x = expanded_min_x
                        self.vx = -abs(self.vx)
                    elif min_d == d_right:
                        self.x = expanded_max_x
                        self.vx = abs(self.vx)
                    elif min_d == d_top:
                        self.y = expanded_min_y
                        self.vy = -abs(self.vy)
                    else:
                        self.y = expanded_max_y
                        self.vy = abs(self.vy)

        # 2. Store Perimeter Boundary Clamping
        self.x = max(min_x + 15, min(max_x - 15, self.x))
        self.y = max(min_y + 15, min(max_y - 15, self.y))


class ProxemicsField:
    """
    Computes 2D Gaussian personal-space discomfort fields based on HA-VLN 2.0 guidelines.
    Includes continuous line-segment integration along corridor edges.
    """
    def __init__(self, amplitude: float = 400.0, sigma: float = 40.0):
        self.amplitude = amplitude
        self.sigma = sigma

    def compute_penalty_at_point(self, x: float, y: float, humans: List[Human]) -> float:
        total_penalty = 0.0
        two_sigma_sq = 2.0 * (self.sigma ** 2)

        for human in humans:
            d_sq = (x - human.x) ** 2 + (y - human.y) ** 2
            if d_sq < (3.5 * self.sigma) ** 2:
                total_penalty += self.amplitude * math.exp(-d_sq / two_sigma_sq)

        return total_penalty

    def compute_edge_segment_penalty(self, p1: Tuple[float, float], p2: Tuple[float, float],
                                    humans: List[Human], num_samples: int = 6) -> float:
        max_penalty = 0.0
        x1, y1 = p1
        x2, y2 = p2

        for step in range(num_samples + 1):
            tau = step / num_samples
            sx = (1.0 - tau) * x1 + tau * x2
            sy = (1.0 - tau) * y1 + tau * y2
            pt_penalty = self.compute_penalty_at_point(sx, sy, humans)
            if pt_penalty > max_penalty:
                max_penalty = pt_penalty

        return max_penalty
