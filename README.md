# D²RO — Socially-Weighted Distributed Graph Optimization for Autonomous Multi-Agent Service Fleets

> **Authors:** Polla Fattah and Sanar Fawzi  
> Department of Computer Science and Engineering  
> Contact: polla.fattah@koyauniversity.org · sanar.fawzi@koyauniversity.org

---

## Overview

**D²RO (Distributed Dynamic Route Optimization)** is a multi-agent path-planning framework powered by **SW-DGO (Socially-Weighted Distributed Graph Optimization)**. It enables fleets of autonomous trolleys (retail, hospital, airport) to navigate crowded human-shared environments **safely, efficiently, and socially-compliantly**.

The core contribution is a unified, 5-component edge traversal cost function:

```
C(u, v, t) = w_D · D(u,v)         # Euclidean distance
           + w_M · W_mesh(u,v,t)   # V2V anticipatory cost field
           + w_H · H_prox(v,t)     # Human Gaussian proxemics
           + w_R · R_lock(u,v,t)   # Directional corridor mutex
           + w_S · S_trolley(v,t)  # Non-holonomic safety envelope
```

solved incrementally via **D\* Lite** (sub-millisecond vertex repair, ≤ 1.23 ms at N_h = 30 pedestrians).

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Quick Start — Run All Experiments](#2-quick-start--run-all-experiments)
3. [Framework Architecture](#3-framework-architecture)
   - [Core Algorithms](#core-algorithms-sw_dgo_frameworkcore)
   - [Baseline Algorithms](#baseline-algorithms-sw_dgo_frameworkbaselines)
   - [Environment Domains](#environment-domains-sw_dgo_frameworkenvironments)
4. [Experimental Suite (2,500 Simulation Runs)](#4-experimental-suite-2500-simulation-runs)
   - [Exp 1 — Benchmark Comparison](#exp-1--comparative-benchmark)
   - [Exp 2 — Component Ablation](#exp-2--component-ablation-study)
   - [Exp 3 — Cross-Domain Generalization](#exp-3--cross-domain-generalization)
   - [Exp 4A — Crowd Density Scalability](#exp-4a--crowd-density-scalability)
   - [Exp 4B — Fleet Size Scalability](#exp-4b--fleet-size-scalability)
5. [Datasets — Where to Find the Data](#5-datasets--where-to-find-the-data)
6. [Paper Generation Pipeline](#6-paper-generation-pipeline)
7. [Key Empirical Results](#7-key-empirical-results)
8. [Dependencies](#8-dependencies)
9. [License](#9-license)

---

## 1. Project Structure

```
D2RO/
├── main.py                             # Interactive demo entry point
│
├── sw_dgo_framework/                   # Core simulation framework
│   ├── core/                           # D²RO algorithm internals
│   │   ├── agent.py                    # TrolleyAgent (D* Lite + SW-DGO)
│   │   ├── graph.py                    # Weighted navigation graph
│   │   ├── human.py                    # Human proxemics & Gaussian halo
│   │   └── mesh_network.py             # V2V telemetry mesh
│   ├── baselines/                      # Comparison algorithms
│   │   ├── static_astar.py             # Static A* (no social cost)
│   │   ├── artificial_potential_fields.py  # APF (repulsive forces)
│   │   ├── reactive_orca.py            # ORCA (velocity obstacles)
│   │   └── decentralized_local_mapf.py # Local MAPF (token-passing)
│   ├── environments/                   # Simulation domains
│   │   ├── supermarket.py              # Retail supermarket layout
│   │   ├── hospital.py                 # Clinical hospital + Turnout Alcoves
│   │   └── airport.py                  # Airport terminal concourse
│   ├── sim/
│   │   └── run_experiments.py          # Full 2,500-run experimental suite
│   └── tests/                          # Unit & integration tests
│
├── experiments/
│   └── data/                           # ← ALL RAW SIMULATION DATA (CSV)
│       ├── benchmark_comparison.csv        (500 rows: 5 algorithms × 100 trials)
│       ├── ablation_study.csv              (500 rows: 5 configs × 100 trials)
│       ├── cross_domain_benchmark.csv      (300 rows: 3 domains × 100 trials)
│       ├── scalability_crowd_density.csv   (600 rows: 6 densities × 100 trials)
│       ├── scalability_fleet_size.csv      (600 rows: 6 fleet sizes × 100 trials)
│       └── experimental_results_analysis.md  (auto-generated statistical report)
│
├── paper/
│   ├── paper.tex                       # LaTeX manuscript (IEEEtran)
│   ├── paper.pdf                       # Compiled camera-ready PDF
│   ├── references.bib                  # BibTeX bibliography
│   ├── D2RO_IEEE_Transactions_Overhaul.docx  # Microsoft Word submission copy
│   ├── figures/                        # 300 DPI publication figures (PDF + PNG)
│   │   ├── fig1_benchmark_comparison.*
│   │   ├── fig2_ablation_study.*
│   │   ├── fig3_cross_domain_generalization.*
│   │   ├── fig4_scalability_density.*
│   │   ├── fig5_supermarket_topology_trajectories.*
│   │   ├── fig6_hospital_topology_trajectories.*
│   │   ├── fig7_airport_topology_trajectories.*
│   │   ├── fig8_social_detour_proxemic_heatmap.*
│   │   ├── fig9_spatiotemporal_alcove_lock_diagram.*
│   │   └── fig10_airport_crowd_density_streamlines.*
│   ├── build_latex.py                  # Compiles paper.tex → paper.pdf
│   ├── build_paper_docx.py             # Generates paper.docx with all figures
│   ├── generate_paper_plots.py         # Produces Figs 1–7 from CSV data
│   ├── generate_heatmaps_and_trajectories.py  # Produces Figs 8–10
│   └── sync_data_to_manuscript.py      # Reads CSVs → computes statistics → reports
│
├── planners/                           # Research planning documents
│   ├── Response_to_Reviewers.md        # Point-by-point rebuttal (18 items)
│   └── Reviewer recommendation.md     # Original reviewer feedback
│
└── litrautre/                          # Literature reference PDFs
```

---

## 2. Quick Start — Run All Experiments

### Prerequisites
```powershell
pip install numpy scipy matplotlib python-docx
```

> **Python version:** 3.10+ recommended. Tested on Python 3.12.7.  
> **CPU:** All experiments use `multiprocessing` and finish in < 2 minutes on an 8-core machine.

### Step-by-Step Reproduction

**Step 1 — Run all 2,500 genuine simulation trials:**
```powershell
python sw_dgo_framework\sim\run_experiments.py
```
This will populate all 5 CSV files in `experiments/data/`.

**Step 2 — Compute statistics and verify results:**
```powershell
python paper\sync_data_to_manuscript.py
```
Outputs `experiments/data/experimental_results_analysis.md` with exact Welch's t-tests and 95% CIs.

**Step 3 — Generate all 10 publication figures (300 DPI):**
```powershell
python paper\generate_paper_plots.py
python paper\generate_heatmaps_and_trajectories.py
```
Figures saved to `paper/figures/`.

**Step 4 — Compile the LaTeX PDF:**
```powershell
python paper\build_latex.py
```
Requires MiKTeX or TeX Live. Output: `paper/paper.pdf`.

**Step 5 — Generate the Word document:**
```powershell
python paper\build_paper_docx.py
```
Output: `paper.docx` (in project root) and `paper/D2RO_IEEE_Transactions_Overhaul.docx`.

**Step 6 — Run the interactive simulation demo:**
```powershell
python main.py
```

---

## 3. Framework Architecture

### Core Algorithms (`sw_dgo_framework/core/`)

| File | Class | Description |
| :--- | :--- | :--- |
| [`agent.py`](sw_dgo_framework/core/agent.py) | `TrolleyAgent` | Main D²RO agent. Implements D\* Lite with the 5-component SW-DGO cost function, V2V mesh integration, corridor mutex acquisition, and proxemic-aware replanning. |
| [`graph.py`](sw_dgo_framework/core/graph.py) | `NavigationGraph` | Weighted directed graph representing the environment topology. Nodes = junction points; edges = corridor segments with dynamic cost fields. |
| [`human.py`](sw_dgo_framework/core/human.py) | `Human`, `ProxemicsField` | Stochastic pedestrian model. Generates continuous 2D asymmetric Gaussian discomfort halos $H_{\text{prox}}(v, t)$ using Hall's proxemic zones (intimate < 0.45 m, personal < 1.2 m). |
| [`mesh_network.py`](sw_dgo_framework/core/mesh_network.py) | `MeshNetwork` | V2V ad-hoc broadcast network with exponential time-decay. Propagates congestion alerts as anticipatory edge cost deltas $W_{\text{mesh}}(e, t) = W_0 \cdot e^{-\lambda t}$. |

### Baseline Algorithms (`sw_dgo_framework/baselines/`)

| File | Algorithm | Failure Mode in Narrow Aisles |
| :--- | :--- | :--- |
| [`static_astar.py`](sw_dgo_framework/baselines/static_astar.py) | Static A\* | Ignores pedestrians entirely → 4.00 ± 0.00 intimate violations/trial |
| [`artificial_potential_fields.py`](sw_dgo_framework/baselines/artificial_potential_fields.py) | APF | Force cancellation at 90° shelf corners → 0.0% success |
| [`reactive_orca.py`](sw_dgo_framework/baselines/reactive_orca.py) | Reactive ORCA | Infeasible velocity half-planes in single-file corridors (∩ Hᵢ = ∅) → 0.0% success |
| [`decentralized_local_mapf.py`](sw_dgo_framework/baselines/decentralized_local_mapf.py) | Decentralized Local MAPF | Head-on token-swap livelocks without global routing → 0.0% success |

### Environment Domains (`sw_dgo_framework/environments/`)

| File | Class | Dimensions | Key Features |
| :--- | :--- | :--- | :--- |
| [`supermarket.py`](sw_dgo_framework/environments/supermarket.py) | `SupermarketLayout`, `ScenarioSuite` | 1200×800 px (36 m × 24 m) | Orthogonal shelf rows, Action Alley, single-file aisles, checkout zone |
| [`hospital.py`](sw_dgo_framework/environments/hospital.py) | `HospitalLayout`, `HospitalScenarioSuite` | 1200×800 px | Turnout Alcoves (priority clearance), ER/OR/ICU zones, narrow clinical corridors |
| [`airport.py`](sw_dgo_framework/environments/airport.py) | `AirportLayout`, `AirportScenarioSuite` | 1200×800 px | Open concourse, gate piers, security pinch points, high-density passenger flow |

---

## 4. Experimental Suite (2,500 Simulation Runs)

All experiments use:
- **Control loop:** Δt = 0.05 s (20 Hz), non-holonomic unicycle kinematics  
- **Seeds:** Deterministic per-trial seed = trial_index + 1000  
- **Timeout:** T_max = 35.0 s (failure if not completed)  
- **Statistics:** Welch's t-test (two-sided, α = 0.01) with Satterthwaite degrees of freedom

### Exp 1 — Comparative Benchmark

**Dataset:** [`experiments/data/benchmark_comparison.csv`](experiments/data/benchmark_comparison.csv)  
**Conditions:** N = 100 trials × 5 algorithms = 500 runs  
**Algorithms:** D²RO (proposed), Static A\*, APF, Reactive ORCA, Decentralized Local MAPF  
**Metrics:** `success`, `travel_time_s`, `deadlocks`, `proxemic_violations`, `mesh_packets`, `replan_cycles`, `avg_replan_latency_ms`

### Exp 2 — Component Ablation Study

**Dataset:** [`experiments/data/ablation_study.csv`](experiments/data/ablation_study.csv)  
**Conditions:** N = 100 trials × 5 configurations = 500 runs  
**Configurations:** Full D²RO, w/o V2V Mesh (W_mesh=0), w/o Mutex Lock (R_lock=0), w/o Proxemics (H_prox=0), w/o Safety Bubble (S_trolley=0)  
**Metrics:** `success`, `travel_time_s`, `deadlocks`, `discomfort_integral`, `shelf_corner_scrapes`, `inter_cart_crowding`

### Exp 3 — Cross-Domain Generalization

**Dataset:** [`experiments/data/cross_domain_benchmark.csv`](experiments/data/cross_domain_benchmark.csv)  
**Conditions:** N = 100 trials × 3 environments = 300 runs  
**Domains:** Retail Supermarket, Clinical Hospital, Airport Terminal  
**Metrics:** `success_rate_pct`, `makespan_s`, `mean_transit_time_s`, `proxemic_violations`, `mesh_packets_exchanged`, `dynamic_replans`

### Exp 4A — Crowd Density Scalability

**Dataset:** [`experiments/data/scalability_crowd_density.csv`](experiments/data/scalability_crowd_density.csv)  
**Conditions:** N = 100 trials × 6 crowd levels = 600 runs  
**Crowd levels:** N_humans ∈ {2, 6, 12, 18, 24, 30} (fixed fleet N_carts = 4)  
**Metrics:** `success_rate_pct`, `makespan_s`, `mean_replan_latency_ms`, `discomfort_integral`, `v2v_mesh_packets`

### Exp 4B — Fleet Size Scalability

**Dataset:** [`experiments/data/scalability_fleet_size.csv`](experiments/data/scalability_fleet_size.csv)  
**Conditions:** N = 100 trials × 6 fleet sizes = 600 runs  
**Fleet sizes:** N_carts ∈ {2, 4, 6, 8, 10, 12} (fixed crowd N_humans = 10)  
**Metrics:** `success_rate_pct`, `makespan_s`, `mean_replan_latency_ms`, `corridor_mutex_wait_s`, `v2v_mesh_packets`

---

## 5. Datasets — Where to Find the Data

All raw simulation data is stored in plain CSV format under [`experiments/data/`](experiments/data/). Each file can be opened in Excel, Python (pandas), or R directly.

```
experiments/data/
├── benchmark_comparison.csv         # 500 rows — Exp 1 (5 algorithms)
├── ablation_study.csv               # 500 rows — Exp 2 (5 configurations)
├── cross_domain_benchmark.csv       # 300 rows — Exp 3 (3 environments)
├── scalability_crowd_density.csv    # 600 rows — Exp 4A (6 crowd levels)
├── scalability_fleet_size.csv       # 600 rows — Exp 4B (6 fleet sizes)
└── experimental_results_analysis.md # Auto-generated statistical tables
```

**To replicate the statistical analysis from scratch:**

```python
import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_csv("experiments/data/benchmark_comparison.csv")
d2ro = df[df["method"] == "D2RO (SW-DGO Proposed)"]["travel_time_s"].values
astar = df[df["method"] == "Static A*"]["travel_time_s"].values
t_stat, p_val = stats.ttest_ind(d2ro, astar, equal_var=False)  # Welch's t-test
print(f"Welch's t-test vs Static A*: t={t_stat:.3f}, p={p_val:.4e}")
```

---

## 6. Paper Generation Pipeline

```
experiments/data/*.csv
         │
         ▼
paper/sync_data_to_manuscript.py   → experiments/data/experimental_results_analysis.md
         │
         ▼
paper/generate_paper_plots.py      → paper/figures/fig1_*.pdf + fig2_*.pdf + fig3_*.pdf + fig4_*.pdf
paper/generate_heatmaps_and_trajectories.py → paper/figures/fig5_*.pdf ... fig10_*.pdf
         │
         ▼
paper/build_latex.py               → paper/paper.pdf   (MiKTeX/TeX Live required)
paper/build_paper_docx.py          → paper.docx
```

| Script | Purpose | Output |
| :--- | :--- | :--- |
| [`sync_data_to_manuscript.py`](paper/sync_data_to_manuscript.py) | Computes Mean, SD, 95% CI, Welch's t-test | `experimental_results_analysis.md` |
| [`generate_paper_plots.py`](paper/generate_paper_plots.py) | Figs 1–7 at 300 DPI | `paper/figures/fig1_*.{pdf,png}` – `fig7_*.{pdf,png}` |
| [`generate_heatmaps_and_trajectories.py`](paper/generate_heatmaps_and_trajectories.py) | Figs 8–10 at 300 DPI | `paper/figures/fig8_*.{pdf,png}` – `fig10_*.{pdf,png}` |
| [`build_latex.py`](paper/build_latex.py) | 4-pass PDFLaTeX + BibTeX | `paper/paper.pdf` |
| [`build_paper_docx.py`](paper/build_paper_docx.py) | Word document with embedded figures | `paper.docx`, `paper/D2RO_IEEE_Transactions_Overhaul.docx` |

---

## 7. Key Empirical Results

### Table I — Comparative Benchmark (N = 100 trials, Mean ± SD)

| Algorithm | Success | Makespan (s) [95% CI] | Deadlocks | Intimate Violations |
| :--- | :---: | :--- | :---: | :---: |
| **D²RO (Proposed)** | **97.0%** | **21.47 ± 5.32 [20.42, 22.53]** | **0.00** | **0.59 ± 5.90** |
| Static A\* | 100.0% | 0.80 ± 0.00 [0.80, 0.80] | 0.00 | 4.00 ± 0.00 |
| APF (Forces) | 0.0% | Timeout (35.0 s) | 0.01 | 226.39 ± 69.25 |
| ORCA (Velocity) | 0.0% | Timeout (35.0 s) | 2094.37 | 19.37 ± 65.28 |
| Decentralized MAPF | 0.0% | Timeout (35.0 s) | 11.00 | 102.44 ± 15.00 |

All Welch's t-tests vs D²RO: **p < 0.001**

### Table II — Ablation Study (N = 100 trials)

| Metric | Full D²RO | w/o V2V Mesh | w/o Mutex Lock | w/o Proxemics | w/o Safety Bubble |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Success (%) | **99.0%** | 100.0% | 100.0% | 17.0% | 100.0% |
| Makespan (s) | 22.98 ± 2.21 | 15.24 ± 1.95 | 15.24 ± 1.95 | 32.70 ± 5.67 | 21.26 ± 2.17 |
| Discomfort ∫ | **0.63 ± 3.09** | 0.43 ± 1.99 | 0.43 ± 1.99 | 71.56 ± 34.26 | 0.41 ± 2.07 |
| Shelf Scrapes | **0.00** | 0.00 | 0.00 | 0.00 | 77.72 ± 11.94 |

### Table III — Cross-Domain Generalization

| Domain | Success | Makespan (s) | V2V Packets | D\* Lite Replans |
| :--- | :---: | :---: | :---: | :---: |
| Retail Supermarket | 100.0% | 23.07 ± 2.47 | 15.2 ± 2.6 | 341.7 ± 82.8 |
| Clinical Hospital | 92.0% | 27.68 ± 11.35 | 2.8 ± 2.0 | 309.6 ± 127.1 |
| Airport Terminal | 80.0% | 25.29 ± 13.60 | 6.6 ± 14.8 | 897.9 ± 342.9 |

### Table IV — Scalability

**Crowd density** (fixed N_carts = 4): Replan latency scales from 0.18 ms (N_h=2) to 1.23 ms (N_h=30) — always under 2.5% of the 50 ms control tick.

**Fleet size** (fixed N_humans = 10): Makespan scales from 25.67 s (N_c=2) to 41.25 s (N_c=12) with V2V packets scaling predictably (5.0 → 134.9).

---

## 8. Dependencies

| Package | Version | Purpose |
| :--- | :--- | :--- |
| `numpy` | ≥ 1.24 | Numerical computations |
| `scipy` | ≥ 1.10 | Statistical tests (Welch's t-test, CIs) |
| `matplotlib` | ≥ 3.7 | 300 DPI publication figures |
| `python-docx` | ≥ 0.8 | Word document generation |
| MiKTeX / TeX Live | Any | LaTeX PDF compilation |

Install all Python dependencies:
```powershell
pip install numpy scipy matplotlib python-docx
```

---

## 9. License

MIT License. See `LICENSE` for full text.

All simulation data (`experiments/data/*.csv`) and generated figures (`paper/figures/`) are released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) to support open science and reproducibility.

---

*If you use this work in your research, please cite our paper (citation details to be added after acceptance).*
