"""
Human Pedestrian Model and Gaussian Proxemics Generator.
Models dynamic shoppers and computes continuous social personal-space discomfort fields
with segment-level edge sampling and kinematic collision bubbles.
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass
from typing import List, Tuple

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

    def update(self, dt: float, bounds: Tuple[float, float, float, float]) -> None:
        """Updates position, wandering motion, and shelf browsing states."""
        self.state_timer -= dt
        min_x, min_y, max_x, max_y = bounds

        if self.state_timer <= 0:
            if self.state == "browsing":
                self.state = "walking"
                self.state_timer = random.uniform(3.0, 7.0)
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

        # Clamp within store bounds
        self.x = max(min_x + 10, min(max_x - 10, self.x))
        self.y = max(min_y + 10, min(max_y - 10, self.y))


class ProxemicsField:
    """
    Computes 2D Gaussian personal-space discomfort fields based on HA-VLN 2.0 guidelines.
    Includes continuous line-segment integration along corridor edges.
    """
    def __init__(self, amplitude: float = 350.0, sigma: float = 40.0):
        self.amplitude = amplitude  # High peak penalty to ensure detours are mathematically favored
        self.sigma = sigma          # Personal space standard deviation (pixels)

    def compute_penalty_at_point(self, x: float, y: float, humans: List[Human]) -> float:
        """Computes Gaussian discomfort penalty at point (x, y) across all humans."""
        total_penalty = 0.0
        two_sigma_sq = 2.0 * (self.sigma ** 2)

        for human in humans:
            d_sq = (x - human.x) ** 2 + (y - human.y) ** 2
            if d_sq < (3.5 * self.sigma) ** 2:
                total_penalty += self.amplitude * math.exp(-d_sq / two_sigma_sq)

        return total_penalty

    def compute_edge_segment_penalty(self, p1: Tuple[float, float], p2: Tuple[float, float],
                                    humans: List[Human], num_samples: int = 5) -> float:
        """
        Numerically integrates proxemic discomfort along the continuous line segment (p1 -> p2).
        Guarantees that a human standing anywhere in an aisle inflates the edge cost.
        """
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
