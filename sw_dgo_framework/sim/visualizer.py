"""
Multi-Scenario Interactive Visualizer for SW-DGO Framework (D²RO).
Generates a standalone web dashboard featuring live scenario switching (Scenarios A through E),
speed controls, yielding/braking telemetry, Gaussian proxemic halos, and trajectory inspection.
"""

from __future__ import annotations
import json
from typing import List, Dict, Tuple
from ..environments.supermarket import SupermarketLayout

class SimulationVisualizer:
    """
    Renders multi-scenario interactive HTML5/SVG simulation dashboards.
    """
    def __init__(self, layout: SupermarketLayout, width: int = 950, height: int = 680):
        self.layout = layout
        self.width = width
        self.height = height

    def export_multi_scenario_html(self, scenarios_data: Dict[str, Dict], output_path: str) -> None:
        """
        Exports an interactive HTML dashboard containing precomputed trajectories
        for all benchmark scenarios (A through E).
        """
        min_x, min_y, max_x, max_y = self.layout.bounds

        # Static Shelf SVG Elements
        shelf_svg = []
        for s in self.layout.shelves:
            shelf_svg.append(f'<rect x="{s.x}" y="{s.y}" width="{s.w}" height="{s.h}" fill="#1f2937" stroke="#374151" stroke-width="1.5" rx="4" />')
            shelf_svg.append(f'<text x="{s.x + s.w/2}" y="{s.y + s.h/2}" font-size="11" font-weight="600" fill="#9ca3af" text-anchor="middle" dominant-baseline="middle">{s.name}</text>')

        # Static Node / Aisle SVG Elements
        edge_svg = []
        for (u, v), edge in self.layout.graph.edges.items():
            nu = self.layout.graph.get_node(u)
            nv = self.layout.graph.get_node(v)
            color = "#f43f5e" if edge.is_single_file else "#4b5563"
            stroke_w = "2.5" if edge.is_single_file else "1.5"
            dash = 'stroke-dasharray="4,4"' if edge.is_single_file else ""
            edge_svg.append(f'<line x1="{nu.x}" y1="{nu.y}" x2="{nv.x}" y2="{nv.y}" stroke="{color}" stroke-width="{stroke_w}" {dash} opacity="0.75" />')

        node_svg = []
        for nid, n in self.layout.graph.nodes.items():
            fill = "#10b981" if n.is_docking_bay else "#38bdf8"
            r = "9" if n.is_docking_bay else "4"
            node_svg.append(f'<circle cx="{n.x}" cy="{n.y}" r="{r}" fill="{fill}" />')
            if n.is_docking_bay:
                node_svg.append(f'<text x="{n.x}" y="{n.y + 22}" font-size="12" font-weight="bold" fill="#10b981" text-anchor="middle">CART DOCK</text>')

        scenarios_json = json.dumps(scenarios_data)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>D²RO (SW-DGO) Multi-Scenario Fleet Simulation</title>
    <style>
        :root {{
            --bg-main: #0f172a;
            --card-bg: #1e293b;
            --accent: #3b82f6;
            --text: #f8fafc;
            --text-dim: #94a3b8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        body {{ background: var(--bg-main); color: var(--text); padding: 24px; }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        
        /* Header & Navigation */
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
        .title-group h1 {{ font-size: 22px; font-weight: 700; color: #fff; }}
        .title-group p {{ font-size: 13px; color: var(--text-dim); margin-top: 4px; }}
        .scenario-tabs {{ display: flex; gap: 8px; margin-bottom: 16px; }}
        .tab-btn {{ background: #334155; border: none; color: var(--text-dim); padding: 8px 16px; border-radius: 6px; font-weight: 600; font-size: 13px; cursor: pointer; transition: all 0.2s; }}
        .tab-btn:hover {{ background: #475569; color: #fff; }}
        .tab-btn.active {{ background: #2563eb; color: #fff; box-shadow: 0 4px 12px rgba(37,99,235,0.3); }}

        /* Main Canvas Card */
        .canvas-card {{ background: var(--card-bg); border-radius: 12px; border: 1px solid #334155; padding: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
        .scenario-banner {{ background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; padding: 10px 14px; border-radius: 4px; font-size: 13px; margin-bottom: 14px; color: #cbd5e1; }}
        
        svg {{ background: #0b1120; border: 1px solid #1e293b; border-radius: 8px; width: 100%; height: auto; }}
        
        /* Playback Controls */
        .controls-panel {{ display: flex; align-items: center; justify-content: space-between; margin-top: 16px; padding-top: 12px; border-top: 1px solid #334155; flex-wrap: wrap; gap: 12px; }}
        .btn-group {{ display: flex; gap: 8px; align-items: center; }}
        .ctrl-btn {{ background: #2563eb; border: none; color: white; padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.15s; }}
        .ctrl-btn:hover {{ background: #1d4ed8; }}
        .ctrl-btn.secondary {{ background: #475569; }}
        .ctrl-btn.secondary:hover {{ background: #64748b; }}
        
        .timeline-group {{ display: flex; align-items: center; gap: 12px; flex: 1; min-width: 280px; }}
        input[type="range"] {{ flex: 1; accent-color: #3b82f6; cursor: pointer; }}
        .time-badge {{ background: #0f172a; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-family: monospace; color: #38bdf8; }}
        
        /* Telemetry Stats & Legend */
        .stats-bar {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-top: 16px; }}
        .stat-card {{ background: #0f172a; padding: 10px 14px; border-radius: 6px; border: 1px solid #334155; }}
        .stat-label {{ font-size: 11px; color: var(--text-dim); text-transform: uppercase; }}
        .stat-val {{ font-size: 16px; font-weight: 700; color: #fff; margin-top: 2px; }}
        
        .legend {{ display: flex; gap: 18px; margin-top: 16px; font-size: 12px; flex-wrap: wrap; }}
        .legend-item {{ display: flex; align-items: center; gap: 6px; color: var(--text-dim); }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title-group">
                <h1>D²RO Multi-Scenario Fleet Simulator</h1>
                <p>Socially-Weighted Distributed Graph Optimization (SW-DGO) + Ad-Hoc V2V Mesh</p>
            </div>
        </div>

        <div class="scenario-tabs">
            <button class="tab-btn active" onclick="switchScenario('A')">Scenario A: Aisle Congestion</button>
            <button class="tab-btn" onclick="switchScenario('B')">Scenario B: Corridor Lock (Head-On)</button>
            <button class="tab-btn" onclick="switchScenario('C')">Scenario C: Sudden V2V Blockage</button>
            <button class="tab-btn" onclick="switchScenario('D')">Scenario D: Social Yielding</button>
            <button class="tab-btn" onclick="switchScenario('E')">Scenario E: Rush Hour</button>
        </div>

        <div class="canvas-card">
            <div class="scenario-banner" id="scenario-desc">Loading scenario...</div>
            
            <svg id="sim-svg" viewBox="{min_x} {min_y} {max_x - min_x} {max_y - min_y}">
                <g id="edges">{''.join(edge_svg)}</g>
                <g id="shelves">{''.join(shelf_svg)}</g>
                <g id="nodes">{''.join(node_svg)}</g>
                <g id="dynamic-layer"></g>
            </svg>

            <div class="controls-panel">
                <div class="btn-group">
                    <button class="ctrl-btn" id="play-btn" onclick="togglePlay()">Pause</button>
                    <button class="ctrl-btn secondary" onclick="restartSim()">Restart</button>
                </div>

                <div class="timeline-group">
                    <input type="range" id="timeline" min="0" max="100" value="0" oninput="seekFrame(this.value)">
                    <span class="time-badge" id="time-display">0.0s</span>
                </div>
            </div>

            <div class="stats-bar">
                <div class="stat-card">
                    <div class="stat-label">Active Trolleys</div>
                    <div class="stat-val" id="stat-trolleys">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Mesh Packets Transmitted</div>
                    <div class="stat-val" id="stat-packets">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Dynamic D* Replans</div>
                    <div class="stat-val" id="stat-replans">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Yielding / Braking</div>
                    <div class="stat-val" id="stat-yielding" style="color:#f59e0b;">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Docked Status</div>
                    <div class="stat-val" id="stat-docked" style="color:#10b981;">0 / 0</div>
                </div>
            </div>

            <div class="legend">
                <div class="legend-item"><span class="legend-dot" style="background:#3b82f6;"></span> Trolley (Navigating)</div>
                <div class="legend-item"><span class="legend-dot" style="background:#f59e0b;"></span> Trolley (Yielding to Human)</div>
                <div class="legend-item"><span class="legend-dot" style="background:#a855f7;"></span> Trolley (Corridor Lock Wait)</div>
                <div class="legend-item"><span class="legend-dot" style="background:#10b981;"></span> Docked Trolley</div>
                <div class="legend-item"><span class="legend-dot" style="background:#f97316;"></span> Shopper (Gaussian Bubble)</div>
                <div class="legend-item"><span class="legend-dot" style="background:#f43f5e;"></span> Single-File Aisle</div>
            </div>
        </div>
    </div>

    <script>
        const scenarioDB = {scenarios_json};
        let currentKey = 'A';
        let frameIdx = 0;
        let isPlaying = true;
        let timer = null;

        const layer = document.getElementById("dynamic-layer");
        const slider = document.getElementById("timeline");
        const timeDisplay = document.getElementById("time-display");
        const playBtn = document.getElementById("play-btn");
        const descBanner = document.getElementById("scenario-desc");

        function switchScenario(key) {{
            currentKey = key;
            frameIdx = 0;
            
            // Update tab buttons
            document.querySelectorAll(".tab-btn").forEach((btn, idx) => {{
                btn.classList.toggle("active", btn.innerText.includes(`Scenario ${{key}}`));
            }});

            const scn = scenarioDB[key];
            descBanner.innerText = scn.description;
            slider.max = scn.frames.length - 1;
            slider.value = 0;

            renderFrame(0);
        }}

        function renderFrame(idx) {{
            const scn = scenarioDB[currentKey];
            if (!scn || !scn.frames[idx]) return;
            const f = scn.frames[idx];

            timeDisplay.innerText = `${{f.time.toFixed(1)}}s`;
            slider.value = idx;

            // Update stats
            document.getElementById("stat-trolleys").innerText = f.agents.length;
            document.getElementById("stat-packets").innerText = f.packets;
            document.getElementById("stat-replans").innerText = f.replans;
            
            const yieldingCount = f.agents.filter(a => a.state === 'YIELDING_HUMAN').length;
            document.getElementById("stat-yielding").innerText = yieldingCount;

            const dockedCount = f.agents.filter(a => a.docked).length;
            document.getElementById("stat-docked").innerText = `${{dockedCount}} / ${{f.agents.length}}`;

            let svgHtml = "";

            // 1. Render Humans & Continuous Gaussian Halos
            f.humans.forEach(h => {{
                // Outer Gaussian personal space field
                svgHtml += `<circle cx="${{h.x}}" cy="${{h.y}}" r="38" fill="rgba(249, 115, 22, 0.15)" stroke="rgba(249, 115, 22, 0.3)" stroke-dasharray="3,3" />`;
                // Inner intimate zone
                svgHtml += `<circle cx="${{h.x}}" cy="${{h.y}}" r="16" fill="rgba(249, 115, 22, 0.35)" />`;
                // Human body center
                svgHtml += `<circle cx="${{h.x}}" cy="${{h.y}}" r="6" fill="#f97316" stroke="#fff" stroke-width="1.5" />`;
            }});

            // 2. Render Trolleys & State Indicators
            f.agents.forEach(a => {{
                let color = "#3b82f6"; // Navigating
                if (a.docked) color = "#10b981"; // Docked
                else if (a.state === "YIELDING_HUMAN") color = "#f59e0b"; // Yielding / Braking
                else if (a.state === "WAITING_LOCK") color = "#a855f7"; // Waiting lock

                // Heading velocity indicator
                const hx = a.x + Math.cos(a.heading) * 14;
                const hy = a.y + Math.sin(a.heading) * 14;
                svgHtml += `<line x1="${{a.x}}" y1="${{a.y}}" x2="${{hx}}" y2="${{hy}}" stroke="${{color}}" stroke-width="2.5" />`;

                // Trolley body
                svgHtml += `<circle cx="${{a.x}}" cy="${{a.y}}" r="9" fill="${{color}}" stroke="#fff" stroke-width="1.8" />`;
                
                // Label
                svgHtml += `<text x="${{a.x}}" y="${{a.y - 13}}" font-size="11" font-weight="700" fill="#fff" text-anchor="middle">T${{a.id}}</text>`;
                
                // Yielding text banner if stopped
                if (a.state === "YIELDING_HUMAN") {{
                    svgHtml += `<text x="${{a.x}}" y="${{a.y + 20}}" font-size="9" font-weight="bold" fill="#f59e0b" text-anchor="middle">YIELD</text>`;
                }} else if (a.state === "WAITING_LOCK") {{
                    svgHtml += `<text x="${{a.x}}" y="${{a.y + 20}}" font-size="9" font-weight="bold" fill="#a855f7" text-anchor="middle">LOCK WAIT</text>`;
                }}
            }});

            layer.innerHTML = svgHtml;
        }}

        function togglePlay() {{
            isPlaying = !isPlaying;
            playBtn.innerText = isPlaying ? "Pause" : "Play";
        }}

        function restartSim() {{
            frameIdx = 0;
            renderFrame(0);
        }}

        function seekFrame(val) {{
            frameIdx = parseInt(val);
            renderFrame(frameIdx);
        }}

        // Main playback loop
        setInterval(() => {{
            const scn = scenarioDB[currentKey];
            if (isPlaying && scn && frameIdx < scn.frames.length - 1) {{
                frameIdx++;
                renderFrame(frameIdx);
            }}
        }}, 50);

        // Initialize with Scenario A
        switchScenario('A');
    </script>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Exported multi-scenario dashboard to: {output_path}")
