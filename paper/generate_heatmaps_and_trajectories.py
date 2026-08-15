"""
High-Resolution Trajectory Heatmaps & Spatiotemporal Visual Path Generator for D²RO Paper.
Produces publication-grade 300 DPI figures:
1. Fig 8: 2D Proxemic Discomfort Field Heatmap & Social Detour Comparison (Supermarket)
2. Fig 9: Spatiotemporal Time-Space Corridor Lock & Turnout Alcove Resolution (Hospital)
3. Fig 10: Multi-Agent Trajectory Streamlines & Crowd Flow in Open Concourse (Airport)
"""

from __future__ import annotations
import os
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(OUT_DIR, exist_ok=True)

# Publication styling
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#334155"
plt.rcParams["axes.linewidth"] = 1.2

# ------------------------------------------------------------------------------
# 1. Figure 8: Supermarket 2D Proxemic Heatmap & Social Detour Overlay
# ------------------------------------------------------------------------------
def generate_figure_8():
    fig, ax = plt.subplots(figsize=(10.5, 6.8), dpi=300)
    ax.set_facecolor("#f8fafc")
    ax.set_xlim(20, 1000)
    ax.set_ylim(560, 40)  # Inverted y for top-down floorplan

    # Compute continuous 2D Gaussian proxemics field grid
    x_grid = np.linspace(20, 1000, 200)
    y_grid = np.linspace(40, 560, 120)
    X, Y = np.meshgrid(x_grid, y_grid)
    Z = np.zeros_like(X)

    # Dynamic human shopper clusters (Aisle 3 crowd)
    humans = [
        (410, 160, 55.0, 38.0),
        (410, 200, 60.0, 42.0),
        (410, 240, 50.0, 35.0),
        (525, 340, 40.0, 32.0),
        (295, 380, 45.0, 34.0),
        (640, 270, 40.0, 30.0)
    ]
    for hx, hy, amp, sig in humans:
        Z += amp * np.exp(-((X - hx)**2 + (Y - hy)**2) / (2 * sig**2))

    # Heatmap Colormap: Smooth Transparent-to-Amber-to-Crimson
    cdict = {
        'red':   [(0.0, 1.0, 1.0), (0.2, 0.99, 0.99), (0.6, 0.96, 0.96), (1.0, 0.88, 0.88)],
        'green': [(0.0, 1.0, 1.0), (0.2, 0.85, 0.85), (0.6, 0.45, 0.45), (1.0, 0.10, 0.10)],
        'blue':  [(0.0, 1.0, 1.0), (0.2, 0.65, 0.65), (0.6, 0.15, 0.15), (1.0, 0.10, 0.10)],
        'alpha': [(0.0, 0.0, 0.0), (0.15, 0.25, 0.25), (0.6, 0.65, 0.65), (1.0, 0.85, 0.85)]
    }
    custom_cmap = LinearSegmentedColormap('ProxemicMap', cdict)

    im = ax.imshow(Z, extent=[20, 1000, 560, 40], origin='upper', cmap=custom_cmap, vmin=0, vmax=100)
    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Gaussian Human Proxemic Discomfort Field $H_{prox}(x, y)$", fontsize=10, fontweight="bold")

    # Draw Retail Shelves
    for i in range(6):
        x = 180 + i * 115
        ax.add_patch(patches.Rectangle((x - 18, 120), 36, 120, facecolor="#334155", edgecolor="#0f172a", linewidth=1.5, zorder=3))
        ax.add_patch(patches.Rectangle((x - 18, 300), 36, 120, facecolor="#334155", edgecolor="#0f172a", linewidth=1.5, zorder=3))
        ax.text(x, 180, f"Aisle {i+1}", color="#f8fafc", fontsize=7.5, ha="center", va="center", rotation=90, fontweight="bold", zorder=4)
        ax.text(x, 360, f"Aisle {i+1}", color="#f8fafc", fontsize=7.5, ha="center", va="center", rotation=90, fontweight="bold", zorder=4)

    # Produce & Deli Zones
    ax.add_patch(patches.Rectangle((40, 120), 60, 300, facecolor="#064e3b", edgecolor="#047857", linewidth=1.5, zorder=3))
    ax.text(70, 270, "PRODUCE & FRESH", color="#6ee7b7", fontsize=8, ha="center", va="center", rotation=90, fontweight="bold", zorder=4)
    ax.add_patch(patches.Rectangle((870, 120), 60, 300, facecolor="#881337", edgecolor="#be123c", linewidth=1.5, zorder=3))
    ax.text(900, 270, "DELI & BAKERY", color="#fecdd3", fontsize=8, ha="center", va="center", rotation=90, fontweight="bold", zorder=4)

    # Action Alley Label
    ax.text(475, 270, "— CENTRAL ACTION ALLEY (TRANSVERSE PROMENADE) —", color="#475569", fontsize=8.5, ha="center", va="center", fontweight="bold", zorder=4)

    # Cart Depots
    for x_d in [295, 410, 525, 640]:
        ax.add_patch(patches.Circle((x_d, 520), 11, facecolor="#059669", edgecolor="#ffffff", linewidth=1.8, zorder=5))
        ax.text(x_d, 545, "DEPOT", color="#059669", fontsize=7.5, ha="center", va="center", fontweight="bold", zorder=5)

    # Start and Goal markers
    start_pos = (410, 80)
    goal_pos = (410, 520)
    ax.scatter([start_pos[0]], [start_pos[1]], color="#10b981", s=140, edgecolors="#0f172a", linewidth=2, zorder=6, label="Mission Start (T1)")
    ax.scatter([goal_pos[0]], [goal_pos[1]], color="#ef4444", s=140, marker="*", edgecolors="#0f172a", linewidth=2, zorder=6, label="Target Cart Depot")

    # 1. Static A* Path (Drives straight through crowd in Aisle 3)
    ax.plot([410, 410], [80, 520], color="#dc2626", linestyle="--", linewidth=3.0, zorder=5, label="Static A* Path (Blind to Crowd Violations)")

    # 2. D²RO (SW-DGO Proposed) Social Detour Path (Diverts through Aisle 2 & Action Alley)
    d2ro_x = [410, 295, 295, 295, 410]
    d2ro_y = [80, 80, 270, 520, 520]
    ax.plot(d2ro_x, d2ro_y, color="#0284c7", linestyle="-", linewidth=3.5, zorder=5, label="D²RO SW-DGO Path (Proactive Social Detour)")

    # Kinetic Safety Clearance Envelope on cart
    ax.add_patch(patches.Circle((295, 270), 26, facecolor="none", edgecolor="#0284c7", linestyle="--", linewidth=1.5, zorder=6))
    ax.add_patch(patches.Rectangle((287, 264), 16, 12, facecolor="#0284c7", edgecolor="#ffffff", linewidth=1.5, zorder=7))
    ax.text(295, 252, "T1 (D²RO)", color="#0284c7", fontsize=8, fontweight="bold", ha="center", zorder=7)

    # Human markers
    for hx, hy, _, _ in humans:
        ax.add_patch(patches.Circle((hx, hy), 7, facecolor="#ea580c", edgecolor="#ffffff", linewidth=1.2, zorder=6))

    ax.legend(loc="upper left", frameon=True, fontsize=9.5, facecolor="#ffffff", edgecolor="#334155")
    ax.set_title("Spatial Human Proxemic Discomfort Field & D²RO Social Detour Trajectory Overlay",
                 fontsize=11.5, fontweight="bold", pad=12)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig8_social_detour_proxemic_heatmap.png"), dpi=300)
    plt.savefig(os.path.join(OUT_DIR, "fig8_social_detour_proxemic_heatmap.pdf"))
    plt.close()
    print("  -> Generated: fig8_social_detour_proxemic_heatmap.png & .pdf")


# ------------------------------------------------------------------------------
# 2. Figure 9: Spatiotemporal Time-Space Diagram (Hospital Turnout Alcoves)
# ------------------------------------------------------------------------------
def generate_figure_9():
    fig, ax = plt.subplots(figsize=(9.0, 5.2), dpi=300)
    ax.set_facecolor("#f8fafc")

    # Time axis (0 to 18 seconds)
    t = np.linspace(0, 18, 200)

    # Main corridor coordinate X (0 to 1000 meters/pixels)
    # P1 (Emergency Pushchair - Traveling West to East: 100 -> 900 at 3.2 m/s)
    x_p1 = 100 + (800 / 12.0) * np.clip(t - 2.0, 0, 12.0)

    # P2 (Routine Pushchair - Traveling East to West: 900 -> 100)
    # At t=4.5s (reaches alcove at X=650), P2 pulls into Turnout Alcove and halts until t=10.5s when P1 passes
    x_p2 = np.zeros_like(t)
    for idx, time_val in enumerate(t):
        if time_val < 4.5:
            x_p2[idx] = 900 - (250 / 4.5) * time_val
        elif time_val <= 10.5:
            x_p2[idx] = 650.0  # Held in Turnout Alcove
        else:
            x_p2[idx] = 650.0 - (550 / 7.5) * (time_val - 10.5)

    # Draw Corridor Boundaries & Alcove Zone
    ax.axvspan(620, 680, color="#fef3c7", alpha=0.6, label="Turnout Alcove Active Zone ($V_{alcove}$)")
    ax.axvline(650, color="#d97706", linestyle="--", linewidth=1.5)
    ax.text(650, 17.2, "Turnout Alcove ($X=650$)", color="#b45309", fontsize=9, fontweight="bold", ha="center")

    # Plot Trajectories
    ax.plot(x_p1, t, color="#dc2626", linewidth=2.8, label="P1: Emergency Trauma Pushchair (Priority Lock $R_{lock}=\infty$)")
    ax.plot(x_p2, t, color="#0284c7", linewidth=2.8, linestyle="--", label="P2: Routine Patient Pushchair (Alcove Yield & Wait)")

    # Annotations
    ax.annotate("P2 pulls into Alcove\nyielding corridor", xy=(650, 4.5), xytext=(450, 6.0),
                arrowprops=dict(facecolor="#0284c7", shrink=0.05, width=1.5, headwidth=6),
                fontsize=9, fontweight="bold", color="#0284c7")

    ax.annotate("P1 passes without\nkinematic slowdown", xy=(650, 9.5), xytext=(720, 8.5),
                arrowprops=dict(facecolor="#dc2626", shrink=0.05, width=1.5, headwidth=6),
                fontsize=9, fontweight="bold", color="#dc2626")

    ax.annotate("P2 resumes transit\nafter Lock Release", xy=(650, 10.5), xytext=(460, 13.0),
                arrowprops=dict(facecolor="#0284c7", shrink=0.05, width=1.5, headwidth=6),
                fontsize=9, fontweight="bold", color="#0284c7")

    ax.set_xlabel("Corridor Longitudinal Position $X$ (px)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Spatiotemporal Progression Time $t$ (seconds)", fontsize=11, fontweight="bold")
    ax.set_title("Spatiotemporal Time-Space Trajectory Diagram of Turnout Alcove Resolution",
                 fontsize=11.5, fontweight="bold", pad=12)
    ax.set_ylim(0, 18)
    ax.set_xlim(50, 950)
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.legend(loc="lower left", frameon=True, fontsize=9.5)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig9_spatiotemporal_alcove_lock_diagram.png"), dpi=300)
    plt.savefig(os.path.join(OUT_DIR, "fig9_spatiotemporal_alcove_lock_diagram.pdf"))
    plt.close()
    print("  -> Generated: fig9_spatiotemporal_alcove_lock_diagram.png & .pdf")


# ------------------------------------------------------------------------------
# 3. Figure 10: Airport Open Concourse Streamlines & Crowd Density
# ------------------------------------------------------------------------------
def generate_figure_10():
    fig, ax = plt.subplots(figsize=(10.5, 6.5), dpi=300)
    ax.set_facecolor("#f8fafc")
    ax.set_xlim(20, 960)
    ax.set_ylim(560, 40)

    # Concourse vector flow field
    Y, X = np.mgrid[40:560:80j, 20:960:120j]
    U = np.ones_like(X) * 1.5
    V = np.zeros_like(Y)

    # Crowd vortex deflection near security chokepoint (X=480, Y=140) and central plaza (X=480, Y=270)
    deflect_1 = np.exp(-((X - 480)**2 + (Y - 140)**2) / (2 * 70**2))
    deflect_2 = np.exp(-((X - 480)**2 + (Y - 320)**2) / (2 * 80**2))
    V += -2.5 * deflect_1 + 2.0 * deflect_2
    U += -1.0 * (deflect_1 + deflect_2)

    # Streamplot of multi-agent flow
    strm = ax.streamplot(X, Y, U, V, color="#94a3b8", density=1.1, linewidth=1.0, arrowsize=1.2)

    # Check-in Banks
    for i in range(3):
        x = 90 + i * 110
        ax.add_patch(patches.Rectangle((x-20, 90), 40, 100, facecolor="#0f2942", edgecolor="#0284c7", linewidth=1.5, zorder=3))
        ax.text(x, 140, f"Check-in {i+1}", color="#7dd3fc", fontsize=7.5, ha="center", va="center", fontweight="bold", zorder=4)

    # Security Screening Bottleneck
    ax.add_patch(patches.Rectangle((440, 80), 80, 120, facecolor="#451a03", edgecolor="#d97706", linewidth=1.8, zorder=3))
    ax.text(480, 140, "SECURITY\nCHOKEPOINT", color="#fcd34d", fontsize=8, ha="center", va="center", fontweight="bold", zorder=4)

    # Gate Lounges
    for x, y, name in [(750, 80, "GATE PIER A"), (750, 360, "GATE PIER B")]:
        ax.add_patch(patches.Rectangle((x-40, y), 80, 120, facecolor="#064e3b", edgecolor="#059669", linewidth=1.8, zorder=3))
        ax.text(x, y + 60, name, color="#6ee7b7", fontsize=8, ha="center", va="center", fontweight="bold", zorder=4)

    # Central Plaza Label
    ax.text(480, 270, "— MAIN OPEN-PLAN CONCOURSE PLAZA —", color="#64748b", fontsize=8.5, ha="center", va="center", fontweight="bold", zorder=4)

    # Multiple Luggage Cart Trajectories
    # Cart 1: Check-in 1 -> Gate A
    c1_x = [90, 250, 440, 520, 750]
    c1_y = [200, 240, 200, 140, 140]
    ax.plot(c1_x, c1_y, color="#0284c7", linewidth=3.0, zorder=5, label="Cart L1: Check-in -> Gate A")

    # Cart 2: Check-in 3 -> Gate B
    c2_x = [310, 420, 580, 750]
    c2_y = [200, 380, 420, 420]
    ax.plot(c2_x, c2_y, color="#10b981", linewidth=3.0, linestyle="--", zorder=5, label="Cart L2: Check-in -> Gate B")

    # Dynamic Pedestrians with Halos
    for hx, hy in [(340, 240), (480, 240), (600, 300), (380, 380), (550, 180), (700, 220), (250, 360)]:
        ax.add_patch(patches.Circle((hx, hy), 22, facecolor="none", edgecolor="#f59e0b", linestyle=":", linewidth=1.2, zorder=4))
        ax.add_patch(patches.Circle((hx, hy), 7, facecolor="#ea580c", edgecolor="#ffffff", linewidth=1.2, zorder=5))

    ax.legend(loc="upper left", frameon=True, fontsize=9.5, facecolor="#ffffff")
    ax.set_title("Airport Open Concourse Vector Flow Streamlines & Multi-Agent Luggage Trajectories",
                 fontsize=11.5, fontweight="bold", pad=12)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig10_airport_crowd_density_streamlines.png"), dpi=300)
    plt.savefig(os.path.join(OUT_DIR, "fig10_airport_crowd_density_streamlines.pdf"))
    plt.close()
    print("  -> Generated: fig10_airport_crowd_density_streamlines.png & .pdf")


def main():
    print("=" * 80)
    print("  GENERATING TRAJECTORY HEATMAPS & VISUAL PATH SNAPSHOTS (300 DPI)")
    print("=" * 80)
    generate_figure_8()
    generate_figure_9()
    generate_figure_10()
    print("\n" + "=" * 80)
    print(f"  ALL 3 HEATMAP FIGURES SUCCESSFULLY SAVED IN: {OUT_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()
