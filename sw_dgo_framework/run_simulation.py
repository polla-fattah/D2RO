"""
Main Execution Script for SW-DGO Framework (D²RO).
Runs a live simulation, logs real-time telemetry, exports the interactive HTML visualizer,
and runs the comparative benchmark suite.
"""

import os
from sw_dgo_framework.environments.supermarket import SupermarketLayout
from sw_dgo_framework.core.mesh_network import MeshNetwork
from sw_dgo_framework.core.agent import TrolleyAgent
from sw_dgo_framework.core.human import Human, ProxemicsField
from sw_dgo_framework.sim.visualizer import SimulationVisualizer
from sw_dgo_framework.sim.benchmark import BenchmarkHarness

def run_single_simulation():
    print("Initializing Supermarket Environment & D²RO Fleet...")
    layout = SupermarketLayout(num_aisles=5)
    mesh = MeshNetwork(comm_radius=350.0)
    prox_field = ProxemicsField(amplitude=45.0, sigma=35.0)

    # Spawn 4 Trolleys at different starting aisles
    agents = [
        TrolleyAgent(1, layout.graph, "N_top_0", "DOCK_BAY", mesh),
        TrolleyAgent(2, layout.graph, "N_top_1", "DOCK_BAY", mesh),
        TrolleyAgent(3, layout.graph, "N_top_3", "DOCK_BAY", mesh),
        TrolleyAgent(4, layout.graph, "N_top_4", "DOCK_BAY", mesh),
    ]

    # Spawn 6 dynamic shoppers
    humans = [
        Human(1, 220.0, 200.0, speed=1.1),
        Human(2, 360.0, 280.0, speed=0.9),
        Human(3, 500.0, 180.0, speed=1.2),
        Human(4, 640.0, 310.0, speed=1.0),
        Human(5, 300.0, 420.0, speed=0.8),
        Human(6, 580.0, 400.0, speed=1.1),
    ]

    dt = 0.1
    sim_time = 0.0
    max_time = 40.0
    history = []

    print("Running D²RO Simulation Loop...")
    while sim_time < max_time and not all(a.is_docked for a in agents):
        for h in humans:
            h.update(dt, layout.bounds)

        for a in agents:
            a.step(dt, humans, prox_field, sim_time)

        layout.graph.decay_mesh_penalties(dt, decay_rate=2.0)

        # Log frame for visualizer
        frame_agents = [{"id": a.agent_id, "x": round(a.x, 1), "y": round(a.y, 1), "docked": a.is_docked} for a in agents]
        frame_humans = [{"id": h.id, "x": round(h.x, 1), "y": round(h.y, 1)} for h in humans]
        history.append({
            "time": round(sim_time, 2),
            "agents": frame_agents,
            "humans": frame_humans,
            "packets": mesh.total_packets_transmitted,
            "replans": sum(a.replan_count for a in agents)
        })

        sim_time += dt

    print(f"Simulation completed in {round(sim_time, 2)}s.")
    print(f"Total Mesh Packets Transmitted: {mesh.total_packets_transmitted}")
    print(f"All trolleys docked successfully: {all(a.is_docked for a in agents)}")

    # Export interactive visual replay
    viz = SimulationVisualizer(layout)
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "simulation_replay.html")
    viz.export_html_animation(agents, humans, history, out_path)

if __name__ == "__main__":
    run_single_simulation()
