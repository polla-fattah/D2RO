# Socially-Weighted Distributed Graph Optimization ($\text{D}^2\text{RO}$) for Autonomous Multi-Agent Service Fleets in Crowded Environments

**Authors:** Polla Fattah, et al.  
**Target Submission:** *IEEE Transactions on Robotics / Autonomous Robots (Special Issue on Multi-Agent Social Navigation)*

---

## 1. Introduction & Literature Review

The continuous deployment of autonomous mobile service fleets—such as retail shopping trolleys (*Int-Cart*), hospital patient pushchairs, and airport luggage carts—in shared human-populated environments represents a fundamental frontier in robotics. Navigating these environments requires addressing multiple intersecting challenges: Multi-Agent Path Finding (MAPF), dynamic graph replanning, continuous local collision avoidance, ad-hoc wireless communication, and human-aware social proxemics.

```mermaid
graph TD
    subgraph Literature["Foundations & Literature Landscape"]
        L1["1. Lifelong MAPF & MAPD<br/>(Stern et al., 2019; Ma et al., 2017)"]
        L2["2. Incremental Graph Repair<br/>(Koenig & Likhachev, 2002; Al-Mutib et al., 2012)"]
        L3["3. Velocity Obstacles & ORCA<br/>(Van den Berg et al., 2008; Dergachev & Yakovlev, 2021)"]
        L4["4. Mobile Ad-Hoc Networks (MANET)<br/>(Gielis et al., 2022; Slyusar & Kulich, 2016)"]
        L5["5. Social Proxemics & Footprints<br/>(HA-VLN Authors, 2024; Mohamad Azlan et al., 2024)"]
    end

    subgraph IdentifiedGaps["Critical Research Gaps Identified"]
        G1["Lack of V2V Mesh Telemetry in MAPF"]
        G2["Symmetrical Live-Locks in Narrow Corridors"]
        G3["Omission of Physical Chassis Sweeping Margins & Tailgating"]
        G4["Single-Domain Evaluation Overfitting"]
    end

    Literature --> IdentifiedGaps
    IdentifiedGaps --> D2RO["Proposed D²RO / SW-DGO Framework"]
```

### 1.1 Decentralized and Lifelong Multi-Agent Path Finding (MAPF)
Classical MAPF formalizes the collision-free routing of discrete agents on graph topologies (*Stern et al., 2019*). In lifelong multi-agent pickup and delivery (MAPD) (*Ma et al., 2017*), agents dynamically receive transport assignments without resting. To overcome the communication bottlenecks and single-point failure risks of centralized servers, recent research has investigated decentralized solvers, including priority swapping (*Dergachev & Yakovlev, 2024*), automated negotiation (*Keskin et al., 2024*), and learning-based policies such as PRIMAL (*Sartoretti et al., 2019*) and Learn-to-Follow (*Skrynnik et al., 2024*). However, learning-based policies suffer from out-of-distribution failure when encountering sudden physical corridor blockages, demonstrating the continued necessity of provably complete heuristic search.

### 1.2 Dynamic Incremental Replanning in Stochastic Environments
In retail and hospital corridors, topological traversal costs shift dynamically as shoppers congregate or medical carts block aisles. Full graph recalculations from scratch ($O(|V| \log |V|)$) are computationally prohibitive for decentralized embedded microcontrollers. Koenig and Likhachev (2002) resolved this with $D^*$ Lite, an incremental heuristic search algorithm that re-evaluates only inconsistent vertices ($g(s) \neq rhs(s)$) affected by dynamic edge-cost shifts. Al-Mutib et al. (2012) and Wagner & Choset (2011) demonstrated the power of dynamic dimensionality reduction and incremental repair in multi-agent routing.

### 1.3 Kinematic Coordination, Velocity Obstacles, and Corridor Deadlocks
In continuous space, Optimal Reciprocal Collision Avoidance (ORCA) (*Van den Berg et al., 2008*) calculates collision-free half-planes in velocity space without explicit communication. However, standard ORCA suffers from **symmetrical live-locks and local minima traps** in narrow, orthogonal corridors where agents cannot physically pass one another. Dergachev and Yakovlev (2021) addressed this by combining continuous reciprocal avoidance with locally confined MAPF fallback.

### 1.4 Ad-Hoc Multi-Robot Mesh Communication
Transitioning to fully decentralized fleets requires peer-to-peer data exchange without centralized infrastructure (*Gielis et al., 2022*). Slyusar and Kulich (2016) and Edwige (2024) evaluated mobile ad-hoc networks (MANET) and Swarm SLAM, proving that decentralized agents can effectively merge localized spatial state representations over multi-hop wireless meshes.

### 1.5 Human Proxemics and Vehicle Clearance Margins
Social navigation guidelines (*HA-VLN 2.0, 2024*) dictate that robots must respect psychological personal space boundaries rather than treating pedestrians as rigid cylindrical obstacles. Crucially, recent mechatronic deployments of autonomous carts (*Mohamad Azlan et al., 2024 - Int-Cart*) reveal that real non-holonomic vehicles require **physical sweeping clearance margins**: turning sharp $90^\circ$ corners can cause outer chassis boundaries to scrape shelf fixtures, and trailing carts require kinetic following buffers to eliminate tailgating.

### 1.6 Identified Research Gaps & Contributions of $\text{D}^2\text{RO}$
1. **The Remote Information Isolation Gap:** Existing decentralized MAPF planners rely on myopic, on-board line-of-sight sensing. Trailing carts drive directly into blocked corridors before discovering obstructions, requiring costly backtracking.
2. **The Symmetrical Corridor Deadlock Gap:** Reactive continuous algorithms (ORCA, APF) fail completely ($0.0\%$ success) in narrow single-file corridors due to opposing velocity cancellation.
3. **The Chassis Sweeping Clearance Gap:** Standard graph formulations assume point agents, leading to wall scraping during non-holonomic corner execution.
4. **The Multi-Domain Generalization Gap:** Existing literature overfits to single benchmark layouts. A robust framework must generalize across retail aisles, clinical hospital wards with turnout alcoves, and massive open airport concourses.

The proposed **$\text{D}^2\text{RO}$ (Decentralized Dynamic Route Optimization)** framework bridges all four gaps.

---

## 2. Mathematical Formulation & System Architecture

### 2.1 Environmental Topology & Non-Holonomic Kinematics
The planar workspace $\mathcal{W} \subset \mathbb{R}^2$ is embedded as a directed graph $G = (V, E)$. The fleet consists of $N$ autonomous agents $\mathcal{A} = \{a_1, \dots, a_N\}$ governed by unicycle non-holonomic kinematics:

$$\mathbf{x}_i(t) = \begin{bmatrix} x_i(t) \\ y_i(t) \\ \theta_i(t) \\ v_i(t) \end{bmatrix}, \quad \dot{\mathbf{x}}_i(t) = \begin{bmatrix} v_i(t) \cos \theta_i(t) \\ v_i(t) \sin \theta_i(t) \\ \omega_i(t) \\ a_i(t) \end{bmatrix}$$

subject to linear speed $v_i(t) \in [0, v_{\max}]$, angular steering rate $\omega_i(t) \in [-\omega_{\max}, \omega_{\max}]$, and linear acceleration $a_i(t) \in [-a_{\max}, a_{\max}]$.

### 2.2 The Complete 5-Component SW-DGO Traversal Cost Function
The traversal cost $C(u, v, t)$ across any directed edge $(u, v) \in E$ at time $t$ is evaluated as:

$$\boxed{C(u, v, t) = D(u, v) + W_{\text{mesh}}(u, v, t) + H_{\text{prox}}(v, t) + R_{\text{lock}}(u, v, t) + S_{\text{trolley}}(v, t)}$$

```mermaid
flowchart TD
    Cost["Composite Traversal Cost: C(u, v, t)"]
    D["1. Kinematic Metric: D(u, v)"]
    W["2. V2V Mesh Decay: W_mesh(u, v, t)"]
    H["3. Gaussian Proxemics: H_prox(v, t)"]
    R["4. Corridor Mutex Lock: R_lock(u, v, t)"]
    S["5. Kinetic Safety Bubble: S_trolley(v, t)"]

    Cost --> D & W & H & R & S
```

#### 1. Baseline Kinematic Distance: $D(u, v)$
$$D(u, v) = \|\mathbf{p}_u - \mathbf{p}_v\|_2 + \alpha_{\text{turn}} \cdot |\Delta \theta(u, v)|$$
Penalizes Euclidean distance and angular steering alignment $\Delta \theta(u, v) = |\text{atan2}(y_v - y_u, x_v - x_u) - \theta_i|$.

#### 2. Spatiotemporal V2V Mesh Congestion Penalty: $W_{\text{mesh}}(u, v, t)$
$$W_{\text{mesh}}(u, v, t) = \sum_{k \in \mathcal{M}} \gamma^h \cdot W_0 \cdot \exp\left( -\lambda_{\text{decay}} (t - t_k) \right)$$
Event-driven broadcast of `CONGESTION_ALERT` packets across wireless radius $R_{\text{mesh}} = 350\text{px}$ with hop discount $\gamma \in (0, 1]$ and temporal decay rate $\lambda_{\text{decay}} = 2.0\text{ s}^{-1}$.

#### 3. Continuous 2D Anisotropic Gaussian Proxemics: $H_{\text{prox}}(v, t)$
$$H_{\text{prox}}(v, t) = \sum_{j=1}^{M(t)} A_j \cdot \exp \left( -\frac{1}{2} (\mathbf{p}_v - \mathbf{p}_j^h)^T \mathbf{R}(\phi_j^h) \mathbf{\Sigma}_j^{-1} \mathbf{R}(\phi_j^h)^T (\mathbf{p}_v - \mathbf{p}_j^h) \right)$$
Evaluates psychological personal space discomfort ($A_j = 50.0$, $\sigma_{\text{front}} = 1.8\text{m}$, $\sigma_{\text{side}} = 1.2\text{m}$).

#### 4. Spatiotemporal Directional Corridor Mutex Lock: $R_{\text{lock}}(u, v, t)$
$$R_{\text{lock}}(u, v, t) = \begin{cases} \infty, & \text{if opposing edge } (v, u) \text{ is locked by another agent at time } t \\ 0, & \text{otherwise} \end{cases}$$
Enforces strict single-agent exclusivity in narrow corridors ($w_{\text{aisle}} < 2 r_{\text{trolley}}$) to eliminate head-on live-locks.

#### 5. Trolley Kinetic Safety Clearance Envelope: $S_{\text{trolley}}(v, t)$
$$S_{\text{trolley}}(\mathbf{p}, t) = \sum_{j \neq i} A_{\text{trolley}} \cdot \exp\left( -\frac{\|\mathbf{p} - \mathbf{p}_j(t)\|^2}{2\sigma_{\text{trolley}}^2} \right)$$
Enforces safe following distances (anti-tailgating) and inflates static fixture boundaries by an $18\text{px}$ margin to prevent corner clipping during non-holonomic turns.

---

## 3. Incremental Graph Repair Engine ($D^*$ Lite Integration)

Each agent maintains distance estimates $g(s)$ and one-step lookahead values $rhs(s)$:

$$rhs(s) = \begin{cases} 0 & \text{if } s = s_{\text{goal}} \\ \min_{s' \in \text{Succ}(s)} \left( C(s, s', t) + g(s') \right) & \text{otherwise} \end{cases}$$

Inconsistent vertices are ordered in priority queue $U$ using key vector $\mathbf{k}(s) = [k_1(s), k_2(s)]^T$:

$$\begin{aligned}
k_1(s) &= \min(g(s), rhs(s)) + \|\mathbf{p}_{s_{\text{start}}} - \mathbf{p}_s\|_2 + k_m \\
k_2(s) &= \min(g(s), rhs(s))
\end{aligned}$$

where key modifier $k_m \leftarrow k_m + \|\mathbf{p}_{s_{\text{last}}} - \mathbf{p}_{s_{\text{start}}}\|_2$ maintains queue correctness as the vehicle moves, reducing replan complexity to $O(k \log |V|)$ where $k \ll |V|$.

---

## 4. Multi-Domain Generalization & Topologies

The framework is validated across three divergent real-world architectural environments:

```mermaid
graph LR
    subgraph D1["1. Retail Supermarket (Fig. 5)"]
        S1["Single-File Aisles 1-6"]
        S2["Central Action Alley"]
        S3["Multi-Bay Cart Depots"]
    end

    subgraph D2["2. Clinical Hospital (Fig. 6)"]
        H1["Emergency Trauma (ER)"]
        H2["Sterile OR / MRI Suite"]
        H3["Turnout Alcove Passing Bays"]
    end

    subgraph D3["3. Airport Terminal (Fig. 7)"]
        A1["Massive Open Concourse"]
        A2["Security Screening Lane"]
        A3["Gate Piers A1-A2 & B1-B2"]
    end
```

### 4.1 Turnout Alcove Kinematics (Hospital Pushchair Domain)
In single-file clinical corridors, emergency transport vehicles ($P_1$) receive absolute right-of-way. When an emergency broadcast is received, routine pushchairs ($P_2$) execute an alcove transition maneuver:

$$\pi_{\text{yield}} = \arg\min_{v \in V_{\text{alcove}}} \|\mathbf{p}_{\text{agent}} - \mathbf{p}_v\|_2$$

The yielding pushchair pulls into the alcove bay $v_{\text{alcove}}$ and pauses until $P_1$ clears the corridor, resuming transit without blocking the clinical artery.

---

## 5. Experimental Results & Quantitative Discussion

```text
Associated Datasets (in experiments/data/):
• benchmark_comparison.csv       • ablation_study.csv
• cross_domain_benchmark.csv     • scalability_density.csv
```

```latex
\begin{table*}[t]
\centering
\caption{Quantitative Performance Benchmark over 20 Randomized Monte Carlo Trials (Mean $\pm$ Std. Dev.).}
\label{tab:benchmark_results}
\begin{tabular}{lcccccc}
\hline
\textbf{Algorithm} & \textbf{Success Rate (\%)} & \textbf{Makespan (s)} & \textbf{Deadlocks} & \textbf{Intimate Violations} & \textbf{Mesh Packets} & \textbf{Avg Replan (ms)} \\
\hline
Static $A^*$ & 100.0\% & 14.2 \pm 0.4 & 0.0 & 11.2 \pm 2.1 & 0.0 & \text{N/A (Static)} \\
Reactive Avoidance (ORCA) & 0.0\% & \text{Timeout (35s)} & 5.1 \pm 1.4 & 16.8 \pm 3.2 & 0.0 & 0.12 \pm 0.02 \\
\textbf{D$^2$RO (SW-DGO Proposed)} & \textbf{100.0\%} & \textbf{14.8 \pm 0.5} & \textbf{0.0} & \textbf{0.0 \pm 0.0} & \textbf{18.4 \pm 2.2} & \textbf{0.08 \pm 0.01} \\
\hline
\end{tabular}
\end{table*}
```

### 5.1 Analysis of Comparative Benchmark (Figure 1)
* **The Failure of Reactive Avoidance in Orthogonal Fixtures:** As shown in **Figure 1(a)**, reactive potential fields and ORCA achieve **$0.0\%$ success** in the supermarket environment. Repulsive vectors from shelf walls and passing pedestrians cancel out at internal $90^\circ$ corners, trapping carts in permanent local minima.
* **Social Compliance:** Static $A^*$ completes paths quickly but causes **$11.2 \pm 2.1$ intimate personal space violations** (**Fig. 1(c)**). In contrast, $\text{D}^2\text{RO}$ achieves **$0.0$ violations** while incurring negligible transit overhead ($14.8\text{s}$ vs $14.2\text{s}$).

### 5.2 Component Ablation Insights (Figure 2)
* **Impact of $W_{\text{mesh}}$:** Omitting V2V mesh telemetry forces trailing carts to discover obstructions with on-board sensors only at the bottleneck, increasing fleet makespan by **$+46.5\%$** ($21.4\text{s}$ vs $14.6\text{s}$) due to forced backtracking.
* **Impact of $R_{\text{lock}}$:** Removing the corridor mutex lock reduces mission success to **$45.0\%$**, as opposing carts lock heads in single-file aisles (**Fig. 2(b)**).
* **Impact of $H_{\text{prox}}$:** Disabling Gaussian proxemics causes the cumulative discomfort integral to spike by **$+663.7\%$** ($12.4 \to 94.7$, **Fig. 2(a)**).
* **Impact of $S_{\text{trolley}}$:** Disabling vehicle safety envelopes leads to **$5.4 \pm 1.8$ shelf corner scrapes** and frequent tailgating.

### 5.3 Scalability & Computational Efficiency (Figure 4)
As crowd density scales $12\times$ (from 2 to 24 pedestrians) and fleet size scales $5\times$ (from 2 to 10 carts), incremental $D^*$ Lite vertex repair latency increases sub-linearly from **$0.04\text{ms}$ to $0.11\text{ms}$** (**Fig. 4**), maintaining full 60 FPS real-time guarantees on low-cost embedded hardware.

---

## 6. Conclusion

The $\text{D}^2\text{RO}$ framework provides an integrated, socially compliant, and provably deadlock-free routing architecture for autonomous multi-agent fleets operating in human-dense environments. By coupling incremental heuristic search ($D^*$ Lite) with event-driven V2V mesh telemetry, spatiotemporal corridor mutex locks, continuous Gaussian proxemics, and vehicle safety envelopes, $\text{D}^2\text{RO}$ eliminates the local minima and live-lock failure modes of prior methods while maintaining sub-millisecond computational execution across retail, healthcare, and transit architectures.
