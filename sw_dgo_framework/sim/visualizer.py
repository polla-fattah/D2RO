"""
Visualizer and Trajectory Exporter for SW-DGO Framework.
Renders real-time simulation state or exports high-resolution SVG/HTML animation frames.
"""

from __future__ import annotations
import math
from typing import List, Dict, Tuple
from ..environments.supermarket import SupermarketLayout
from ..core.mesh_network import MeshNetwork
from ..core.agent import TrolleyAgent
from ..core.human import Human, ProxemicsField

class SimulationVisualizer:
    """
    Renders SVG / HTML interactive visual replay of the SW-DGO supermarket simulation.
    """
    def __init__(self, layout: SupermarketLayout, width: int = 900, height: int = 650):
        self.layout = layout
        self.width = width
        self.height = height

    def export_html_animation(self, agents: List[TrolleyAgent], humans: List[Human],
                              history: List[Dict], output_path: str) -> None:
        """Exports a standalone interactive HTML visualizer with timeline playback."""
        min_x, min_y, max_x, max_y = self.layout.bounds

        # Generate Shelf SVG elements
        shelf_svg = []
        for s in self.layout.shelves:
            shelf_svg.append(f'<rect x="{s.x}" y="{s.y}" width="{s.w}" height="{s.h}" fill="#374151" rx="4" />')
            shelf_svg.append(f'<text x="{s.x + s.w/2}" y="{s.y + s.h/2}" font-size="10" fill="#9ca3af" text-anchor="middle" dominant-baseline="middle">{s.name}</text>')

        # Generate Node/Edge SVG elements
        edge_svg = []
        for (u, v), edge in self.layout.graph.edges.items():
            nu = self.layout.graph.get_node(u)
            nv = self.layout.graph.get_node(v)
            color = "#ef4444" if edge.is_single_file else "#4b5563"
            stroke_width = "2" if edge.is_single_file else "1"
            dash = 'stroke-dasharray="4,4"' if edge.is_single_file else ""
            edge_svg.append(f'<line x1="{nu.x}" y1="{nu.y}" x2="{nv.x}" y2="{nv.y}" stroke="{color}" stroke-width="{stroke_width}" {dash} />')

        node_svg = []
        for nid, n in self.layout.graph.nodes.items():
            fill = "#10b981" if n.is_docking_bay else "#60a5fa"
            r = "8" if n.is_docking_bay else "4"
            node_svg.append(f'<circle cx="{n.x}" cy="{n.y}" r="{r}" fill="{fill}" />')
            if n.is_docking_bay:
                node_svg.append(f'<text x="{n.x}" y="{n.y + 20}" font-size="11" font-weight="bold" fill="#10b981" text-anchor="middle">DOCK BAY</text>')

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>D²RO (SW-DGO) Simulation Replay</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #111827; color: #f3f4f6; margin: 0; padding: 20px; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #374151; padding-bottom: 10px; margin-bottom: 20px; }}
        .badge {{ background: #2563eb; color: white; padding: 4px 10px; border-radius: 9999px; font-size: 12px; }}
        .canvas-card {{ background: #1f2937; border-radius: 8px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); padding: 20px; text-align: center; }}
        svg {{ background: #111827; border: 1px solid #374151; border-radius: 6px; }}
        .controls {{ margin-top: 15px; display: flex; gap: 10px; align-items: center; justify-content: center; }}
        button {{ background: #3b82f6; border: none; color: white; padding: 8px 16px; border-radius: 4px; cursor: pointer; }}
        button:hover {{ background: #2563eb; }}
        .legend {{ display: flex; gap: 20px; justify-content: center; margin-top: 15px; font-size: 13px; }}
        .legend-item {{ display: flex; align-items: center; gap: 6px; }}
        .legend-color {{ width: 12px; height: 12px; border-radius: 2px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>D²RO Supermarket Fleet Simulation</h2>
            <span class="badge">SW-DGO + V2V Mesh</span>
        </div>
        <div class="canvas-card">
            <svg id="sim-svg" width="{self.width}" height="{self.height}" viewBox="{min_x} {min_y} {max_x - min_x} {max_y - min_y}">
                <g id="edges">{''.join(edge_svg)}</g>
                <g id="shelves">{''.join(shelf_svg)}</g>
                <g id="nodes">{''.join(node_svg)}</g>
                <g id="dynamic-layer"></g>
            </svg>
            <div class="controls">
                <button onclick="togglePlay()">Play / Pause</button>
                <input type="range" id="timeline" min="0" max="{len(history)-1}" value="0" style="width: 400px;" oninput="seekFrame(this.value)">
                <span id="frame-label">Time: 0.0s</span>
            </div>
            <div class="legend">
                <div class="legend-item"><div class="legend-color" style="background:#3b82f6;"></div> Trolleys</div>
                <div class="legend-item"><div class="legend-color" style="background:#f59e0b;"></div> Shoppers (Gaussian Bubble)</div>
                <div class="legend-item"><div class="legend-color" style="background:#ef4444;"></div> Single-File Aisles</div>
                <div class="legend-item"><div class="legend-color" style="background:#10b981;"></div> Docking Station</div>
            </div>
        </div>
    </div>
    <script>
        const historyData = {str(history).replace("'", '"').replace("True", "true").replace("False", "false")};
        let frameIdx = 0;
        let isPlaying = true;
        const layer = document.getElementById("dynamic-layer");
        const label = document.getElementById("frame-label");
        const slider = document.getElementById("timeline");

        function renderFrame(idx) {{
            const f = historyData[idx];
            if (!f) return;
            label.innerText = `Time: ${{f.time.toFixed(1)}}s (Replans: ${{f.replans}}, Pkts: ${{f.packets}})`;
            slider.value = idx;

            let html = "";
            // Render Humans with Gaussian bubbles
            f.humans.forEach(h => {{
                html += `<circle cx="${{h.x}}" cy="${{h.y}}" r="35" fill="rgba(245, 158, 11, 0.2)" />`;
                html += `<circle cx="${{h.x}}" cy="${{h.y}}" r="5" fill="#f59e0b" />`;
            }});

            // Render Trolleys
            f.agents.forEach(a => {{
                html += `<circle cx="${{a.x}}" cy="${{a.y}}" r="8" fill="${{a.docked ? '#10b981' : '#3b82f6'}}" stroke="#fff" stroke-width="1.5" />`;
                html += `<text x="${{a.x}}" y="${{a.y - 12}}" font-size="10" fill="#fff" text-anchor="middle">T${{a.id}}</text>`;
            }});

            layer.innerHTML = html;
        }}

        function togglePlay() {{ isPlaying = !isPlaying; }}
        function seekFrame(val) {{ frameIdx = parseInt(val); renderFrame(frameIdx); }}

        setInterval(() => {{
            if (isPlaying && frameIdx < historyData.length - 1) {{
                frameIdx++;
                renderFrame(frameIdx);
            }}
        }}, 50);
        renderFrame(0);
    </script>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Exported interactive visualizer replay to: {output_path}")
