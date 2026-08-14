"""
Native Python Desktop GUI Visualizer for D²RO / SW-DGO Framework.
Built with Python's native Tkinter Canvas for 60 FPS real-time simulation,
interactive scenario switching, live telemetry, and direct obstacle placement.
"""

from __future__ import annotations
import math
import time
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Tuple, Optional
from ..environments.supermarket import SupermarketLayout, ScenarioSuite
from ..core.mesh_network import MeshNetwork
from ..core.agent import TrolleyAgent
from ..core.human import Human, ProxemicsField

class SupermarketSimApp:
    """
    Native Python GUI Application for D²RO Fleet Simulation.
    """
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("D²RO (SW-DGO) Supermarket Fleet Simulator")
        self.root.geometry("1120x820")
        self.root.configure(bg="#0f172a")

        # Simulation parameters & state
        self.layout = SupermarketLayout(num_aisles=5)
        self.prox_field = ProxemicsField(amplitude=450.0, sigma=38.0)
        self.current_scenario_key = "A"
        self.is_running = True
        self.sim_speed = 1.0
        self.dt = 0.05
        self.sim_time = 0.0

        # Simulation entities
        self.mesh_net: Optional[MeshNetwork] = None
        self.agents: List[TrolleyAgent] = []
        self.humans: List[Human] = []
        self.scenario_desc = ""

        # Geometry helpers
        self.shelf_boxes = [s.bounds for s in self.layout.shelves]
        self.aisle_x = [self.layout.start_x + i * self.layout.aisle_spacing for i in range(self.layout.num_aisles)]
        self.crossway_y = [
            self.layout.start_y,
            self.layout.start_y + self.layout.aisle_length / 2.0,
            self.layout.start_y + self.layout.aisle_length,
            self.layout.start_y + self.layout.aisle_length + 80.0
        ]

        self._create_widgets()
        self.load_scenario("A")
        self._sim_loop()

    def _create_widgets(self) -> None:
        # Top Header & Scenario Tabs
        top_frame = tk.Frame(self.root, bg="#0f172a", pady=10)
        top_frame.pack(fill=tk.X, padx=16)

        title_lbl = tk.Label(top_frame, text="D²RO Fleet Simulator (SW-DGO + V2V Mesh)",
                             font=("Segoe UI", 16, "bold"), fg="#ffffff", bg="#0f172a")
        title_lbl.pack(anchor="w")

        # Scenario Button Tabs
        tab_frame = tk.Frame(top_frame, bg="#0f172a", pady=8)
        tab_frame.pack(fill=tk.X)

        self.tab_buttons: Dict[str, tk.Button] = {}
        scenarios = [
            ("A", "Scenario A: Aisle Congestion"),
            ("B", "Scenario B: Corridor Lock"),
            ("C", "Scenario C: V2V Blockage"),
            ("D", "Scenario D: Social Yielding"),
            ("E", "Scenario E: Rush Hour")
        ]

        for key, label in scenarios:
            btn = tk.Button(tab_frame, text=label, font=("Segoe UI", 9, "bold"),
                            bg="#1e293b", fg="#94a3b8", activebackground="#2563eb",
                            activeforeground="#ffffff", relief=tk.FLAT, padx=10, pady=5,
                            command=lambda k=key: self.load_scenario(k))
            btn.pack(side=tk.LEFT, padx=4)
            self.tab_buttons[key] = btn

        # Banner Description
        self.desc_lbl = tk.Label(self.root, text="", font=("Segoe UI", 10),
                                 fg="#38bdf8", bg="#1e293b", padx=12, pady=6, anchor="w")
        self.desc_lbl.pack(fill=tk.X, padx=16, pady=4)

        # Simulation Canvas
        min_x, min_y, max_x, max_y = self.layout.bounds
        self.canvas = tk.Canvas(self.root, width=int(max_x - min_x) + 40, height=int(max_y - min_y) + 40,
                               bg="#0b1120", highlightthickness=1, highlightbackground="#334155")
        self.canvas.pack(padx=16, pady=8)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Bottom Controls & Telemetry
        bottom_frame = tk.Frame(self.root, bg="#0f172a", pady=6)
        bottom_frame.pack(fill=tk.X, padx=16)

        # Play / Pause / Reset Buttons
        ctrl_frame = tk.Frame(bottom_frame, bg="#0f172a")
        ctrl_frame.pack(side=tk.LEFT)

        self.play_btn = tk.Button(ctrl_frame, text="Pause", font=("Segoe UI", 10, "bold"),
                                  bg="#2563eb", fg="#ffffff", padx=14, pady=4, relief=tk.FLAT,
                                  command=self._toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=4)

        restart_btn = tk.Button(ctrl_frame, text="Restart", font=("Segoe UI", 10, "bold"),
                                bg="#475569", fg="#ffffff", padx=14, pady=4, relief=tk.FLAT,
                                command=lambda: self.load_scenario(self.current_scenario_key))
        restart_btn.pack(side=tk.LEFT, padx=4)

        # Telemetry Labels
        self.telemetry_lbl = tk.Label(bottom_frame, text="", font=("Consolas", 10),
                                      fg="#f8fafc", bg="#1e293b", padx=12, pady=5)
        self.telemetry_lbl.pack(side=tk.RIGHT)

    def load_scenario(self, key: str) -> None:
        self.current_scenario_key = key
        self.sim_time = 0.0

        # Update tab styles
        for k, btn in self.tab_buttons.items():
            if k == key:
                btn.configure(bg="#2563eb", fg="#ffffff")
            else:
                btn.configure(bg="#1e293b", fg="#94a3b8")

        # Reset layout graph locks and penalties
        self.layout = SupermarketLayout(num_aisles=5)
        trolley_cfgs, self.humans, self.scenario_desc = ScenarioSuite.get_scenario(key, self.layout)
        self.desc_lbl.configure(text=self.scenario_desc)

        self.mesh_net = MeshNetwork(comm_radius=350.0)
        self.agents = []
        for cfg in trolley_cfgs:
            agent = TrolleyAgent(
                agent_id=cfg["id"],
                graph=self.layout.graph,
                start_node=cfg["start"],
                goal_node=cfg["goal"],
                mesh_net=self.mesh_net
            )
            self.agents.append(agent)

    def _toggle_play(self) -> None:
        self.is_running = not self.is_running
        self.play_btn.configure(text="Pause" if self.is_running else "Play")

    def _on_canvas_click(self, event: tk.Event) -> None:
        """Left click allows user to dynamically place a congestion penalty on the nearest aisle."""
        click_x, click_y = event.x, event.y
        nearest_node = None
        min_d = 999999.0
        for nid, n in self.layout.graph.nodes.items():
            d = math.hypot(click_x - n.x, click_y - n.y)
            if d < min_d:
                min_d = d
                nearest_node = nid

        if nearest_node and min_d < 40.0:
            # Broadcast obstacle alert at nearest node
            for a in self.agents:
                for succ in self.layout.graph.successors(nearest_node):
                    a.broadcast_congestion(nearest_node, succ, penalty=500.0, current_time=self.sim_time)
            print(f"[User Click] Spawned Dynamic Blockage near {nearest_node}")

    def _sim_loop(self) -> None:
        if self.is_running and self.agents:
            self.sim_time += self.dt

            # 1. Update dynamic humans with shelf collision clamping
            for h in self.humans:
                h.update(self.dt, self.layout.bounds, self.shelf_boxes, self.aisle_x, self.crossway_y)

            # 2. Step trolley agents with D* Lite, mesh & yielding
            for a in self.agents:
                a.step(self.dt, self.humans, self.prox_field, current_sim_time=self.sim_time, shelves=self.shelf_boxes)

            # 3. Decay mesh penalties over time
            self.layout.graph.decay_mesh_penalties(self.dt, decay_rate=2.0)

        # Draw frame
        self._render()

        # 30 ms tick (~33 FPS smooth animation)
        self.root.after(30, self._sim_loop)

    def _render(self) -> None:
        self.canvas.delete("all")

        # 1. Draw Edges (Aisles & Crossways)
        for (u, v), edge in self.layout.graph.edges.items():
            nu = self.layout.graph.get_node(u)
            nv = self.layout.graph.get_node(v)
            color = "#f43f5e" if edge.is_single_file else "#475569"
            dash = (4, 4) if edge.is_single_file else ()
            w = 2 if edge.is_single_file else 1
            self.canvas.create_line(nu.x, nu.y, nv.x, nv.y, fill=color, width=w, dash=dash)

        # 2. Draw Shelves
        for s in self.layout.shelves:
            self.canvas.create_rectangle(s.x, s.y, s.x + s.w, s.y + s.h,
                                        fill="#1e293b", outline="#334155", width=2)
            self.canvas.create_text(s.x + s.w/2, s.y + s.h/2, text=s.name,
                                   fill="#94a3b8", font=("Segoe UI", 9, "bold"))

        # 3. Draw Nodes
        for nid, n in self.layout.graph.nodes.items():
            if n.is_docking_bay:
                self.canvas.create_oval(n.x - 9, n.y - 9, n.x + 9, n.y + 9, fill="#10b981", outline="#ffffff", width=1.5)
                self.canvas.create_text(n.x, n.y + 20, text="DOCK BAY", fill="#10b981", font=("Segoe UI", 10, "bold"))
            else:
                self.canvas.create_oval(n.x - 3.5, n.y - 3.5, n.x + 3.5, n.y + 3.5, fill="#38bdf8", outline="")

        # 4. Draw Humans (Shoppers with Gaussian Halos)
        for h in self.humans:
            # Gaussian Personal-Space Halo
            self.canvas.create_oval(h.x - 38, h.y - 38, h.x + 38, h.y + 38,
                                   outline="#f97316", width=1, dash=(3, 3))
            self.canvas.create_oval(h.x - 18, h.y - 18, h.x + 18, h.y + 18,
                                   fill="#7c2d12", outline="")
            # Human Body
            self.canvas.create_oval(h.x - 6, h.y - 6, h.x + 6, h.y + 6,
                                   fill="#f97316", outline="#ffffff", width=1.5)

        # 5. Draw Trolley Agents
        for a in self.agents:
            color = "#3b82f6"  # Default: Navigating
            badge_text = ""
            if a.is_docked:
                color = "#10b981"
            elif a.state == "YIELDING_HUMAN":
                color = "#f59e0b"
                badge_text = "YIELD"
            elif a.state == "WAITING_LOCK":
                color = "#a855f7"
                badge_text = "LOCK WAIT"

            # Heading indicator line
            hx = a.x + math.cos(a.heading) * 15
            hy = a.y + math.sin(a.heading) * 15
            self.canvas.create_line(a.x, a.y, hx, hy, fill=color, width=2.5)

            # Body circle
            self.canvas.create_oval(a.x - 9, a.y - 9, a.x + 9, a.y + 9,
                                   fill=color, outline="#ffffff", width=2)
            # Label
            self.canvas.create_text(a.x, a.y - 14, text=f"T{a.agent_id}",
                                   fill="#ffffff", font=("Segoe UI", 9, "bold"))
            if badge_text:
                self.canvas.create_text(a.x, a.y + 18, text=badge_text,
                                       fill=color, font=("Segoe UI", 8, "bold"))

        # 6. Update Telemetry
        replans = sum(a.replan_count for a in self.agents)
        packets = self.mesh_net.total_packets_transmitted if self.mesh_net else 0
        docked = sum(1 for a in self.agents if a.is_docked)
        yielding = sum(1 for a in self.agents if a.state == "YIELDING_HUMAN")
        
        telemetry_text = f"Time: {self.sim_time:.1f}s | Replans: {replans} | Mesh Pkts: {packets} | Yielding: {yielding} | Docked: {docked}/{len(self.agents)}"
        self.telemetry_lbl.configure(text=telemetry_text)


def launch_gui():
    root = tk.Tk()
    app = SupermarketSimApp(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
