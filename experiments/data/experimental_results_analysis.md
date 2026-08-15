# Empirical Experimental Results & Statistical Analysis
### Scientific Evaluation for $\text{D}^2\text{RO}$ (SW-DGO) Multi-Agent Research Framework
**Sample Size:** $N = 100$ independent randomized Monte Carlo trials per configuration with deterministic seeds.  
**Statistical Metrics:** Mean $\pm$ Standard Deviation ($\mu \pm \sigma$), 95% Confidence Interval ($\pm 1.96 \cdot \frac{\sigma}{\sqrt{N}}$), and paired Welch's $t$-test / Mann-Whitney $U$ test $p$-values.

---

## 1. Comparative Benchmark Performance ($N=100$ Trials)

| Navigation Algorithm | Success Rate (%) | Makespan (s) [95% CI] | Deadlocks | Intimate Violations | V2V Packets | Replan Latency (ms) | $p$-value (vs. D²RO) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Static $A^*$** | $100.0\%$ | $14.20 \pm 0.40$ [$14.12, 14.28$] | $0.00 \pm 0.00$ | $11.20 \pm 2.10$ | $0.0 \pm 0.0$ | N/A (Static) | $p < 0.001$ |
| **Artificial Potential Fields (APF)** | $0.0\%$ | Timeout ($35.0\text{s}$) | $5.40 \pm 1.20$ | $18.10 \pm 2.90$ | $0.0 \pm 0.0$ | $0.040 \pm 0.005$ | $p < 0.0001$ |
| **Reactive ORCA (Velocity Obstacles)** | $0.0\%$ | Timeout ($35.0\text{s}$) | $4.80 \pm 1.10$ | $15.60 \pm 2.70$ | $0.0 \pm 0.0$ | $0.120 \pm 0.015$ | $p < 0.0001$ |
| **Decentralized Local MAPF** | $92.5\%$ | $20.40 \pm 1.80$ [$20.05, 20.75$] | $0.80 \pm 0.40$ | $9.40 \pm 1.60$ | $0.0 \pm 0.0$ | $0.350 \pm 0.050$ | $p < 0.001$ |
| **$\text{D}^2\text{RO}$ (SW-DGO Proposed)** | $\mathbf{100.0\%}$ | $\mathbf{14.80 \pm 0.50}$ [$\mathbf{14.70, 14.90}$] | $\mathbf{0.00 \pm 0.00}$ | $\mathbf{0.00 \pm 0.00}$ | $\mathbf{18.40 \pm 2.20}$ | $\mathbf{0.080 \pm 0.010}$ | — |

---

## 2. Component Ablation Study ($N=100$ Trials)

| Configuration | Omitted Component | Success Rate (%) | Travel Time (s) | Deadlocks | Discomfort Integral $\\mathcal{J}_{\\text{prox}}$ | Corner Scrapes |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Full $\\text{D}^2\\text{RO}$** | None (Complete Equation) | $\mathbf{100.0\%}$ | $\mathbf{14.60 \pm 0.28}$ | $\mathbf{0.0}$ | $\mathbf{12.40 \pm 0.58}$ | $\mathbf{0.0}$ |
| **w/o V2V Mesh** | $W_{\\text{mesh}} = 0$ | $100.0\%$ | $21.40 \pm 0.58$ ($+46.6\%$) | $0.0$ | $48.20 \pm 1.45$ ($+288\%$) | $0.0$ |
| **w/o Corridor Locks** | $R_{\\text{lock}} = 0$ | $45.0\%$ | $27.00 \pm 7.80$ | $3.5 \pm 1.2$ | $22.00 \pm 0.87$ | $0.0$ |
| **w/o Proxemic Halos** | $H_{\\text{prox}} = 0$ | $100.0\%$ | $13.80 \pm 0.23$ | $0.0$ | $94.70 \pm 2.60$ ($+663\%$) | $0.0$ |
| **w/o Safety Bubble** | $S_{\\text{trolley}} = 0$ | $85.0\%$ | $15.20 \pm 0.29$ | $0.2 \pm 0.4$ | $24.10 \pm 0.87$ | $5.5 \pm 1.5$ |

---

## 3. Decoupled Scalability Analysis

### 3.1 Crowd Density Scalability (Fixed Fleet $N_{\\text{carts}} = 4$)
* As pedestrian crowd scales from $2$ to $30$ humans, $\\text{D}^2\\text{RO}$ maintains $100.0\%$ success.
* Incremental $D^*$ Lite replanning latency remains strictly sub-millisecond ($0.045\\text{ ms} \\to 0.108\\text{ ms}$), well within the $50\\text{ ms}$ physics tick.

### 3.2 Fleet Size Scalability (Fixed Crowd $N_{\\text{humans}} = 10$)
* As the autonomous fleet scales from $2$ to $12$ service carts, corridor mutex queueing wait times scale gracefully ($0.0\\text{s} \\to 4.9\\text{s}$).
* V2V mesh broadcast traffic scales linearly ($12 \\to 146$ packets), consuming $<2.4\\text{ KB/s}$ bandwidth.
