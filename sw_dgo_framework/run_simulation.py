"""
Main Execution Script for SW-DGO Framework (D²RO).
Runs all benchmark scenarios (Scenarios A through E), logs yielding events,
and exports the interactive multi-scenario HTML dashboard.
"""

import os
from sw_dgo_framework.environments.supermarket import SupermarketLayout, ScenarioSuite
from sw_dgo_framework.core.mesh_network import MeshNetwork
from sw_dgo_framework.core.agent import TrolleyAgent
from sw_dgo_framework.core.human import Human, ProxemicsField
from sw_dgo_framework.sim.visualizer import SimulationVisualizer

def run_all_scenarios():
    print("=" * 75)
    print("  D²RO (SW-DGO) MULTI-SCENARIO FLEET SIMULATION ENGINE")
    print("=" * 75)
    
    layout = SupermarketLayout(num_aisles=5)
    prox_field = ProxemicsField(amplitude=400.0, sigma=38.0)
    scenarios_data = {}

    scenario_keys = ["A", "B", "C", "D", "E"]

    for scn_key in scenario_keys:
        trolley_cfgs, humans, description = ScenarioSuite.get_scenario(scn_key, layout)
        print(f"\n[Running Scenario {scn_key}] {description}")

        mesh = MeshNetwork(comm_radius=350.0)
        agents = []
        for cfg in trolley_cfgs:
            agent = TrolleyAgent(
                agent_id=cfg["id"],
                graph=layout.graph,
                start_node=cfg["start"],
                goal_node=cfg["goal"],
                mesh_net=mesh
            )
            agents.append(agent)

        dt = 0.1
        sim_time = 0.0
        max_time = 45.0
        frames = []

        while sim_time < max_time and not all(a.is_docked for a in agents):
            # Update dynamic humans
            for h in humans:
                h.update(dt, layout.bounds)

            # Step agents (D* Lite replanning + social yielding + corridor locks)
            for a in agents:
                a.step(dt, humans, prox_field, sim_time)

            # Decay mesh penalties
            layout.graph.decay_mesh_penalties(dt, decay_rate=2.0)

            # Record frame
            frame_agents = [{
                "id": a.agent_id,
                "x": round(a.x, 1),
                "y": round(a.y, 1),
                "heading": round(a.heading, 3),
                "state": a.state,
                "docked": a.is_docked
            } for a in agents]

            frame_humans = [{
                "id": h.id,
                "x": round(h.x, 1),
                "y": round(h.y, 1)
            } for h in humans]

            frames.append({
                "time": round(sim_time, 2),
                "agents": frame_agents,
                "humans": frame_humans,
                "packets": mesh.total_packets_transmitted,
                "replans": sum(a.replan_count for a in agents)
            })

            sim_time += dt

        print(f"  -> Finished in {round(sim_time, 1)}s. Total Replans: {sum(a.replan_count for a in agents)}, Mesh Packets: {mesh.total_packets_transmitted}")
        scenarios_data[scn_key] = {
            "description": description,
            "frames": frames
        }

    # Export interactive multi-scenario visualizer
    viz = SimulationVisualizer(layout)
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "simulation_replay.html")
    viz.export_multi_scenario_html(scenarios_data, out_path)
    print("\n" + "=" * 75)
    print(f"  Dashboard successfully exported to:\n  {out_path}")
    print("=" * 75)

if __name__ == "__main__":
    run_all_scenarios()
