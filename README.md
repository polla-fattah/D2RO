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

> ℹ️ **Status: round-4 revision. All 11 datasets verified against the current code.**
> 4,650 simulation trials across 11 experiments. Every table, figure and numeric
> claim in the manuscript is generated or verified against the committed raw data
> by a single pipeline; `paper/scripts/verify_manuscript_claims.py` pins 51 exact
> claims and fails the build if the prose and the data disagree.
>
> **Reproduce everything from a clean checkout with one command:**
>
> ```bash
> pip install -r requirements.txt && python run_full_suite.py \
>   && python paper/scripts/analyze_results.py \
>   && python paper/scripts/generate_tables_and_figures.py
> ```
>
> **Submitting or citing?** Run the gate first:
>
> ```bash
> python paper/scripts/release_gate.py
> ```
>
> It refuses to certify a build with a stale dataset, a prose claim that disagrees
> with the data, an unresolved reference, superseded terminology, or a p-value that
> does not appear in `analysis_results.json`. A clean tree produces a clean
> provenance stamp, so `paper/paper.pdf` built locally is submittable once the gate
> passes; the release attachment is the same artefact built from the tag.
>
> Point-by-point replies to the reviewers are in
> [`docs/RESPONSE_TO_REVIEWERS_R4.md`](docs/RESPONSE_TO_REVIEWERS_R4.md).
> Work still open is tracked in [`docs/OUTSTANDING_WORK.md`](docs/OUTSTANDING_WORK.md).

## What is D²RO?

**D²RO** enables fleets of autonomous trolleys — retail shopping carts, clinical hospital pushchairs, airport luggage trolleys — to navigate crowded, human-shared environments **safely, efficiently, and socially-compliantly**.

The framework formalizes **four weighted soft terms subject to one hard
feasibility constraint**, solved incrementally via **D\* Lite**:

```
minimise  C(u,v,t) = w_D · D(u,v)          # Euclidean distance
                   + w_M · W_mesh(u,v,t)    # V2V anticipatory congestion field
                   + w_H · H_prox(v,t)      # Human Gaussian proxemics
                   + w_S · S_trolley(v,t)   # Non-holonomic safety envelope

subject to  e ∉ E_reserved(t)               # directional corridor reservation
```

> Earlier versions of this README described a fifth weight `w_R` multiplying the
> reservation term. That was not faithful to the implementation: a reserved edge has
> infinite cost and an unreserved one contributes zero, so the coefficient had no
> effect in any reachable state. Reservation is a constraint, not a weighted
> objective.

**Key results** across 4,650 Monte Carlo trials (N=100 seed-paired trials per
benchmark condition). The contribution is deliberately bounded rather than
maximised:

| Method | Success | Makespan | Intimate exposure (person-s, median) |
|:-------|:-------:|:--------:|:------------------------------------:|
| D²RO | 99.0% | 47.18 ± 13.40 s | **0.00** |
| Local Social D\* Lite | 100.0% | **39.06 ± 15.12 s** | **0.00** |
| Static A\* (matched controller) | 100.0% | 19.20 s | 6.40 |
| Static A\* | 100.0% | **18.00 s** | 6.40 |
| APF | 100.0% | 34.54 s | 10.18 |

### The question this study is organised around

Distributed coordination layers — peer-to-peer telemetry, reservation protocols — are
widely proposed for multi-robot navigation and almost always evaluated against
baselines that lack *both* the distributed layer *and* any social competence. That
comparison cannot separate the two: a socially weighted distributed planner beats a
socially blind one whether or not the distribution does any work.

So we hold social competence fixed and vary only the coordination architecture, and
ask **when a distributed layer is actually necessary.** The answer is conditional,
and the conditions are the contribution.

**Where the social behaviour comes from.** Socially weighted routing essentially
eliminates intimate-space intrusion (median 0 person-seconds vs 6.40, Holm-adjusted
*p* = 9.4 × 10⁻¹⁶). A 2×2 factorial isolates the cause: with the mesh and the
reservation disabled in every cell and D\* Lite replanning in every cell, enabling
the proxemic cost term alone drops exposure by 6.40 person-seconds
(95% CI [−6.48, −6.31], *p* = 1.5 × 10⁻⁹), at a cost of 19.03 s of makespan.
Reactive yielding adds nothing on top of a social route (0.11 person-s, *p* = 0.59)
and collapses success to 12% on a shortest-path one.

**When the distributed layer is not needed.** Against an equal-competence control —
Local Social D\* Lite, same proxemic cost, no mesh, no reservation — the full system
gains nothing measurable in the broad scenario: identical social compliance
(*p* = 1) while running 8 s slower.

**When it is decisive.** Under the two topologies the mechanisms target, the same
layer carries the outcome: anticipatory rerouting 10.7 s before a blockage enters
sensing range, and corridor success raised from 36% to 88% by cost-projected
diversion. A deployment whose topology produces out-of-sight blockages or contested
single-file corridors should pay for the radio; one that does not should run the
local planner, which is simpler, faster, and equally well behaved around people.

> ORCA and Decentralized Local MAPF are our own implementations and complete 0% of
> missions. They are reported as diagnostics only; no claim depends on them.

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
│   │   ├── run_experiments.py          # All 11 experiments (4,650 rows)
│   │   ├── gui.py                      # Supermarket visual GUI
│   │   ├── hospital_gui.py             # Hospital visual GUI
│   │   └── airport_gui.py              # Airport visual GUI
│   │
│   └── tests/                          # Unit & integration tests (67 tests)
│       ├── test_baselines.py
│       ├── test_dstar_lite.py          # replanner correctness
│       ├── test_dstar_optimality.py    # matches Dijkstra on the same graph
│       ├── test_mesh.py
│       ├── test_mesh_multihop.py
│       ├── test_corridor_lock.py
│       ├── test_hospital.py
│       ├── test_airport.py
│       ├── test_physics_kinematics.py  # non-holonomic motion
│       ├── test_safety_envelope.py
│       ├── test_instrumentation.py     # counters mean what they claim
│       ├── test_metrics_semantics.py   # person-time vs robot-time
│       └── test_provenance_fingerprint.py  # fingerprint is platform-independent
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
│       ├── benchmark_comparison.csv        (700 rows: 7 planners × 100 trials)
│       ├── ablation_study.csv              (700 rows: 7 configs × 100 trials)
│       ├── cross_domain_benchmark.csv      (300 rows: 3 domains × 100 trials)
│       ├── scalability_crowd_density.csv   (600 rows)
│       ├── scalability_fleet_size.csv      (600 rows)
│       ├── mesh_anticipation_experiment.csv (100 rows: Exp A, N=50 paired)
│       ├── corridor_lock_experiment.csv     (100 rows: Exp B, N=50 paired)
│       ├── weight_sensitivity.csv           (510 rows: 17 configs, disjoint seeds)
│       ├── comm_robustness.csv              (480 rows: 4×4 channels)
│       ├── route_yield_factorial.csv        (200 rows: 2×2 attribution design)
│       ├── mesh_degradation.csv             (360 rows: Mech A under 3×3 channels)
│       └── *.provenance.json                (code fingerprint per dataset)
│
├── paper/                              # Manuscript files
│   ├── paper.tex                       # LaTeX source (IEEEtran)
│   ├── paper.pdf                       # Compiled camera-ready PDF
│   ├── references.bib                  # BibTeX bibliography
│   ├── generated/                      # ← ALL TABLES, written by the pipeline
│   │   ├── table_ablation.tex          # never edit by hand; regenerate instead
│   │   ├── table_factorial.tex
│   │   ├── table_factorial_contrasts.tex
│   │   ├── table_cross_domain.tex
│   │   ├── table_mesh_anticipation.tex
│   │   ├── table_corridor_lock.tex
│   │   ├── fig_*.tex                   # float wrappers + captions
│   │   └── commit.tex                  # provenance stamp
│   ├── figures/                        # 300 DPI publication figures (PDF + PNG)
│   │   ├── fig1_benchmark_comparison.* # data-driven
│   │   ├── fig_crowd_density.*         # data-driven
│   │   ├── fig_fleet_size.*            # data-driven
│   │   ├── fig_weight_sensitivity.*    # data-driven (four soft weights)
│   │   ├── fig_degradation.*           # data-driven (paired mesh effect vs channel)
│   │   ├── fig5_supermarket_topology_trajectories.*   # qualitative
│   │   ├── fig6_hospital_topology_trajectories.*      # qualitative
│   │   ├── fig7_airport_topology_trajectories.*       # qualitative
│   │   ├── fig8_social_detour_proxemic_heatmap.*      # qualitative
│   │   ├── fig9_spatiotemporal_alcove_lock_diagram.*  # qualitative
│   │   └── fig10_airport_crowd_density_streamlines.*  # qualitative
│   ├── scripts/                        # Paper build pipeline
│   │   ├── analyze_results.py          # THE statistics pipeline
│   │   ├── generate_tables_and_figures.py  # DATA-DRIVEN: every table + data figures
│   │   ├── verify_manuscript_claims.py # 51 prose claims vs analysis_results.json
│   │   ├── release_gate.py             # refuses to certify a non-reproducible build
│   │   ├── audit_references.py         # Crossref DOI check on every bib entry
│   │   ├── build_latex.py              # Compiles paper.tex → paper.pdf
│   │   ├── build_paper_docx.py         # Generates Word manuscript
│   │   ├── generate_topology_figures.py    # Qualitative: Figs 5–7
│   │   └── generate_heatmaps_and_trajectories.py  # Qualitative: Figs 8–10
│   ├── LICENSE                         # manuscript: all rights reserved
│   └── drafts/                         # Section drafts (Markdown, historical)
│       ├── abstract.md
│       ├── introduction.md
│       ├── Literature_Review.md
│       ├── methodology_and_formulation.md
│       ├── results_and_discussion.md
│       └── conclusion_and_future_work.md
│
├── docs/                               # Research documentation + web demo
│   ├── RESPONSE_TO_REVIEWERS_R4.md     # ← current point-by-point reply
│   ├── OUTSTANDING_WORK.md             # what is knowingly still open
│   ├── REFERENCE_AUDIT.md              # Crossref DOI verification of every entry
│   ├── REVISION_PLAN_R2.md             # round-2 plan (historical)
│   ├── REVISION_PLAN_R3.md             # round-3 plan (historical)
│   ├── email.md, email2.md, comments1.md   # reviewer correspondence, verbatim
│   ├── Metrics_and_Evaluation_Guide.md # Metric definitions & formulas
│   ├── Mathematical_Formalization.md   # Mathematical formalization notes
│   ├── Mathematical_Notes.md
│   ├── Algorithm_Design_Options.md     # Early design exploration notes
│   └── index.html, simulator.js, …     # browser demo (Pyodide; GitHub Pages)
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

### Reproduce all 4,650 simulation trials
```bash
python d2ro/sim/run_experiments.py
```
All 11 CSV files written to `experiments/data/`, each with a `.provenance.json`
stamp recording the fingerprint of the code that produced it. Runtime: ~30 minutes.

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
| [`agent.py`](d2ro/core/agent.py) | `TrolleyAgent` | D²RO agent: D\* Lite + four soft cost terms, V2V mesh, directional reservation |
| [`dstar_lite.py`](d2ro/core/dstar_lite.py) | `DStarLite` | Incremental replanner (0.18–1.23 ms per vertex repair) |
| [`graph.py`](d2ro/core/graph.py) | `TopologicalGraph` | Weighted directed navigation graph with dynamic cost fields |
| [`human.py`](d2ro/core/human.py) | `Human`, `ProxemicsField` | Stochastic pedestrian with 2D asymmetric Gaussian halo |
| [`mesh_network.py`](d2ro/core/mesh_network.py) | `MeshNetwork` | V2V ad-hoc broadcast with exponential time-decay |

### Baseline Algorithms (`d2ro/baselines/`)

| File | Algorithm | Failure Mode |
|:-----|:----------|:-------------|
| [`static_astar.py`](d2ro/baselines/static_astar.py) | Static A\* | Ignores pedestrians → 6.40 person-s exposure, 5 intimate encounters/trial |
| [`artificial_potential_fields.py`](d2ro/baselines/artificial_potential_fields.py) | APF | Completes missions, but reacts only once a pedestrian is close → highest exposure of any completing planner (10.18 person-s) |
| [`reactive_orca.py`](d2ro/baselines/reactive_orca.py) | Reactive ORCA | Infeasible velocity half-planes in narrow aisles → **0.0% success** |
| [`decentralized_local_mapf.py`](d2ro/baselines/decentralized_local_mapf.py) | Decentralized MAPF | **0.0% success**, but traced trials finish within ~1.3 m of the goal — a near-miss against the arrival criterion, not a livelock |

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
- **Arrival tolerance:** 0.84 m (≈ one cart length), identical for every planner
- **Time budget:** T_max = 180 s (benchmark, ablation, cross-domain, crowd density),
  240 s (fleet-size scaling), 120 s (two-cart mechanism experiments) — each set well
  above the longest observed mission for its class, so a timeout means genuine
  non-completion. An earlier revision used 35 s, inherited from an incorrectly scaled
  kinematic model; that budget is what produced the retracted "APF achieves 0%
  success" result, and it is superseded.
- **Statistics:** Wilcoxon signed-rank (paired, continuous) + McNemar exact (success),
  Holm-adjusted; medians [IQR] for skewed metrics, Wilson CIs for proportions

### Experiment overview

| # | Name | Rows | Output |
|:--|:-----|-----:|:-------|
| 1 | Comparative benchmark (7 planners) | 700 | `benchmark_comparison.csv` |
| 2 | Component ablation (7 configurations) | 700 | `ablation_study.csv` |
| 3 | Cross-domain generalisation | 300 | `cross_domain_benchmark.csv` |
| 4A | Crowd-density scalability | 600 | `scalability_crowd_density.csv` |
| 4B | Fleet-size scalability | 600 | `scalability_fleet_size.csv` |
| A | V2V mesh anticipation (controlled) | 100 | `mesh_anticipation_experiment.csv` |
| B | Directional corridor reservation (controlled) | 100 | `corridor_lock_experiment.csv` |
| C | Weight sensitivity (17 configurations, disjoint seeds) | 510 | `weight_sensitivity.csv` |
| D | Communication robustness (4×4 channels) | 480 | `comm_robustness.csv` |
| E | Route × yield factorial | 200 | `route_yield_factorial.csv` |
| F | Mechanism A under degradation (3×3 channels) | 360 | `mesh_degradation.csv` |
| | **Total** | **4,650** | |

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
CSVs; none are typed by hand. `paper/scripts/verify_manuscript_claims.py` fails if the
manuscript prose disagrees with them. See
[`experiments/data/analysis_report.md`](experiments/data/analysis_report.md) for the
full statistical report.

### Table I — Comparative benchmark (N=100 seed-paired trials)

| Algorithm | Success (95% CI) | Makespan, successful (s) | Exposure (person-s, median [IQR]) | Encounters |
|:----------|:----------------:|:------------------------:|:---------------------------------:|:----------:|
| **D²RO (proposed)** | 99.0% [94.6, 99.8] | 47.18 ± 13.40 | 0.00 [0.0, 0.0] | 0 |
| Local Social D\* Lite | 100.0% [96.3, 100.0] | 39.06 ± 15.12 | 0.00 [0.0, 0.0] | 0 |
| Static A\* (matched controller) | 100.0% [96.3, 100.0] | 19.20 ± 0.00 | 6.40 [6.2, 6.6] | 5 |
| Static A\* | 100.0% [96.3, 100.0] | 18.00 ± 0.00 | 6.40 [6.2, 6.5] | 5 |
| APF | 100.0% [96.3, 100.0] | 34.54 ± 0.16 | 10.18 [8.8, 13.8] | 8 |

Exposure is **person-seconds** inside the intimate boundary: the counter increments
once per human per control step, so it is a person-time, not a robot-time. Tests are
Wilcoxon signed-rank (continuous) and McNemar exact (success), Holm-adjusted.

**The headline is bounded on purpose.** D²RO and Local Social D\* Lite achieve
identical social compliance (*p* = 1); D²RO is 8.12 s slower (*p* = 2.0e-5). In this
broad scenario the distributed layer returns nothing measurable — it pays only in
Tables III–IV below.

> ORCA and Decentralized Local MAPF (our implementations) complete 0% of missions and
> are omitted here as diagnostics; no claim depends on them.

### Table II — Proxemic routing vs reactive yielding (N=50 seed-paired trials per cell)

The mesh and the corridor reservation are disabled in **every** cell and D\* Lite
replans in **every** cell, so the routing factor toggles the proxemic cost term and
nothing else.

| Configuration | Success | Makespan (s) | Exposure, median [IQR] |
|:--------------|:-------:|:------------:|:----------------------:|
| `H_prox` OFF, yield OFF | 100.0% | 19.20 ± 0.00 | 6.45 [6.21, 6.60] |
| `H_prox` OFF, yield ON | 12.0% | 173.89 ± 17.01 | 48.00 [38.51, 57.86] |
| `H_prox` ON, yield OFF | 100.0% | 38.23 ± 10.90 | 0.00 [0.00, 0.00] |
| `H_prox` ON, yield ON (**D²RO**) | 100.0% | 38.40 ± 11.04 | 0.00 [0.00, 0.00] |

Pre-specified paired contrasts, tested against zero across matched trials and
Holm-adjusted within outcome family:

| Contrast | Effect (person-s) | 95% CI | *p* |
|:---------|:-----------------:|:------:|:---:|
| `H_prox`, yielding OFF (C − A) | −6.40 | [−6.48, −6.31] | 1.5 × 10⁻⁹ |
| Yielding, `H_prox` ON (D − C) | 0.11 | [0.00, 0.32] | 0.59 |
| Yielding, `H_prox` OFF (B − A) | 42.92 | [37.89, 48.08] | 4.7 × 10⁻²¹ |
| **Interaction** (D−C)−(B−A) | −42.81 | [−47.99, −37.76] | 4.7 × 10⁻²¹ |

Routing produces the social benefit; yielding adds nothing measurable on top of it.
Yielding *without* social routing is actively harmful — an agent that stops for a
pedestrian but has no social gradient to steer around them waits beside the
obstruction until it times out.

### Table III — Component ablation (N=100 trials)

*Routing-cost ablations*

| Configuration | Success | Makespan (s) | Fixture contacts (median [IQR]) |
|:--------------|:-------:|:------------:|:-------------------------------:|
| Full D²RO | 100.0% | 47.38 | 3 [2, 6] |
| w/o V2V mesh | 100.0% | 38.23 | 3 [3, 9] |
| w/o proxemics | 11.0% | 172.05 | 56 [39, 78] |
| reservation constraint lifted | 100.0% | 37.86 | 3 [3, 9] |

*Safety attribution*

| Configuration | Success | Makespan (s) | Fixture contacts (median [IQR]) |
|:--------------|:-------:|:------------:|:-------------------------------:|
| Full D²RO | 100.0% | 47.38 | 3 [2, 6] |
| *w_S* = 0, reactive controller retained | 99.0% | 53.52 | 5 [5, 8] |
| controller off, *w_S* retained | 100.0% | 42.34 | 48 [35, 69] |
| both off | 100.0% | 43.02 | 94 [82, 96] |

The safety term is ablated three ways because one switch used to remove both the
graph cost and the reactive controller. The effect is mostly the **controller**:
3 → 5 contacts when only the cost term goes, 3 → 48 when only the controller does.

### Table IV — Controlled mechanism experiments (N=50 paired trials)

| Experiment | Metric | ON | OFF |
|:-----------|:-------|:--:|:---:|
| A — V2V mesh | Anticipation lead (s) | 10.70 | -0.10 |
| A — V2V mesh | Backtrack (m) | 1.08 | 2.73 |
| B — reservation | Mission success | **88%** | 36% |
| B — reservation | Off-corridor vertices | 2.16 | 0.00 |

The reservation works by **cost-projected diversion**, not mutual exclusion: head-on
encounters are unchanged, deadlocks are zero in both arms, and total wait is 0.03 s.

### Sensitivity and robustness

Success stays within **97–100%** under every perturbation of each of the four soft
weights (×0.5 to ×1.5, disjoint seed set), so the operating point is a plateau, not
a ridge. Reservation is not in the sweep: it is a feasibility constraint, and the
ablation lifts it outright instead.

Under communication degradation the mesh advantage is measured as a **paired**
within-seed effect at each channel condition. Relative to a clean channel it is
statistically unchanged at 10% packet loss (−0.80 s, *p* = 0.16) and falls about
38% at 20% (−4.26 s, 95% CI [−5.73, −2.90], *p* = 6.6 × 10⁻⁶). One-hop latency to
200 ms is detectable but practically negligible (≤ 0.55 s).

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

