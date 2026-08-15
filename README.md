# D²RO — Distributed Dynamic Route Optimization

> **Socially-Weighted Distributed Graph Optimization (SW-DGO) for Autonomous Multi-Agent Service Fleets in Crowded Environments**

**Authors:** Polla Fattah and Sanar Fawzi  
Department of Computer Science and Engineering, Koya University  
📧 polla.fattah@koyauniversity.org · sanar.fawzi@koyauniversity.org  
📄 Manuscript under review

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/Data-CC%20BY%204.0-lightblue)](https://creativecommons.org/licenses/by/4.0/)

---

## What is D²RO?

**D²RO** enables fleets of autonomous trolleys — retail shopping carts, clinical hospital pushchairs, airport luggage trolleys — to navigate crowded, human-shared environments **safely, efficiently, and socially-compliantly**.

The framework formalizes a unified 5-component edge traversal cost function solved incrementally via **D\* Lite**:

```
C(u, v, t) = w_D · D(u,v)           # Euclidean distance
           + w_M · W_mesh(u,v,t)     # V2V anticipatory congestion field
           + w_H · H_prox(v,t)       # Human Gaussian proxemics
           + w_R · R_lock(u,v,t)     # Directional corridor mutex lock
           + w_S · S_trolley(v,t)    # Non-holonomic safety envelope
```

**Key results** across 2,500 genuine Monte Carlo simulation trials:

| Metric | D²RO | Best Baseline |
|:-------|:----:|:-------------:|
| Mission Success (Supermarket) | **97.0%** | 100% (Static A\* — but 4.0 violations/trial) |
| Corridor Deadlocks | **0.00 ± 0.00** | 11.00 (MAPF) |
| Intimate Space Violations | **0.59 ± 5.90** | 226.39 (APF) |
| APF Success | 0.0% | — |
| ORCA Success | 0.0% | — |
| Replan Latency | **0.18–1.23 ms** | — |

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Quick Start](#2-quick-start)
3. [Framework Architecture](#3-framework-architecture)
4. [Running the Experiments](#4-running-the-experiments)
5. [Datasets](#5-datasets)
6. [Building the Paper](#6-building-the-paper)
7. [Interactive Demo](#7-interactive-demo)
8. [Key Results](#8-key-results)
9. [Dependencies](#9-dependencies)

---

## 1. Project Structure

```
D2RO/
│
├── d2ro/                               # Core Python package (SW-DGO framework)
│   ├── core/                           # D²RO algorithm internals
│   │   ├── agent.py                    # TrolleyAgent (D* Lite + SW-DGO)
│   │   ├── dstar_lite.py               # D* Lite incremental replanner
│   │   ├── graph.py                    # Weighted navigation graph
│   │   ├── human.py                    # Pedestrian model & proxemics field
│   │   ├── mesh_network.py             # V2V telemetry mesh (exponential decay)
│   │   ├── grid_map.py                 # Occupancy grid helper
│   │   └── units.py                    # Physical constants (px ↔ m, speeds)
│   │
│   ├── baselines/                      # Comparison algorithms
│   │   ├── static_astar.py             # Static A* (no social cost)
│   │   ├── artificial_potential_fields.py  # APF
│   │   ├── reactive_orca.py            # Reactive ORCA (velocity obstacles)
│   │   └── decentralized_local_mapf.py # Local MAPF (token-passing)
│   │
│   ├── environments/                   # Simulation domains
│   │   ├── supermarket.py              # Retail supermarket layout
│   │   ├── hospital.py                 # Clinical hospital + Turnout Alcoves
│   │   └── airport.py                  # Airport terminal concourse
│   │
│   ├── sim/                            # Simulation runners
│   │   ├── run_experiments.py          # Full 2,500-run experimental suite
│   │   ├── gui.py                      # Supermarket visual GUI
│   │   ├── hospital_gui.py             # Hospital visual GUI
│   │   └── airport_gui.py              # Airport visual GUI
│   │
│   └── tests/                          # Unit & integration tests
│       ├── test_baselines.py
│       ├── test_dstar_lite.py
│       ├── test_mesh.py
│       ├── test_corridor_lock.py
│       ├── test_hospital.py
│       └── test_airport.py
│
├── scripts/                            # Ready-to-run demo entry points
│   ├── demo_main.py                    # Full interactive demo (all environments)
│   ├── demo_supermarket.py             # Supermarket scenario
│   ├── demo_hospital.py                # Hospital scenario
│   └── demo_airport.py                 # Airport scenario
│
├── experiments/
│   └── data/                           # ← ALL RAW SIMULATION DATA (CSV)
│       ├── README.md                   # Column descriptions & statistics
│       ├── benchmark_comparison.csv        (500 rows: 5 algorithms × 100 trials)
│       ├── ablation_study.csv              (500 rows: 5 configs × 100 trials)
│       ├── cross_domain_benchmark.csv      (300 rows: 3 domains × 100 trials)
│       ├── scalability_crowd_density.csv   (600 rows: 6 densities × 100 trials)
│       ├── scalability_fleet_size.csv      (600 rows: 6 fleet sizes × 100 trials)
│       ├── mesh_anticipation_experiment.csv (100 rows: Exp A, N=50 controlled)
│       └── corridor_lock_experiment.csv     (100 rows: Exp B, N=50 controlled)
│
├── paper/                              # Manuscript files
│   ├── paper.tex                       # LaTeX source (IEEEtran)
│   ├── paper.pdf                       # Compiled camera-ready PDF
│   ├── references.bib                  # BibTeX bibliography
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
│   ├── scripts/                        # Paper build pipeline
│   │   ├── build_latex.py              # Compiles paper.tex → paper.pdf
│   │   ├── build_paper_docx.py         # Generates Word manuscript
│   │   ├── generate_paper_plots.py     # Produces Figs 1–7 from CSV
│   │   ├── generate_heatmaps_and_trajectories.py  # Produces Figs 8–10
│   │   ├── sync_data_to_manuscript.py  # CSV → statistics → report
│   │   └── verify_and_update_statistics.py
│   └── drafts/                         # Section drafts (Markdown)
│       ├── abstract.md
│       ├── introduction.md
│       ├── methodology_and_formulation.md
│       ├── results_and_discussion.md
│       └── conclusion_and_future_work.md
│
├── docs/                               # Research documentation
│   ├── Response_to_Reviewers.md        # Point-by-point rebuttal (18 items)
│   ├── Journal_Feedback_Round1.md      # First informal journal feedback
│   ├── Journal_Feedback_Round2.md      # Second informal journal feedback
│   ├── Metrics_and_Evaluation_Guide.md # Metric definitions & formulas
│   ├── Algorithm_Design_Options.md     # Early design exploration notes
│   └── Mathematical_Formalization.md   # Mathematical formalization notes
│
├── literature/                         # Reference PDFs
│
├── requirements.txt                    # Python dependencies
├── README.md                           # This file
└── .gitignore
```

---

## 2. Quick Start

### Install dependencies
```bash
pip install -r requirements.txt
```
> Python 3.10+ required. Tested on Python 3.12.7.

### Reproduce all 2,500 simulation trials
```bash
python d2ro/sim/run_experiments.py
```
All 7 CSV files written to `experiments/data/`. Runtime: ~2 minutes on an 8-core machine.

### Regenerate all figures (300 DPI)
```bash
python paper/scripts/generate_paper_plots.py
python paper/scripts/generate_heatmaps_and_trajectories.py
```

### Compute statistics and verify data
```bash
python paper/scripts/sync_data_to_manuscript.py
```

### Compile the LaTeX PDF
```bash
python paper/scripts/build_latex.py
```
Requires MiKTeX or TeX Live.

### Generate Word document
```bash
python paper/scripts/build_paper_docx.py
```

---

## 3. Framework Architecture

### Core Algorithms (`d2ro/core/`)

| File | Class | Role |
|:-----|:------|:-----|
| [`agent.py`](d2ro/core/agent.py) | `TrolleyAgent` | D²RO agent: D\* Lite + all 5 cost terms, V2V mesh, mutex |
| [`dstar_lite.py`](d2ro/core/dstar_lite.py) | `DStarLite` | Incremental replanner (0.18–1.23 ms per vertex repair) |
| [`graph.py`](d2ro/core/graph.py) | `TopologicalGraph` | Weighted directed navigation graph with dynamic cost fields |
| [`human.py`](d2ro/core/human.py) | `Human`, `ProxemicsField` | Stochastic pedestrian with 2D asymmetric Gaussian halo |
| [`mesh_network.py`](d2ro/core/mesh_network.py) | `MeshNetwork` | V2V ad-hoc broadcast with exponential time-decay |

### Baseline Algorithms (`d2ro/baselines/`)

| File | Algorithm | Failure Mode |
|:-----|:----------|:-------------|
| [`static_astar.py`](d2ro/baselines/static_astar.py) | Static A\* | Ignores pedestrians → 4.00 ± 0.00 intimate violations/trial |
| [`artificial_potential_fields.py`](d2ro/baselines/artificial_potential_fields.py) | APF | Force cancellation at 90° corners → **0.0% success** |
| [`reactive_orca.py`](d2ro/baselines/reactive_orca.py) | Reactive ORCA | Infeasible velocity half-planes in narrow aisles → **0.0% success** |
| [`decentralized_local_mapf.py`](d2ro/baselines/decentralized_local_mapf.py) | Decentralized MAPF | Head-on livelocks without global routing → **0.0% success** |

### Environment Domains (`d2ro/environments/`)

| File | Dimensions | Key Features |
|:-----|:----------:|:------------|
| [`supermarket.py`](d2ro/environments/supermarket.py) | 36 m × 24 m | Orthogonal shelf rows, single-file aisles, Action Alley |
| [`hospital.py`](d2ro/environments/hospital.py) | 36 m × 24 m | Turnout Alcoves (priority clearance), ER/OR/ICU zones |
| [`airport.py`](d2ro/environments/airport.py) | 36 m × 24 m | Open concourse, gate piers, security pinch points |

---

## 4. Running the Experiments

All experiments use:
- **Control loop:** Δt = 0.05 s (20 Hz), non-holonomic unicycle kinematics
- **Seeds:** `seed = trial_index + 1000` (fully deterministic and reproducible)
- **Timeout:** T_max = 35.0 s
- **Statistics:** Welch's t-test (two-sided, α = 0.01) + 95% Student-t CIs

### Experiment overview

| # | Name | Trials | Output |
|:--|:-----|-------:|:-------|
| 1 | Comparative Benchmark | 500 | `benchmark_comparison.csv` |
| 2 | Component Ablation | 500 | `ablation_study.csv` |
| 3 | Cross-Domain Generalization | 300 | `cross_domain_benchmark.csv` |
| 4A | Crowd Density Scalability | 600 | `scalability_crowd_density.csv` |
| 4B | Fleet Size Scalability | 600 | `scalability_fleet_size.csv` |
| 5A | V2V Mesh Anticipation (controlled) | 100 | `mesh_anticipation_experiment.csv` |
| 5B | Corridor Mutex Lock (controlled) | 100 | `corridor_lock_experiment.csv` |
| | **Total** | **2,700** | |

### Run individual experiments
```python
from d2ro.sim.run_experiments import ExperimentRunner

runner = ExperimentRunner(output_dir="experiments/data")
runner.run_baseline_comparison(num_trials=100)   # Exp 1
runner.run_ablation_study(num_trials=100)         # Exp 2
runner.run_cross_domain_benchmark(num_trials=100) # Exp 3
runner.run_mesh_anticipation_experiment(50)       # Exp 5A
runner.run_corridor_lock_experiment(50)           # Exp 5B
```

### Run unit tests
```bash
python -m pytest d2ro/tests/ -v
```

---

## 5. Datasets

All raw simulation data is in plain CSV under [`experiments/data/`](experiments/data/). Open directly in Excel, Python (pandas), or R.

### Replicate statistical analysis
```python
import pandas as pd
from scipy import stats

df = pd.read_csv("experiments/data/benchmark_comparison.csv")
d2ro  = df[df["method"] == "D2RO (SW-DGO Proposed)"]["travel_time_s"].values
astar = df[df["method"] == "Static A*"]["travel_time_s"].values
t, p  = stats.ttest_ind(d2ro, astar, equal_var=False)   # Welch's t-test
print(f"t={t:.3f}, p={p:.4e}")
```

---

## 6. Building the Paper

All paper build scripts are in [`paper/scripts/`](paper/scripts/).

```
experiments/data/*.csv
        │
        ▼
paper/scripts/sync_data_to_manuscript.py    → experiments/data/README.md (statistics)
        │
        ▼
paper/scripts/generate_paper_plots.py       → paper/figures/fig1_*.{pdf,png} … fig7_*
paper/scripts/generate_heatmaps_and_trajectories.py → paper/figures/fig8_* … fig10_*
        │
        ▼
paper/scripts/build_latex.py                → paper/paper.pdf   (MiKTeX/TeX Live)
paper/scripts/build_paper_docx.py          → paper.docx
```

---

## 7. Interactive Demo

Run the visual simulation to see D²RO routing in real-time:

```bash
# Full demo with environment selector
python scripts/demo_main.py

# Environment-specific demos
python scripts/demo_supermarket.py
python scripts/demo_hospital.py
python scripts/demo_airport.py
```

---

## 8. Key Results

### Table I — Comparative Benchmark (N=100 trials)

| Algorithm | Success | Makespan (s) | Deadlocks | Intimate Violations |
|:----------|:-------:|:------------:|:---------:|:-------------------:|
| **D²RO (Proposed)** | **97.0%** | **21.47 ± 5.32** | **0.00** | **0.59 ± 5.90** |
| Static A\* | 100.0% | 0.80 ± 0.00 | 0.00 | 4.00 ± 0.00 |
| APF | 0.0% | Timeout | 0.01 | 226.39 ± 69.25 |
| ORCA | 0.0% | Timeout | 2094.37 | 19.37 ± 65.28 |
| Decentralized MAPF | 0.0% | Timeout | 11.00 | 102.44 ± 15.00 |

All Welch's t-tests vs D²RO: **p < 0.001**

### Table II — Ablation Study (N=100 trials)

| Metric | Full D²RO | w/o V2V Mesh | w/o Lock | w/o Proxemics | w/o Safety |
|:-------|:---------:|:------------:|:--------:|:-------------:|:----------:|
| Success (%) | **99.0** | 100.0 | 100.0 | 17.0 | 100.0 |
| Makespan (s) | 22.98±2.21 | 15.24±1.95 | 15.24±1.95 | 32.70±5.67 | 21.26±2.17 |
| Discomfort | **0.63±3.09** | 0.43±1.99 | 0.43±1.99 | 71.56±34.26 | 0.41±2.07 |
| Shelf Scrapes | **0.00** | 0.00 | 0.00 | 0.00 | 77.72±11.94 |

### Table III — Cross-Domain (N=100 trials each)

| Domain | Success | Makespan (s) | D\* Lite Replans |
|:-------|:-------:|:------------:|:----------------:|
| Retail Supermarket | 100.0% | 23.07 ± 2.47 | 341.7 ± 82.8 |
| Clinical Hospital | 92.0% | 27.68 ± 11.35 | 309.6 ± 127.1 |
| Airport Terminal | 80.0% | 25.29 ± 13.60 | 897.9 ± 342.9 |

---

## 9. Dependencies

| Package | Version | Purpose |
|:--------|:-------:|:--------|
| `numpy` | ≥ 1.24 | Numerical arrays |
| `scipy` | ≥ 1.10 | Welch's t-test, confidence intervals |
| `matplotlib` | ≥ 3.7 | 300 DPI publication figures |
| `python-docx` | ≥ 0.8.11 | Word document generation |
| MiKTeX / TeX Live | any | LaTeX PDF compilation |

```bash
pip install -r requirements.txt
```

---

## Citation

If you use this code or data in your research, please cite (details to be updated after acceptance):

```bibtex
@unpublished{fattah2026d2ro,
  title   = {Socially-Weighted Distributed Graph Optimization ({D\textsuperscript{2}RO})
             for Autonomous Multi-Agent Service Fleets in Crowded Environments},
  author  = {Fattah, Polla and Fawzi, Sanar},
  note    = {Manuscript under review},
  year    = {2026}
}
```

## License

Source code: [MIT License](LICENSE)  
Simulation data (`experiments/data/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
