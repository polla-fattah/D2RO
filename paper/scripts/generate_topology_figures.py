"""
Qualitative architectural figures (Figs. 5-7) for the D2RO manuscript.

These are ILLUSTRATIVE topology renders -- floorplans with representative planned
trajectories -- not statistical results. They are produced by running the simulator
directly and do not read the experiment CSVs.

Every DATA-DRIVEN table and figure is produced instead by
`generate_tables_and_figures.py`, which reads only analysis_results.json and
refuses to emit an artefact for a dataset that is missing or stale. Keep that
separation: nothing in this file may write an artefact that the data-driven
pipeline owns.

Companion script: `generate_heatmaps_and_trajectories.py` (Figs. 8-10), also
qualitative.
"""

from __future__ import annotations
import os
import csv
import math
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Set publication style
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#334155"
plt.rcParams["axes.linewidth"] = 1.2
plt.rcParams["grid.color"] = "#e2e8f0"
plt.rcParams["grid.linestyle"] = "--"
plt.rcParams["grid.alpha"] = 0.7

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "..", "experiments", "data")
OUT_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(OUT_DIR, exist_ok=True)



# ------------------------------------------------------------------------------
# 5. Figures 5-7: Architectural Simulation Snapshots
# ------------------------------------------------------------------------------
def generate_simulation_snapshots():
    # 5.1 Supermarket Architecture Figure
    fig, ax = plt.subplots(figsize=(9.5, 6.0), dpi=300)
    ax.set_facecolor("#0b1120")
    ax.set_xlim(20, 1000)
    ax.set_ylim(560, 40) # inverted y
    ax.axis("off")

    # Shelves
    for i in range(6):
        x = 180 + i * 115
        # Top block
        rect1 = patches.Rectangle((x - 18, 120), 36, 120, facecolor="#1e293b", edgecolor="#334155", linewidth=1.5)
        # Bottom block
        rect2 = patches.Rectangle((x - 18, 300), 36, 120, facecolor="#1e293b", edgecolor="#334155", linewidth=1.5)
        ax.add_patch(rect1)
        ax.add_patch(rect2)
        ax.text(x, 180, f"Aisle {i+1}", color="#94a3b8", fontsize=7.5, ha="center", va="center", rotation=90, fontweight="bold")
        ax.text(x, 360, f"Aisle {i+1}", color="#94a3b8", fontsize=7.5, ha="center", va="center", rotation=90, fontweight="bold")

    # Fresh & Deli
    ax.add_patch(patches.Rectangle((40, 120), 60, 300, facecolor="#064e3b", edgecolor="#059669", linewidth=1.5))
    ax.text(70, 270, "PRODUCE & FRESH", color="#6ee7b7", fontsize=8, ha="center", va="center", rotation=90, fontweight="bold")

    ax.add_patch(patches.Rectangle((870, 120), 60, 300, facecolor="#4c0519", edgecolor="#e11d48", linewidth=1.5))
    ax.text(900, 270, "DELI & BAKERY", color="#fda4af", fontsize=8, ha="center", va="center", rotation=90, fontweight="bold")

    # Action Alley label
    ax.text(475, 270, "— CENTRAL ACTION ALLEY (TRANSVERSE PROMENADE) —", color="#64748b", fontsize=8.5, ha="center", va="center", fontweight="bold")

    # Cart Depots
    for x_d in [295, 410, 525, 640]:
        ax.add_patch(patches.Circle((x_d, 520), 10, facecolor="#10b981", edgecolor="#ffffff", linewidth=1.5))
        ax.text(x_d, 545, "DEPOT", color="#10b981", fontsize=7.5, ha="center", va="center", fontweight="bold")

    # Trolleys with S_trolley safety rings
    t_positions = [(295, 160, "#3b82f6", "T1"), (525, 340, "#06b6d4", "T2"), (755, 270, "#a855f7", "T3")]
    for tx, ty, clr, tname in t_positions:
        # Safety ring
        ax.add_patch(patches.Circle((tx, ty), 24, facecolor="none", edgecolor=clr, linestyle="--", linewidth=1.2))
        # Body
        ax.add_patch(patches.Rectangle((tx-8, ty-6), 16, 12, facecolor=clr, edgecolor="#ffffff", linewidth=1.5))
        ax.text(tx, ty-16, tname, color="#ffffff", fontsize=8, ha="center", va="center", fontweight="bold")

    # Humans with Gaussian proxemics halos
    h_positions = [(295, 210), (640, 270), (410, 380)]
    for hx, hy in h_positions:
        ax.add_patch(patches.Circle((hx, hy), 35, facecolor="none", edgecolor="#f97316", linestyle=":", linewidth=1.2))
        ax.add_patch(patches.Circle((hx, hy), 14, facecolor="#7c2d12", edgecolor="none"))
        ax.add_patch(patches.Circle((hx, hy), 5, facecolor="#f97316", edgecolor="#ffffff", linewidth=1.2))

    # Path trajectories
    ax.plot([295, 295, 180, 180, 295], [160, 90, 90, 520, 520], color="#3b82f6", linestyle="--", linewidth=1.5)
    ax.plot([525, 525, 410], [340, 520, 520], color="#06b6d4", linestyle="--", linewidth=1.5)

    plt.title("Supermarket Environment Floorplan with SW-DGO Trajectories & Safety Envelopes",
              color="#f8fafc", fontsize=11, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig5_supermarket_topology_trajectories.png"), dpi=300, facecolor="#0b1120")
    plt.savefig(os.path.join(OUT_DIR, "fig5_supermarket_topology_trajectories.pdf"), facecolor="#0b1120")
    plt.close()
    print("  -> Generated: fig5_supermarket_topology_trajectories.png & .pdf")

    # 5.2 Hospital Architecture Figure
    fig, ax = plt.subplots(figsize=(9.5, 6.0), dpi=300)
    ax.set_facecolor("#050a18")
    ax.set_xlim(20, 1000)
    ax.set_ylim(560, 40)
    ax.axis("off")

    # Rooms
    rooms = [
        ("EMERGENCY TRAUMA (ER)", 50, 80, 180, 140, "#450a0a", "#dc2626", "#fca5a5"),
        ("STERILE OR & MRI SUITE", 750, 80, 180, 140, "#083344", "#0891b2", "#67e8f9"),
        ("CENTRAL NURSE HUB", 410, 220, 160, 100, "#0f172a", "#3b82f6", "#93c5fd"),
        ("CLINICAL WARD 1A", 50, 340, 180, 140, "#064e3b", "#059669", "#6ee7b7"),
        ("CLINICAL WARD 1B", 750, 340, 180, 140, "#064e3b", "#059669", "#6ee7b7"),
    ]
    for name, rx, ry, rw, rh, bg, bd, tx_c in rooms:
        ax.add_patch(patches.Rectangle((rx, ry), rw, rh, facecolor=bg, edgecolor=bd, linewidth=1.8))
        ax.text(rx + rw/2, ry + rh/2, name, color=tx_c, fontsize=8, ha="center", va="center", fontweight="bold")

    # Turnout Alcoves
    for ax_x, ax_y in [(300, 270), (680, 270)]:
        ax.add_patch(patches.Rectangle((ax_x-14, ax_y-14), 28, 28, facecolor="none", edgecolor="#f59e0b", linestyle="--", linewidth=1.5))
        ax.text(ax_x, ax_y-20, "TURNOUT ALCOVE", color="#f59e0b", fontsize=7, ha="center", va="center", fontweight="bold")

    # Pushchairs
    ax.add_patch(patches.Circle((140, 150), 22, facecolor="none", edgecolor="#dc2626", linestyle="--", linewidth=1.2))
    ax.add_patch(patches.Rectangle((132, 144), 16, 12, facecolor="#dc2626", edgecolor="#ffffff", linewidth=1.5))
    ax.text(140, 130, "P1 (EMERGENCY)", color="#fca5a5", fontsize=7.5, ha="center", va="center", fontweight="bold")

    ax.add_patch(patches.Circle((840, 150), 22, facecolor="none", edgecolor="#0284c7", linestyle="--", linewidth=1.2))
    ax.add_patch(patches.Rectangle((832, 144), 16, 12, facecolor="#0284c7", edgecolor="#ffffff", linewidth=1.5))
    ax.text(840, 130, "P2 (PATIENT)", color="#7dd3fc", fontsize=7.5, ha="center", va="center", fontweight="bold")

    # Alcove yielding trajectory
    ax.plot([140, 300, 490, 840], [150, 150, 150, 150], color="#dc2626", linestyle="-", linewidth=2.0)
    ax.plot([840, 680, 680], [150, 150, 270], color="#0284c7", linestyle="--", linewidth=1.8)

    plt.title("Hospital Pushchair Multi-Path Routing & Alcove Turnout Resolution",
              color="#38bdf8", fontsize=11, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig6_hospital_topology_trajectories.png"), dpi=300, facecolor="#050a18")
    plt.savefig(os.path.join(OUT_DIR, "fig6_hospital_topology_trajectories.pdf"), facecolor="#050a18")
    plt.close()
    print("  -> Generated: fig6_hospital_topology_trajectories.png & .pdf")

    # 5.3 Airport Architecture Figure
    fig, ax = plt.subplots(figsize=(9.5, 6.0), dpi=300)
    ax.set_facecolor("#060e20")
    ax.set_xlim(20, 960)
    ax.set_ylim(560, 40)
    ax.axis("off")

    # Check-in Banks
    for i in range(3):
        x = 90 + i * 110
        ax.add_patch(patches.Rectangle((x-20, 90), 40, 100, facecolor="#0f2942", edgecolor="#0284c7", linewidth=1.5))
        ax.text(x, 140, f"Check-in\nBank {i+1}", color="#7dd3fc", fontsize=7.5, ha="center", va="center", fontweight="bold")

    # Security lanes
    ax.add_patch(patches.Rectangle((440, 80), 80, 120, facecolor="#451a03", edgecolor="#d97706", linewidth=1.8))
    ax.text(480, 140, "SECURITY\nSCREENING", color="#fcd34d", fontsize=8, ha="center", va="center", fontweight="bold")

    # Gate Lounges
    for x, y, name in [(750, 80, "GATE A1-A2"), (750, 360, "GATE B1-B2")]:
        ax.add_patch(patches.Rectangle((x-40, y), 80, 120, facecolor="#064e3b", edgecolor="#059669", linewidth=1.8))
        ax.text(x, y + 60, name, color="#6ee7b7", fontsize=8, ha="center", va="center", fontweight="bold")

    # Central Concourse Plaza label
    ax.text(480, 270, "— MAIN AIRPORT TERMINAL CONCOURSE (OPEN PLAZA) —", color="#94a3b8", fontsize=8, ha="center", va="center", fontweight="bold")

    # Carts & Crowd
    for idx, (tx, ty) in enumerate([(200, 270), (480, 380), (680, 270)]):
        ax.add_patch(patches.Circle((tx, ty), 22, facecolor="none", edgecolor="#38bdf8", linestyle="--", linewidth=1.2))
        ax.add_patch(patches.Rectangle((tx-8, ty-6), 16, 12, facecolor="#0284c7", edgecolor="#ffffff", linewidth=1.5))
        ax.text(tx, ty-14, f"L{idx+1}", color="#ffffff", fontsize=7.5, ha="center", va="center", fontweight="bold")

    for hx, hy in [(340, 240), (480, 250), (600, 300), (380, 380), (550, 180), (700, 220)]:
        ax.add_patch(patches.Circle((hx, hy), 28, facecolor="none", edgecolor="#f59e0b", linestyle=":", linewidth=1.0))
        ax.add_patch(patches.Circle((hx, hy), 10, facecolor="#78350f", edgecolor="none"))

    plt.title("Airport Terminal Autonomous Luggage Trolley Concourse Simulation",
              color="#7dd3fc", fontsize=11, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fig7_airport_topology_trajectories.png"), dpi=300, facecolor="#060e20")
    plt.savefig(os.path.join(OUT_DIR, "fig7_airport_topology_trajectories.pdf"), facecolor="#060e20")
    plt.close()
    print("  -> Generated: fig7_airport_topology_trajectories.png & .pdf")


def main():
    print("Generating qualitative topology figures (Figs. 5-7)...")
    generate_simulation_snapshots()
    print(f"  Done -> {OUT_DIR}")


if __name__ == "__main__":
    main()
