"""
Headless Benchmark Runner for D²RO / SW-DGO Framework.
Runs Monte Carlo batch trials comparing D²RO against Static A* and Pure Reactive Avoidance.
Outputs quantitative tables and logs metrics for paper publication.
"""

from __future__ import annotations
import math
import random
import time
from dataclasses import dataclass
from typing import List, Dict, Tuple
from ..environments.supermarket import SupermarketLayout
from ..core.mesh_network import MeshNetwork
from ..core.agent import TrolleyAgent
from ..core.human import Human, ProxemicsField
from ..baselines.static_astar import StaticAStarAgent
from ..baselines.reactive_orca import ReactiveLocalAgent

@dataclass
class TrialResult:
    method: str
    trial_id: int
    completion_time: float
    all_docked: bool
    deadlocks_count: int
    proxemic_violations: int
    total_packets: int
    total_replans: int

class BenchmarkHarness:
    """
    Runs multi-trial batch simulations under identical crowd and obstacle conditions.
    """
    def __init__(self, num_trolleys: int = 4, num_humans: int = 8,
                 max_sim_time: float = 60.0, dt: float = 0.1):
        self.num_trolleys = num_trolleys
        self.num_humans = num_humans
        self.max_sim_time = max_sim_time
        self.dt = dt
        self.prox_field = ProxemicsField(amplitude=40.0, sigma=35.0)

    def _generate_humans(self, layout: SupermarketLayout, seed: int) -> List[Human]:
        random.seed(seed)
        humans = []
        min_x, min_y, max_x, max_y = layout.bounds
        for i in range(self.num_humans):
            h = Human(
                id=i,
                x=random.uniform(min_x + 60, max_x - 60),
                y=random.uniform(min_y + 60, max_y - 60),
                speed=random.uniform(0.8, 1.4)
            )
            humans.append(h)
        return humans

    def run_d2ro_trial(self, trial_id: int, seed: int) -> TrialResult:
        layout = SupermarketLayout(num_aisles=5)
        mesh = MeshNetwork(comm_radius=300.0)
        humans = self._generate_humans(layout, seed)

        # Spawn trolleys at different top/middle aisle positions
        agents: List[TrolleyAgent] = []
        start_nodes = [f"N_top_{i % 5}" for i in range(self.num_trolleys)]
        for i in range(self.num_trolleys):
            agent = TrolleyAgent(
                agent_id=i + 1,
                graph=layout.graph,
                start_node=start_nodes[i],
                goal_node="DOCK_BAY",
                mesh_net=mesh
            )
            agents.append(agent)

        sim_time = 0.0
        while sim_time < self.max_sim_time:
            all_docked = all(a.is_docked for a in agents)
            if all_docked:
                break

            # Update dynamic humans
            for h in humans:
                h.update(self.dt, layout.bounds)

            # Step agents
            for a in agents:
                a.step(self.dt, humans, self.prox_field, sim_time)

            # Natural decay of mesh penalties
            layout.graph.decay_mesh_penalties(self.dt, decay_rate=2.0)
            sim_time += self.dt

        total_deadlocks = sum(a.deadlock_count for a in agents)
        total_violations = sum(a.proxemic_violations for a in agents)
        total_replans = sum(a.replan_count for a in agents)
        max_t = max(a.travel_time for a in agents)
        all_docked = all(a.is_docked for a in agents)

        return TrialResult(
            method="D2RO (SW-DGO)",
            trial_id=trial_id,
            completion_time=max_t,
            all_docked=all_docked,
            deadlocks_count=total_deadlocks,
            proxemic_violations=total_violations,
            total_packets=mesh.total_packets_transmitted,
            total_replans=total_replans
        )

    def run_static_astar_trial(self, trial_id: int, seed: int) -> TrialResult:
        layout = SupermarketLayout(num_aisles=5)
        humans = self._generate_humans(layout, seed)

        agents: List[StaticAStarAgent] = []
        start_nodes = [f"N_top_{i % 5}" for i in range(self.num_trolleys)]
        for i in range(self.num_trolleys):
            agent = StaticAStarAgent(
                agent_id=i + 1,
                graph=layout.graph,
                start_node=start_nodes[i],
                goal_node="DOCK_BAY"
            )
            agents.append(agent)

        sim_time = 0.0
        while sim_time < self.max_sim_time:
            if all(a.is_docked for a in agents):
                break

            for h in humans:
                h.update(self.dt, layout.bounds)

            for a in agents:
                a.step(self.dt, humans, self.prox_field, sim_time)

            sim_time += self.dt

        total_violations = sum(a.proxemic_violations for a in agents)
        max_t = max(a.travel_time for a in agents)
        all_docked = all(a.is_docked for a in agents)

        return TrialResult(
            method="Static A*",
            trial_id=trial_id,
            completion_time=max_t,
            all_docked=all_docked,
            deadlocks_count=0,
            proxemic_violations=total_violations,
            total_packets=0,
            total_replans=0
        )

    def run_reactive_trial(self, trial_id: int, seed: int) -> TrialResult:
        layout = SupermarketLayout(num_aisles=5)
        humans = self._generate_humans(layout, seed)
        dock_pos = layout.graph.get_node("DOCK_BAY").pos
        shelf_boxes = [s.bounds for s in layout.shelves]

        agents: List[ReactiveLocalAgent] = []
        for i in range(self.num_trolleys):
            start_pos = layout.graph.get_node(f"N_top_{i % 5}").pos
            agent = ReactiveLocalAgent(
                agent_id=i + 1,
                start_pos=start_pos,
                goal_pos=dock_pos
            )
            agents.append(agent)

        sim_time = 0.0
        while sim_time < self.max_sim_time:
            if all(a.is_docked for a in agents):
                break

            for h in humans:
                h.update(self.dt, layout.bounds)

            peer_positions = [a.current_pos for a in agents]
            for a in agents:
                a.step(self.dt, peer_positions, humans, shelf_boxes)

            sim_time += self.dt

        total_deadlocks = sum(a.deadlock_count for a in agents)
        total_violations = sum(a.proxemic_violations for a in agents)
        max_t = max(a.travel_time for a in agents)
        all_docked = all(a.is_docked for a in agents)

        return TrialResult(
            method="Reactive Avoidance",
            trial_id=trial_id,
            completion_time=max_t if all_docked else self.max_sim_time,
            all_docked=all_docked,
            deadlocks_count=total_deadlocks,
            proxemic_violations=total_violations,
            total_packets=0,
            total_replans=0
        )

    def run_benchmark_suite(self, num_trials: int = 15) -> Dict[str, Dict[str, float]]:
        print(f"Executing Benchmark Suite ({num_trials} Monte Carlo trials per method)...")
        results = {"D2RO (SW-DGO)": [], "Static A*": [], "Reactive Avoidance": []}

        for t in range(num_trials):
            seed = 1000 + t
            res_d2ro = self.run_d2ro_trial(t, seed)
            res_astar = self.run_static_astar_trial(t, seed)
            res_react = self.run_reactive_trial(t, seed)

            results["D2RO (SW-DGO)"].append(res_d2ro)
            results["Static A*"].append(res_astar)
            results["Reactive Avoidance"].append(res_react)

        # Aggregate Statistics
        summary = {}
        for method, res_list in results.items():
            success_rate = (sum(1 for r in res_list if r.all_docked) / num_trials) * 100.0
            mean_time = sum(r.completion_time for r in res_list) / num_trials
            mean_deadlocks = sum(r.deadlocks_count for r in res_list) / num_trials
            mean_violations = sum(r.proxemic_violations for r in res_list) / num_trials
            mean_packets = sum(r.total_packets for r in res_list) / num_trials
            mean_replans = sum(r.total_replans for r in res_list) / num_trials

            summary[method] = {
                "Success Rate (%)": success_rate,
                "Mean Time (s)": round(mean_time, 2),
                "Mean Deadlocks": round(mean_deadlocks, 2),
                "Mean Proxemic Violations": round(mean_violations, 2),
                "Mean Mesh Packets": round(mean_packets, 1),
                "Mean Replans": round(mean_replans, 1)
            }

        return summary

def main():
    harness = BenchmarkHarness(num_trolleys=4, num_humans=8, max_sim_time=60.0)
    summary = harness.run_benchmark_suite(num_trials=20)

    print("\n" + "=" * 80)
    print(f"{'METHOD':<22} | {'SUCCESS (%)':<11} | {'TIME (s)':<9} | {'DEADLOCKS':<10} | {'PROX VIOLATIONS':<15} | {'MESH PKTS':<9}")
    print("=" * 80)
    for method, stats in summary.items():
        print(f"{method:<22} | {stats['Success Rate (%)']:<11.1f} | {stats['Mean Time (s)']:<9.2f} | {stats['Mean Deadlocks']:<10.2f} | {stats['Mean Proxemic Violations']:<15.2f} | {stats['Mean Mesh Packets']:<9.1f}")
    print("=" * 80)

if __name__ == "__main__":
    main()
