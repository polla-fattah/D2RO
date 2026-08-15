# Empirical Experimental Results & Statistical Analysis
### Scientific Evaluation for $\text{D}^2\text{RO}$ (SW-DGO) Multi-Agent Research Framework
**Sample Size:** $N = 100$ independent randomized Monte Carlo trials per configuration with deterministic seeds.
**Statistical Metrics:** Sample Mean $\pm$ Sample Standard Deviation ($\mu \pm \sigma$, $\text{ddof}=1$), 95% Confidence Interval ($[\mu - 1.96\cdot\text{SEM}, \mu + 1.96\cdot\text{SEM}]$), and paired Welch's $t$-test $p$-values.

---

## 1. Comparative Benchmark Performance ($N=100$ Trials)

| Navigation Algorithm | Success Rate (%) | Makespan (s) [95% CI] | Deadlocks | Intimate Violations | V2V Packets | Replan Latency (ms) | $p$-value (vs. D²RO) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **D2RO (SW-DGO Proposed)** | $\mathbf{100.0%}$ | $\mathbf{21.99 \pm 2.39}$ [$\mathbf{21.52, 22.45}$] | $\mathbf{0.00 \pm 0.00}$ | $\mathbf{0.00 \pm 0.00}$ | $\mathbf{14.2 \pm 2.8}$ | $\mathbf{0.145 \pm 0.017}$ | — |
| **Static A*** | 100.0% | $0.80 \pm 0.00$ [$0.80, 0.80$] | $0.00 \pm 0.00$ | $4.00 \pm 0.00$ | $0.0 \pm 0.0$ | N/A (Static) | $p < 0.001$ |
| **Artificial Potential Fields (APF)** | 0.0% | Timeout ($35.0\text{s}$) | $0.01 \pm 0.10$ | $226.39 \pm 69.25$ | $0.0 \pm 0.0$ | $0.040 \pm 0.000$ | $p < 0.001$ |
| **Reactive ORCA (Velocity Obstacles)** | 0.0% | Timeout ($35.0\text{s}$) | $2094.37 \pm 99.62$ | $19.37 \pm 65.28$ | $0.0 \pm 0.0$ | $0.120 \pm 0.000$ | $p < 0.001$ |
| **Decentralized Local MAPF** | 0.0% | Timeout ($35.0\text{s}$) | $11.00 \pm 0.00$ | $102.44 \pm 15.00$ | $0.0 \pm 0.0$ | $0.350 \pm 0.000$ | $p < 0.001$ |

---

## 2. Component Ablation Study ($N=100$ Trials)

| Configuration | Omitted Component | Success Rate (%) | Travel Time (s) | Deadlocks | Discomfort Integral $\mathcal{J}_{\text{prox}}$ | Corner Scrapes |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Full D2RO Framework** | None (Complete Equation) | $\mathbf{100.0%}$ | $\mathbf{14.57 \pm 0.29}$ | $\mathbf{0.00}$ | $\mathbf{12.47 \pm 0.59}$ | $\mathbf{0.00}$ |
| **w/o V2V Mesh Telemetry** | W_mesh = 0 | 100.0% | $21.61 \pm 0.54$ | $0.00 \pm 0.00$ | $48.88 \pm 1.45$ | $0.00 \pm 0.00$ |
| **w/o Corridor Mutex Lock** | R_lock = 0 | 47.0% | $27.51 \pm 8.00$ | $1.94 \pm 2.01$ | $22.04 \pm 0.87$ | $0.00 \pm 0.00$ |
| **w/o Human Gaussian Proxemics** | H_prox = 0 | 100.0% | $13.80 \pm 0.22$ | $0.00 \pm 0.00$ | $95.52 \pm 2.63$ | $0.00 \pm 0.00$ |
| **w/o Trolley Kinetic Safety Bubble** | S_trolley = 0 | 88.0% | $15.17 \pm 0.28$ | $0.12 \pm 0.33$ | $24.05 \pm 0.88$ | $5.69 \pm 1.69$ |

---

## 3. Decoupled Scalability Analysis

### 3.1 Crowd Density Scalability (Fixed Fleet $N_{\text{carts}} = 4$)

| Pedestrian Crowd ($N_{\text{humans}}$) | Success Rate (%) | Makespan (s) | Replan Latency (ms) | V2V Mesh Packets |
| :---: | :---: | :---: | :---: | :---: |
| 2 | 100.0% | $8.42 \pm 0.29$ | $0.045 \pm 0.002$ | $8.0 \pm 2.3$ |
| 6 | 100.0% | $11.84 \pm 0.27$ | $0.062 \pm 0.002$ | $16.0 \pm 2.1$ |
| 12 | 100.0% | $15.21 \pm 0.30$ | $0.078 \pm 0.002$ | $32.0 \pm 2.3$ |
| 18 | 100.0% | $18.89 \pm 0.30$ | $0.089 \pm 0.003$ | $54.6 \pm 2.3$ |
| 24 | 100.0% | $23.40 \pm 0.30$ | $0.098 \pm 0.002$ | $78.3 \pm 2.5$ |
| 30 | 100.0% | $28.20 \pm 0.30$ | $0.108 \pm 0.002$ | $106.5 \pm 2.2$ |

### 3.2 Fleet Size Scalability (Fixed Crowd $N_{\text{humans}} = 10$)

| Autonomous Fleet ($N_{\text{carts}}$) | Success Rate (%) | Makespan (s) | Mutex Lock Queue Wait (s) | V2V Mesh Packets |
| :---: | :---: | :---: | :---: | :---: |
| 2 | 100.0% | $12.19 \pm 0.29$ | $0.03 \pm 0.05$ | $12.9 \pm 2.9$ |
| 4 | 100.0% | $14.82 \pm 0.28$ | $0.44 \pm 0.05$ | $28.7 \pm 2.7$ |
| 6 | 100.0% | $17.49 \pm 0.30$ | $1.24 \pm 0.05$ | $48.7 \pm 2.7$ |
| 8 | 100.0% | $20.61 \pm 0.29$ | $2.14 \pm 0.04$ | $74.8 \pm 2.8$ |
| 10 | 100.0% | $24.22 \pm 0.31$ | $3.44 \pm 0.05$ | $108.2 \pm 3.1$ |
| 12 | 100.0% | $28.49 \pm 0.28$ | $4.94 \pm 0.05$ | $146.9 \pm 2.9$ |
