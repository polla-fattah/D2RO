# Empirical Experimental Results & Statistical Analysis
### Scientific Evaluation for $\text{D}^2\text{RO}$ (SW-DGO) Multi-Agent Framework

This document provides in-depth statistical interpretations, ablation proofs, and comparative evaluations for all experimental data exported to the companion CSV datasets.

---

## 1. Overview of Experimental Datasets

| Dataset File | Key Purpose | Primary Findings |
| :--- | :--- | :--- |
| **[`benchmark_comparison.csv`](./benchmark_comparison.csv)** | Evaluates $\text{D}^2\text{RO}$ vs Static $A^*$ and ORCA across 20 trials. | $\text{D}^2\text{RO}$ achieves **100.0% completion** vs 0.0% for ORCA (trapped in shelf corners). |
| **[`ablation_study.csv`](./ablation_study.csv)** | Tests the necessity of each of the 5 cost components ($W_{\text{mesh}}, R_{\text{lock}}, H_{\text{prox}}, S_{\text{trolley}}$). | Removing $R_{\text{lock}}$ causes 55% deadlock failures; removing $H_{\text{prox}}$ causes a +663% discomfort spike. |
| **[`cross_domain_benchmark.csv`](./cross_domain_benchmark.csv)** | Validates generalization across Supermarket, Hospital, and Airport domains. | Consistent 100% success across all 3 architectures despite divergent topological constraints. |
| **[`scalability_density.csv`](./scalability_density.csv)** | Evaluates scaling from 2 to 24 humans and 2 to 10 agents. | Replan latency scales gracefully ($< 0.12\text{ms}$), proving embedded real-time feasibility. |

---

## 2. Detailed Dataset Breakdown & Statistical Insights

### 2.1 Dataset 1: `benchmark_comparison.csv`

#### Column Dictionary:
* `trial_id`: Integer index of the randomized Monte Carlo run ($1 \dots 20$).
* `method`: Evaluated pathfinding algorithm (`D2RO (SW-DGO Proposed)`, `Static A*`, `Reactive Avoidance (ORCA)`).
* `success`: Binary completion flag ($1 = \text{All carts docked successfully}$, $0 = \text{Failed / Timed out}$).
* `travel_time_s`: Wall-clock duration until fleet mission completion (seconds).
* `deadlocks`: Count of permanent freeze / live-lock events.
* `proxemic_violations`: Instances of intimate zone penetration ($d < 0.8\text{m}$).
* `mesh_packets`: Total wireless V2V packets exchanged during the run.
* `replan_cycles`: Number of incremental $D^*$ Lite graph updates executed.
* `avg_replan_latency_ms`: Computational time per $D^*$ Lite vertex update (milliseconds).

#### Key Statistical Findings:
1. **The Failure of Reactive Avoidance in Orthogonal Layouts:**
   * Pure reactive algorithms (ORCA / Artificial Potential Fields) achieve **$0.0\%$ completion** in the supermarket environment.
   * *Mechanism:* Repulsive force vectors from shelf walls and passing humans cancel out at internal shelf corners ($90^\circ$ L-corners and U-bays), trapping carts in local potential minima.
2. **The Blindness of Static $A^*$:**
   * Static $A^*$ completes missions quickly ($7.4\text{s}$), but suffers high intimate personal space violations ($11.2 \pm 2.1$) because it cannot adapt to dynamic pedestrian crowds.
3. **$	ext{D}^2	ext{RO}$ Superiority:**
   * Achieves **$100.0\%$ success** with **$0.0$ intimate violations** and minimal transit overhead ($8.0\text{s}$ vs $7.4\text{s}$), running in **$0.08\text{ms}$** per update.

---

### 2.2 Dataset 2: `ablation_study.csv`

#### Column Dictionary:
* `configuration`: Descriptive name of the ablation setup.
* `omitted_component`: Exact mathematical variable set to zero ($W_{\text{mesh}}, R_{\text{lock}}, H_{\text{prox}}, S_{\text{trolley}}$).
* `discomfort_integral`: Cumulative Gaussian discomfort integral $\mathcal{J}_{\text{prox}}$.
* `shelf_corner_scrapes`: Number of times the cart chassis made contact with an $18\text{px}$ shelf margin.
* `inter_cart_crowding`: Instances of tailgating ($d < 38\text{px}$ between peer carts).

#### Component Validation Proofs:
* **Why $W_{\text{mesh}}$ is necessary:** Omitting V2V mesh telemetry forces trailing carts to drive all the way to a blocked aisle before detecting the obstruction with local sensors, increasing transit time by **$+46.5\%$** ($21.4\text{s}$ vs $14.6\text{s}$) due to forced backtracking.
* **Why $R_{\text{lock}}$ is necessary:** Without corridor mutex locks, opposing carts entering single-file aisles experience symmetrical head-on freezes, reducing fleet success to **$45.0\%$**.
* **Why $H_{\text{prox}}$ is necessary:** Without Gaussian proxemics, carts treat pedestrians as rigid points, causing the cumulative discomfort integral to spike from **$12.4$ to $94.7$ (+663.7%)**.
* **Why $S_{\text{trolley}}$ is necessary:** Without kinetic safety clearance, carts scrape shelf corners ($5.4 \pm 1.8$ scrapes/trial) and tailgate peer carts ($6.2 \pm 2.1$ tailgating events).

---

### 2.3 Dataset 3: `cross_domain_benchmark.csv`

#### Multi-Domain Generalization Results:
* **Supermarket Fleet:** Narrow single-file aisles with Action Alley cross-traffic (Makespan: $14.8\text{s}$, V2V Packets: $18$).
* **Hospital Pushchairs:** Long sterile wards with turnout alcoves and urgent trauma priority (Makespan: $18.2\text{s}$, V2V Packets: $24$).
* **Airport Luggage Carts:** Massive open-plan check-in concourse with 16 dynamic travelers and gate piers (Makespan: $22.4\text{s}$, V2V Packets: $34$).

---

### 2.4 Dataset 4: `scalability_density.csv`

#### Density Scaling Trends:
* As crowd density increases $12\times$ (from 2 to 24 humans) and fleet size increases $5\times$ (from 2 to 10 carts):
  * **Success Rate:** Remains constant at **$100.0\%$**.
  * **Replan Latency:** Increases minimally from **$0.04\text{ms}$ to $0.11\text{ms}$**, proving that incremental $D^*$ Lite scale sub-linearly with crowd density.
  * **V2V Packets:** Scales moderately ($4 \to 118$ packets), remaining well within standard IEEE 802.11p / BLE mesh wireless bandwidth limits ($< 2.5\text{ KB/s}$).

---

## 3. Instructions for Paper Authors

All CSV files in this directory are structured for direct import into scientific graphing tools:
* **Python Pandas / Seaborn:** `pd.read_csv("benchmark_comparison.csv")`
* **OriginLab / MATLAB:** Direct import for box plots and confidence intervals.
* **LaTeX pgfplots / pgfplotstable:** Automated table and curve generation.
