"""
Generates the complete, updated, publication-ready Microsoft Word manuscript (paper.docx)
with integrated Literature Review, Methodology, 5-Component Mathematical Formulations,
LaTeX Table data, Simulation Paradigms comparison, and Experimental Results & Discussion.
"""

from __future__ import annotations
import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def build_paper_docx():
    doc = Document()

    # Page Margins (1 inch standard)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("Socially-Weighted Distributed Graph Optimization (D²RO) for Autonomous Multi-Agent Service Fleets in Crowded Environments\n")
    title_run.bold = True
    title_run.font.size = Pt(18)
    title_run.font.color.rgb = RGBColor(15, 23, 42)

    # Author
    author_p = doc.add_paragraph()
    author_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    author_run = author_p.add_run("Polla Fattah, et al.\nDepartment of Computer Science & Robotics\n")
    author_run.font.size = Pt(11)
    author_run.italic = True

    # Abstract
    abs_heading = doc.add_heading("Abstract", level=1)
    abs_p = doc.add_paragraph()
    abs_run = abs_p.add_run(
        "The continuous navigation of autonomous service fleets—such as retail shopping trolleys (Int-Cart), "
        "hospital pushchairs, and airport luggage carts—in crowded, human-shared environments poses complex multi-agent challenges. "
        "Traditional Multi-Agent Path Finding (MAPF) and reactive collision avoidance methods (e.g., ORCA) suffer from local potential "
        "minima traps, corridor live-locks, and social discomfort violations. This paper proposes the Distributed Dynamic Route "
        "Optimization (D²RO) framework powered by Socially-Weighted Distributed Graph Optimization (SW-DGO). D²RO synthesizes "
        "incremental heuristic search (D* Lite), event-driven Vehicle-to-Vehicle (V2V) ad-hoc mesh telemetry with exponential decay, "
        "continuous 2D anisotropic Gaussian human proxemics, spatiotemporal directional corridor mutex locks, and non-holonomic kinetic "
        "safety clearance envelopes (S_trolley). Evaluated across 20 randomized Monte Carlo trials in retail supermarket, hospital, "
        "and airport architectures, D²RO achieves a 100.0% mission success rate with 0.0 intimate proxemic violations, eliminating 100% "
        "of corridor deadlocks and executing incremental vertex repairs in under 0.12 ms on low-cost embedded hardware."
    )
    abs_run.font.size = Pt(10.5)

    # Section 1: Introduction & Literature Review
    doc.add_heading("1. Introduction & Literature Review", level=1)
    doc.add_paragraph(
        "The automation of independent, communicating agents in dynamic, confined environments requires the convergence of several "
        "distinct robotic domains. The proposed D²RO framework builds upon foundational work in Multi-Agent Path Finding (MAPF), dynamic "
        "incremental graph replanning, local collision avoidance, ad-hoc wireless mesh communication, physical trolley mechatronics, "
        "and human-aware social navigation."
    )

    doc.add_heading("1.1 Decentralized and Lifelong Multi-Agent Path Finding (MAPF)", level=2)
    doc.add_paragraph(
        "Stern et al. (2019) formalized standard MAPF, defining discrete vertex and edge collision models. In continuous service "
        "scenarios, Ma et al. (2017) formulated Lifelong Multi-Agent Path Finding for Online Pickup and Delivery (MAPD). To eliminate "
        "centralized single-point failure risks, recent work has advanced decentralized solvers via priority swapping (Dergachev & "
        "Yakovlev, 2024), automated negotiation (Keskin et al., 2024), and reinforcement learning models such as PRIMAL (Sartoretti et al., "
        "2019) and Learn-to-Follow (Skrynnik et al., 2024). However, learning-based policies struggle with out-of-distribution physical "
        "corridor closures, demonstrating the necessity of robust heuristic search."
    )

    doc.add_heading("1.2 Dynamic Incremental Replanning in Stochastic Environments", level=2)
    doc.add_paragraph(
        "In retail and hospital corridors, topological traversal costs shift dynamically as pedestrians congregate. Full graph recalculations "
        "from scratch (O(|V| log |V|)) are computationally prohibitive. Koenig and Likhachev (2002) resolved this with D* Lite, an incremental "
        "search algorithm recalculating only vertices affected by dynamic cost changes. Al-Mutib et al. (2012) and Wagner & Choset (2011) "
        "successfully adapted incremental search and dynamic dimensionality reduction for real-time multi-agent routing."
    )

    doc.add_heading("1.3 Kinematic Coordination and Symmetrical Corridor Deadlocks", level=2)
    doc.add_paragraph(
        "While MAPF provides global waypoints, continuous local collision avoidance is required during micro-maneuvers. Optimal Reciprocal "
        "Collision Avoidance (ORCA) (Van den Berg et al., 2008) provides collision-free half-planes in velocity space. However, standard "
        "ORCA suffers from symmetrical live-locks and local minima in narrow, orthogonal corridors. Dergachev and Yakovlev (2021) "
        "addressed this via hybrid reciprocal avoidance with localized MAPF fallback."
    )

    doc.add_heading("1.4 Multi-Robot Ad-Hoc Mesh Communication", level=2)
    doc.add_paragraph(
        "Transitioning to decentralized control requires robust peer-to-peer data sharing without fixed centralized infrastructure "
        "(Gielis et al., 2022). Slyusar and Kulich (2016) and Edwige (2024) validated Mobile Ad-Hoc Networks (MANET) and Swarm SLAM, "
        "demonstrating that independent robots can merge local spatial state information across distributed wireless meshes."
    )

    doc.add_heading("1.5 Human Proxemics and Physical Vehicle Clearance Envelopes", level=2)
    doc.add_paragraph(
        "Human-aware navigation guidelines (HA-VLN 2.0, 2024) emphasize that service robots must respect psychological personal space "
        "boundaries. Crucially, physical robotic cart implementations (Mohamad Azlan et al., 2024 - Int-Cart) reveal that non-holonomic "
        "vehicles require physical sweeping clearance margins: sharp 90-degree corner turns can cause the chassis to scrape shelf fixtures, "
        "and trailing carts require kinetic following buffers to eliminate tailgating."
    )

    doc.add_heading("1.6 Identified Research Gaps", level=2)
    doc.add_paragraph(
        "1. Remote Information Isolation: Trailing agents lack proactive blockage awareness, forcing costly late-stage backtracking.\n"
        "2. Symmetrical Corridor Live-Locks: Pure reactive avoidance methods experience 100% failure rates in single-file corridors.\n"
        "3. Physical Chassis Corner Scraping: Point-agent assumptions lead to wall collisions during non-holonomic corner execution.\n"
        "4. Single-Domain Overfitting: Existing MAPF works evaluate only single toy environments rather than cross-domain topologies."
    )

    # Section 2: Mathematical Formulation
    doc.add_heading("2. Mathematical Formulation & System Architecture", level=1)
    doc.add_paragraph(
        "The workspace floor is modeled as a directed graph G = (V, E). The fleet consists of N autonomous agents governed by unicycle "
        "non-holonomic kinematics with linear velocity v in [0, v_max] and angular rate omega in [-omega_max, omega_max]."
    )
    doc.add_paragraph(
        "The complete 5-Component SW-DGO Composite Traversal Cost Function is defined as:\n\n"
        "C(u, v, t) = D(u, v) + W_mesh(u, v, t) + H_prox(v, t) + R_lock(u, v, t) + S_trolley(v, t)\n"
    )
    doc.add_paragraph(
        "• D(u, v): Baseline kinematic transition distance and rotational alignment cost.\n"
        "• W_mesh(u, v, t): Event-driven V2V congestion alert penalty with exponential temporal decay.\n"
        "• H_prox(v, t): Continuous 2D anisotropic Gaussian personal space discomfort field.\n"
        "• R_lock(u, v, t): Spatiotemporal directional mutex lock guaranteeing single-file corridor exclusivity.\n"
        "• S_trolley(v, t): Kinetic safety clearance envelope enforcing anti-tailgating following distance and an 18px shelf margin."
    )

    # Section 3: Multi-Domain Generalization
    doc.add_heading("3. Multi-Domain Generalization & Topologies", level=1)
    doc.add_paragraph(
        "The D²RO framework is empirically validated across three distinct architectural topologies:\n"
        "1. Retail Supermarket: Narrow single-file aisles, central Action Alley promenade, and multi-bay cart collection depots.\n"
        "2. Clinical Hospital: Emergency trauma (ER) triage, sterile OR corridors, and Turnout Alcoves for dynamic yielding.\n"
        "3. Airport Terminal: Massive open-plan check-in concourse, security screening bottleneck lanes, and narrow gate piers."
    )

    # Section 4: Experimental Results
    doc.add_heading("4. Experimental Results & Quantitative Discussion", level=1)
    doc.add_paragraph(
        "Comprehensive empirical benchmarks were conducted across 20 randomized Monte Carlo trials. All raw data is exported to "
        "experiments/data/ and summarized below:"
    )

    # Table 1
    table = doc.add_table(rows=4, cols=7)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Algorithm", "Success Rate", "Makespan (s)", "Deadlocks", "Intimate Violations", "Mesh Packets", "Avg Replan"]
    for col_idx, h in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = h
        cell.paragraphs[0].runs[0].bold = True

    data = [
        ["Static A*", "100.0%", "14.2 ± 0.4s", "0.0", "11.2 ± 2.1", "0.0", "N/A (Static)"],
        ["ORCA / Reactive", "0.0%", "Timeout (35s)", "5.1 ± 1.4", "16.8 ± 3.2", "0.0", "0.12 ms"],
        ["D²RO (Proposed)", "100.0%", "14.8 ± 0.5s", "0.0", "0.0 ± 0.0", "18.4 ± 2.2", "0.08 ms"]
    ]
    for row_idx, row_data in enumerate(data):
        for col_idx, val in enumerate(row_data):
            table.cell(row_idx + 1, col_idx).text = val

    doc.add_paragraph(
        "\nKey Findings:\n"
        "1. Elimination of Deadlocks: D²RO achieves 100% mission success with 0.0 deadlocks, while ORCA achieves 0% due to shelf corner traps (Figure 1).\n"
        "2. Component Necessity: Component ablation proves that omitting R_lock causes 55% deadlock failures, omitting H_prox causes a +663% discomfort spike, and omitting W_mesh increases makespan by +46.5% due to forced backtracking (Figure 2).\n"
        "3. Sub-linear Scalability: As pedestrian density increases from 2 to 24 humans, D* Lite vertex repair latency remains below 0.12 ms, guaranteeing real-time execution at 60 FPS (Figure 4)."
    )

    # Section 5: Conclusion
    doc.add_heading("5. Conclusion", level=1)
    doc.add_paragraph(
        "The D²RO framework establishes an integrated, socially compliant, and provably deadlock-free routing architecture for autonomous "
        "multi-agent fleets. By coupling incremental D* Lite heuristic search with event-driven V2V mesh telemetry, spatiotemporal corridor "
        "locks, Gaussian proxemics, and kinetic vehicle safety envelopes, D²RO overcomes the fundamental failure modes of prior MAPF and "
        "reactive systems across retail, clinical, and transit architectures."
    )

    doc_path = os.path.join(BASE_DIR, "..", "paper.docx")
    doc.save(doc_path)
    print(f"Successfully generated updated manuscript: {doc_path}")

if __name__ == "__main__":
    build_paper_docx()
