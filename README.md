# D²RO — Distributed Dynamic Route Optimization

> **Socially-Weighted Distributed Graph Optimization (SW-DGO) for Autonomous Multi-Agent Service Fleets in Crowded Environments**

**Authors:** Polla Fattah and Sanar Fawzi  
Department of Computer Science and Engineering, Koya University  
📧 polla.fattah@koyauniversity.org · sanar.fawzi@koyauniversity.org  
📄 Manuscript under review

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Code: MIT](https://img.shields.io/badge/Code-MIT-green)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/Data-CC%20BY%204.0-lightblue)](LICENSE-DATA)
[![Paper: All rights reserved](https://img.shields.io/badge/Paper-All%20rights%20reserved-lightgrey)](paper/LICENSE)

---

> ℹ️ **Status: all seven datasets regenerated and verified under the corrected code.**
> The framework was substantially rebuilt following a pre-submission audit. All
> 2,700 trials have been reproduced, the statistics and every manuscript table and
> figure are generated from that data by a single pipeline, and the results,
> discussion and conclusion have been rewritten around the real numbers.
>
> **Read [`docs/OUTSTANDING_WORK.md`](docs/OUTSTANDING_WORK.md) before citing
> anything here.** Work remains — notably a weight-sensitivity study and validation
> of the ORCA baseline against a reference implementation — and that file records
> exactly what is done and what is not.

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

**Key results** across 2,700 Monte Carlo simulation trials (N=100 seed-paired trials
per benchmark condition). The headline is a deliberate trade-off, not a clean sweep:

| Metric | D²RO | Static A\* | APF |
|:-------|:----:|:----------:|:---:|
| Mission success | 99.0% [94.6, 99.8] | 100.0% | 100.0% |
| Makespan (s) | 47.18 ± 13.40 | **18.00 ± 0.00** | 34.54 ± 0.16 |
| Intimate exposure, median [IQR] | **0 [0, 0]** | 128 [123, 131] | 204 [176, 276] |
| Corridor deadlocks | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Replan latency | 0.14–0.32 ms* | n/a | n/a |

\* Replan latency is wall-clock time and is the one metric here that is *not* deterministic — it varies with machine load. Every other value reproduces bit-identically across reruns.

D²RO pays ~2.6× the makespan of the socially blind shortest path to virtually
eliminate intrusion into pedestrians' intimate space, and matches rather than beats
the best baseline on raw success. Cross-domain: 99.0% (supermarket), 100.0%
(hospital), 95.0% (airport).

> Our ORCA and Decentralized Local MAPF implementations complete 0% of missions.
> We report these as properties of *our implementations*, pending validation against
> a reference (e.g. RVO2); no conclusion in the paper depends on them.

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
│   │   ├── run_experiments.py          # Full 2,700-run experimental suite
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
│   │   ├── fig_crowd_density.*
│   │   ├── fig_fleet_size.*
│   │   ├── fig5_supermarket_topology_trajectories.*
│   │   ├── fig6_hospital_topology_trajectories.*
│   │   ├── fig7_airport_topology_trajectories.*
│   │   ├── fig8_social_detour_proxemic_heatmap.*
│   │   ├── fig9_spatiotemporal_alcove_lock_diagram.*
│   │   └── fig10_airport_crowd_density_streamlines.*
│   ├── scripts/                        # Paper build pipeline
│   │   ├── build_latex.py              # Compiles paper.tex → paper.pdf
│   │   ├── build_paper_docx.py         # Generates Word manuscript
│   │   ├── generate_tables_and_figures.py  # DATA-DRIVEN: all tables + Fig 1, scalability
│   │   ├── generate_topology_figures.py    # Qualitative: Figs 5–7
│   │   ├── generate_heatmaps_and_trajectories.py  # Produces Figs 8–10
│   │   └── analyze_results.py          # THE statistics pipeline
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

### Reproduce all 2,700 simulation trials
```bash
python d2ro/sim/run_experiments.py
```
All 7 CSV files written to `experiments/data/`, each with a `.provenance.json` stamp.
Runtime: ~20 minutes.

### Regenerate all figures (300 DPI)
```bash
python paper/scripts/generate_tables_and_figures.py
python paper/scripts/generate_heatmaps_and_trajectories.py
```

### Compute statistics and verify data
```bash
python paper/scripts/analyze_results.py
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
- **Statistics:** Wilcoxon signed-rank (paired, continuous) + McNemar exact (success),
  Holm-adjusted; medians [IQR] for skewed metrics, Wilson CIs for proportions

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
# Trials are seed-paired, so use a paired non-parametric test (as the pipeline does)
stat, p = stats.wilcoxon(d2ro, astar)
print(f"W={stat:.1f}, p={p:.4e}")
```

---

## 6. Building the Paper

All paper build scripts are in [`paper/scripts/`](paper/scripts/).

```
experiments/data/*.csv
        │
        ▼
paper/scripts/analyze_results.py            → analysis_results.json + analysis_report.md
        │
        ▼
paper/scripts/generate_tables_and_figures.py → paper/generated/*.tex + Fig 1, scalability figs
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

All values below are produced by `paper/scripts/analyze_results.py` from the committed
CSVs; none are typed by hand. See [`experiments/data/analysis_report.md`](experiments/data/analysis_report.md)
for the full statistical report including effect sizes and Holm-adjusted p-values.

### Table I — Comparative Benchmark (N=100 seed-paired trials)

| Algorithm | Success (95% CI) | Makespan, successful (s) | Deadlocks | Intimate exposure, median [IQR] |
|:----------|:----------------:|:------------------------:|:---------:|:-------------------------------:|
| **D²RO (Proposed)** | 99.0% [94.6, 99.8] | 47.18 ± 13.40 | 0.00 | **0 [0, 0]** |
| Static A\* | 100.0% [96.3, 100.0] | **18.00 ± 0.00** | 0.00 | 128 [123, 131] |
| APF | 100.0% [96.3, 100.0] | 34.54 ± 0.16 | 0.00 | 204 [176, 276] |
| ORCA (our impl.) | 0.0% [0.0, 3.7] | n/a | 0.00 | 229 [0, 766] |
| Decentralized MAPF (our impl.) | 0.0% [0.0, 3.7] | n/a | 0.00 | 128 [123, 132] |

Exposure is reported as median [IQR] because the distribution is zero-inflated and
right-skewed. Tests are Wilcoxon signed-rank (continuous) and McNemar exact (success),
Holm-adjusted. D²RO vs Static A\*: exposure Δ = −119.2 [−127.6, −107.0], p = 5.1e-16;
makespan Δ = +30.51 s, p = 3.8e-17. Success difference vs A\* is one trial (p = 1).

### Table II — Ablation Study (N=100 trials)

| Metric | Full D²RO | w/o V2V Mesh | w/o Lock | w/o Proxemics | w/o Safety |
|:-------|:---------:|:------------:|:--------:|:-------------:|:----------:|
| Success (%) | 100.0 | 100.0 | 100.0 | **11.0** | 100.0 |
| Makespan (s) | 47.38±13.96 | 38.23±16.88 | 37.86±15.13 | 172.05±26.67 | 43.02±8.84 |
| Discomfort | 0.05±0.13 | 0.09±0.43 | 0.09±0.38 | **13.14±3.57** | 0.05±0.17 |
| Shelf scrapes | 193.05±169.90 | 191.59±182.39 | 186.13±164.45 | 244.86±154.18 | **271.71±84.16** |

The proxemic term is load-bearing. The mesh and lock terms are *not* exercised by this
broad scenario — removing them reduces makespan — which is why the two controlled
mechanism experiments below exist.

### Table III — Cross-Domain (N=100 trials each)

| Domain | Success | Makespan (s) | Mean transit (s) | D\* Lite replans |
|:-------|:-------:|:------------:|:----------------:|:----------------:|
| Retail Supermarket | 99.0% | 49.89 ± 19.94 | 25.90 ± 5.57 | 487.9 ± 151.1 |
| Clinical Hospital | 100.0% | 46.12 ± 10.12 | 31.78 ± 3.89 | 342.5 ± 64.9 |
| Airport Terminal | 95.0% | 74.63 ± 35.71 | 36.84 ± 15.01 | 959.2 ± 359.8 |

### Table IV — Controlled Mechanism Experiments (N=50 paired trials)

| Experiment | Metric | ON | OFF | p (Holm) |
|:-----------|:-------|:--:|:---:|:--------:|
| A — V2V mesh | Anticipation lead (s) | 10.70 ± 4.20 | −0.10 ± 0.04 | 3.8e-9 |
| A — V2V mesh | Backtrack (m) | 1.08 ± 0.68 | 2.73 ± 0.87 | 3.2e-8 |
| B — corridor mutex | Mission success | **88.0%** | 36.0% | 1.5e-4 |
| B — corridor mutex | Corridor occupancy (s) | 40.01 ± 30.87 | 89.41 ± 42.42 | 4.0e-3 |

The corridor mutex works by **cost-projected diversion**, not queueing: head-on
encounters are unchanged (p = 1) and lock wait time is 0.00 s, while agents reroute
around the contested corridor. See `docs/OUTSTANDING_WORK.md` §4.8.

---

## 9. Dependencies

| Package | Version | Purpose |
|:--------|:-------:|:--------|
| `numpy` | ≥ 1.24 | Numerical arrays |
| `scipy` | ≥ 1.10 | Wilcoxon / McNemar tests, confidence intervals |
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

## Licensing

This repository is deliberately licensed in **three separate scopes**. Please read
the one that covers what you intend to use.

| Scope | Licence | File |
|:------|:--------|:-----|
| **Source code** — `d2ro/`, `scripts/`, `paper/scripts/`, `run_full_suite.py` | MIT | [`LICENSE`](LICENSE) |
| **Simulation datasets** — `experiments/data/` | CC BY 4.0 | [`LICENSE-DATA`](LICENSE-DATA) |
| **Manuscript** — everything under `paper/` | **All rights reserved** | [`paper/LICENSE`](paper/LICENSE) |

The code and data are openly licensed precisely so that every number in the paper
can be independently reproduced and checked.

The **manuscript is not openly licensed**. It is unpublished and under review, and
open licences such as CC BY are irrevocable once granted — reserving the paper keeps
the authors free to publish it wherever they choose. You may read, cite and quote it
under normal academic practice; please do not redistribute or republish it.

> **Note for reusers:** the repository-wide badge previously implied MIT covered
> everything. It does not, and never was intended to. Use the table above.

