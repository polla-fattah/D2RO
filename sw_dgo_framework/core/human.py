"""
Human Pedestrian Model and Shelf-Aware Navigation with True Anisotropic Gaussian Proxemics.
Models dynamic shoppers that strictly respect supermarket shelf boundaries,
navigate through aisles/crossways, and possess directional asymmetric Gaussian personal-space fields.
"""

from __future__ import annotations
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional
from math import exp, hypot, cos, sin, atan2, pi, sqrt

from sw_dgo_framework.core.units import (
    PX_TO_M, M_TO_PX, HUMAN_RADIUS_PX,
    PROXEMIC_SIGMA_FRONT_PX, PROXEMIC_SIGMA_SIDE_PX, PROXEMIC_SIGMA_REAR_PX, PROXEMIC_AMPLITUDE
)

@dataclass
class Human:
    """Represents a human shopper navigating retail aisles with directional orientation."""
    id: int
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    heading: float = 0.0     # Facing orientation in radians
    speed: float = 1.0
    state: str = "browsing"  # "browsing" or "walking"
    state_timer: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    radius: float = HUMAN_RADIUS_PX  # Physical body radius in pixels (0.36 m)

    @property
    def pos(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def update(self, dt: float, bounds: Tuple[float, float, float, float],
               shelves: Optional[List[Tuple[float, float, float, float]]] = None,
               aisle_x_coords: Optional[List[float]] = None,
               crossway_y_coords: Optional[List[float]] = None) -> None:
        """
        Updates pedestrian state, kinematics, and facing heading while ensuring pedestrians
        strictly navigate within open corridors and never penetrate solid shelf fixtures.
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
                # When browsing, turn toward nearest shelf to face products
                if shelves:
                    min_dist = float('inf')
                    for sx1, sy1, sx2, sy2 in shelves:
                        cx = (sx1 + sx2) / 2.0
                        cy = (sy1 + sy2) / 2.0
                        d = hypot(self.x - cx, self.y - cy)
                        if d < min_dist:
                            min_dist = d
                            self.heading = atan2(cy - self.y, cx - self.x)

        if self.state == "walking":
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = hypot(dx, dy)
            if dist > 6.0:
                self.vx = (dx / dist) * self.speed
                self.vy = (dy / dist) * self.speed
                self.heading = atan2(self.vy, self.vx)
                self.x += self.vx * dt * 30.0
                self.y += self.vy * dt * 30.0
            else:
                self.state = "browsing"
                self.state_timer = random.uniform(2.0, 4.0)

        # 1. Hard Shelf Collision Resolution (Pedestrians cannot penetrate solid shelves)
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

                    # Find minimum distance to push out
                    min_d = d_left
                    if d_right < min_d: min_d = d_right
                    if d_top < min_d: min_d = d_top
                    if d_bottom < min_d: min_d = d_bottom

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
        if self.x < min_x + 15.0:
            self.x = min_x + 15.0
        elif self.x > max_x - 15.0:
            self.x = max_x - 15.0

        if self.y < min_y + 15.0:
            self.y = min_y + 15.0
        elif self.y > max_y - 15.0:
            self.y = max_y - 15.0


class ProxemicsField:
    """
    Computes true Asymmetric Anisotropic 2D Gaussian personal-space discomfort fields
    based on Hall's Proxemics and HA-VLN 2.0 guidelines.
    
    Front personal space: sigma_front = 1.35 m (45 px)
    Lateral personal space: sigma_side = 0.90 m (30 px)
    Rear personal space: sigma_rear = 0.60 m (20 px)
    """
    def __init__(self, amplitude: float = PROXEMIC_AMPLITUDE,
                 sigma_front: float = PROXEMIC_SIGMA_FRONT_PX,
                 sigma_side: float = PROXEMIC_SIGMA_SIDE_PX,
                 sigma_rear: float = PROXEMIC_SIGMA_REAR_PX):
        self.amplitude = amplitude
        self.sigma_front = sigma_front
        self.sigma_side = sigma_side
        self.sigma_rear = sigma_rear

    def compute_penalty_at_point(self, x: float, y: float, humans: List[Human]) -> float:
        """
        Evaluates the asymmetric anisotropic 2D Gaussian discomfort at coordinate (x, y)
        transformed into each pedestrian's local body orientation frame.
        """
        total_penalty = 0.0
        if humans is None:
            return 0.0
        if not hasattr(humans, '__iter__') or isinstance(humans, (str, bytes)):
            humans = [humans]

        for human in humans:
            if not isinstance(human, Human):
                continue
            dx = x - human.x
            dy = y - human.y
            raw_dist_sq = dx * dx + dy * dy

            # Bounding box cutoff check at 3.5 * sigma_front (~4.7 meters)
            max_cutoff = 3.5 * self.sigma_front
            if raw_dist_sq > max_cutoff * max_cutoff:
                continue

            # Transform into human's local body frame via 2D rotation matrix R(theta_h)
            h_ang = human.heading
            cos_h = cos(h_ang)
            sin_h = sin(h_ang)
            x_local = dx * cos_h + dy * sin_h   # Longitudinal axis (+front / -rear)
            y_local = -dx * sin_h + dy * cos_h  # Lateral axis (+left / -right)

            # Asymmetric longitudinal variance
            sigma_x = self.sigma_front if x_local >= 0.0 else self.sigma_rear
            sigma_y = self.sigma_side

            exponent = -0.5 * ((x_local / sigma_x) ** 2 + (y_local / sigma_y) ** 2)
            if exponent > -18.0:  # Numerical underflow guard
                total_penalty += self.amplitude * exp(exponent)

        return total_penalty

    def compute_edge_segment_penalty(self, p1: Tuple[float, float], p2: Tuple[float, float],
                                     humans: List[Human], num_samples: int = 6) -> float:
        """
        Integrates the continuous 2D anisotropic Gaussian discomfort field along corridor segment (p1 -> p2).
        Returns the peak discomfort sampled along the segment.
        """
        max_penalty = 0.0
        x1, y1 = p1[0], p1[1]
        x2, y2 = p2[0], p2[1]
        n_samp = int(num_samples)

        for step_idx in range(n_samp + 1):
            tau = step_idx / n_samp
            sx = (1.0 - tau) * x1 + tau * x2
            sy = (1.0 - tau) * y1 + tau * y2
            pt_penalty = self.compute_penalty_at_point(sx, sy, humans)
            if pt_penalty > max_penalty:
                max_penalty = pt_penalty

        return max_penalty
