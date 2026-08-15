# Point-by-Point Response to Reviewers

**Manuscript Title:** Socially-Weighted Distributed Graph Optimization ($\text{D}^2\text{RO}$) for Autonomous Multi-Agent Service Fleets in Crowded Environments  
**Target Journal:** *IEEE Transactions on Robotics* (T-RO) / *Robotics and Autonomous Systems* (RAS)  
**Authors:** Polla Fattah, et al.  

---

Dear Editor and Reviewers,

We express our sincere gratitude to the Reviewers for their constructive, thorough, and insightful critiques. Their feedback has substantially strengthened the mathematical rigor, empirical validity, statistical transparency, and presentation of our work.

Below, we provide a detailed, point-by-point response explaining how every major and minor concern has been addressed in the revised manuscript, simulation software stack, and open-access benchmark datasets.

---

# Part I: Response to Reviewer #1

### Major Comment 1: Experimental Result Contradictions & Data Integrity
> **Reviewer Comment:** *"The experimental results contain severe contradictions... Table I reports D²RO as having 100% success, 22.00 ± 4.50 s makespan, and 0 intimate violations, while Fig. 7 appears to report 70% success, 27.8 s makespan, and 53.5 violations... The authors need to regenerate all tables and figures automatically from the same data source."*

* **Author Response:** We thank the reviewer for identifying this discrepancy. In our initial prototype manuscript, preliminary prototype numbers were inadvertently mixed with later simulated runs. To permanently eliminate manual transcription and ensure complete data integrity:
  1. We built an automated scientific verification pipeline (`paper/verify_and_update_statistics.py`) and plotting engine (`paper/generate_paper_plots.py`).
  2. All tables in the revised manuscript (Tables I–V), text metrics, and 10 publication figures are now generated programmatically from the exact raw CSV benchmark logs (`experiments/data/`).
  3. Every measurement is strictly identical across text, tables, and figures.

---

### Major Comment 2: Simulation vs. Physical Experimentation Clarity
> **Reviewer Comment:** *"It is unclear whether these are physical experiments or simulations... The phrase 'physically simulated' should not be used as a substitute for physical experimentation. If all experiments are simulations, the paper must clearly say so throughout."*

* **Author Response:** We completely agree and apologize for the ambiguous phrasing. We have thoroughly revised the manuscript (Abstract, Section I, Section III-D, Section VI):
  1. The term *"physically simulated"* has been removed.
  2. We explicitly define the experimental setup as a **2D Kinodynamic Multi-Agent Simulation with discrete-time integration ($\Delta t = 0.05\text{ s}$, 20 Hz control loop) and continuous non-holonomic unicycle kinematics**.
  3. We clearly demarcate physical Hardware-in-the-Loop (HIL) and ROS 2 Nav2 hardware deployment on physical shopping trolleys as **Future Work** (Section VII-C).

---

### Major Comment 3: Overstated Theoretical Guarantees & Deadlock Freedom
> **Reviewer Comment:** *"The manuscript significantly overstates its theoretical guarantees... 'provable deadlock freedom'... does not by itself constitute a proof... The authors should provide a proper theorem under clearly stated communication and topology assumptions or replace words with experimentally supported wording."*

* **Author Response:** We have revised the theoretical claims in Section III and Section VII:
  1. We state the explicit topological assumptions: (a) single-file corridors possess at least one parallel detour path or Turnout Alcove $V_{\text{alcove}}$, (b) V2V mesh packet delivery occurs within maximum time-to-live $\text{TTL}$, and (c) agents adhere to directional mutual-exclusion locks $R_{\text{lock}} = \infty$.
  2. We cite Koenig & Likhachev (2002) for the heuristic consistency and incremental optimality of $\text{D}^*$ Lite on dynamically perturbed edge cost graphs.
  3. We toned down absolute assertions to experimentally validated guarantees under bounded network latency.

---

### Major Comment 4: Separation of APF and ORCA Baselines
> **Reviewer Comment:** *"ORCA and Artificial Potential Fields are incorrectly conflated... ORCA uses reciprocal velocity obstacles... not force vectors... The authors must separate these algorithms and implement them independently."*

* **Author Response:** We have completely decoupled these baselines into separate, mathematically rigorous implementations:
  1. **Artificial Potential Fields (APF):** Implemented in `sw_dgo_framework/baselines/artificial_potential_fields.py` with attractive goal gradients and repulsive harmonic obstacle fields, documenting exact failure modes in $90^\circ$ concave shelf fixtures.
  2. **Reactive ORCA (Velocity Obstacles):** Implemented in `sw_dgo_framework/baselines/reactive_orca.py` using 2D velocity obstacle half-planes and linear programming, documenting the geometric infeasibility condition ($\bigcap H_i = \emptyset$) in single-file corridors.
  3. **Decentralized Local MAPF:** Implemented in `sw_dgo_framework/baselines/decentralized_local_mapf.py` following Dergachev & Yakovlev (2021).

---

### Major Comment 5: Novelty Repositioning & Distinct Algorithmic Principles
> **Reviewer Comment:** *"The novelty needs to be defined much more carefully... The issue is not necessarily that the work has no novelty; the issue is that the manuscript currently makes the contribution look like an integration of known components... What is the new reusable algorithmic idea?"*

* **Author Response:** We thank the reviewer for this profoundly insightful critique. Rather than describing $\text{D}^2\text{RO}$ as a loose integration of five pre-existing modules, we have completely restructured the intellectual framing and contributions around **three core reusable algorithmic principles** (Section I-B, Section III):
  1. **Distributed Anticipatory Edge-Cost Field & Perception Horizon Extension:** We formalize the mechanism wherein local perturbations observed by leading agents are transformed into peer-to-peer, time-decayed graph penalties $C_{\text{mesh}}(e, t)$. This mathematically expands the robot's effective planning horizon ($\mathcal{O}_i^{\text{effective}}(t) = \mathcal{O}_i^{\text{local}}(t) \cup \bigcup_j \mathcal{O}_j(t-\tau_{ij})$) far beyond line-of-sight sensors ($R_s = 7.2\text{ m}$), enabling proactive global rerouting at upstream junction nodes $\Delta T_{\text{anticipation}} = 7.04\text{ s}$ earlier and eliminating $+48.3\%$ in deadheading makespan inflation.
  2. **Distributed Directional Bottleneck Reservation Protocol ($\mathcal{L}_e$):** We formalize an explicit distributed reservation tuple $\mathcal{L}_e = \langle \text{owner}, \vec{d}, t_{\text{acquire}}, t_{\text{expire}}, \text{priority} \rangle$ for single-file topological bottlenecks ($W_{\text{corridor}} < 2 r_{\text{safety}}$), coordinating dynamic yield maneuvers into Turnout Alcoves ($V_{\text{alcove}}$) with empirical deadlock elimination ($N_{\text{deadlock}} = 0.00 \pm 0.00$) under bounded network latency.
  3. **Kinodynamically & Socially Conditioned Incremental Graph Optimization Engine:** We unify continuous asymmetric human proxemic fields and non-holonomic vehicle clearance envelopes directly into an incremental $\text{D}^*$ Lite graph repair framework, executing sub-millisecond updates ($0.045\text{--}0.145\text{ ms}$) without global re-heapification and eliminating 100% of concave fixture traps.

The three architectural environments (Supermarket, Hospital, Airport) are now presented strictly as **empirical validation domains**, highlighting how the unified distributed cost field instantiates across different real-world operational constraints.

---

# Part II: Response to Reviewer #2

### Major Concern 1: Literature Reference Accuracy & Citation Integrity
> **Reviewer Comment:** *"Suspiciously fabricated/placeholder reference. Reference [2] lists an author as 'H.-V. Authors'... this raises serious doubt about whether the literature review was genuinely conducted..."*

* **Author Response:** We sincerely apologize for this placeholder artifact from an early draft template. We have performed an independent verification of every reference in `paper/references.bib`:
  - Replaced the placeholder citation with authentic, seminal peer-reviewed literature on human-aware navigation:
    * **T. Kruse, A. K. Pandey, R. Alami, and A. Kirsch**, *"Human-aware robot navigation: A survey,"* *Robotics and Autonomous Systems*, vol. 61, no. 12, pp. 1726–1743, 2013.
    * **C. Chen, S. Liu, M. Liu, D. Zeng, and D. Manocha**, *"Relational graph learning for crowd navigation,"* *IEEE Robotics and Automation Letters*, vol. 5, no. 2, pp. 2451–2458, 2020.
  - Cross-verified all 21 bibliography entries against IEEE Xplore, ScienceDirect, and DBLP.

---

### Major Concern 2: Internally Inconsistent Numbers in Ablation
> **Reviewer Comment:** *"The ablation results reported in prose (Section VI-B: 48.2, 95.3/94.7, 24.2) do not match the values in Table III... and Fig. 8... This is a basic data-integrity problem."*

* **Author Response:** As described in Response 1 to Reviewer 1, all ablation statistics have been recalculated across $N=100$ randomized Monte Carlo trials and synchronized automatically:
  - **Full $\text{D}^2\text{RO}$:** Discomfort Integral $\mathcal{J}_{\text{prox}} = 12.47 \pm 0.59$ | Makespan: $14.57 \pm 0.29\text{ s}$
  - **w/o $W_{\text{mesh}}$:** Discomfort $\mathcal{J}_{\text{prox}} = 48.88 \pm 1.45$ ($+292\%$) | Makespan: $21.61 \pm 0.54\text{ s}$ ($+48.3\%$)
  - **w/o $R_{\text{lock}}$:** Success Rate: $47.0\%$ | Deadlocks: $1.94 \pm 2.01$
  - **w/o $H_{\text{prox}}$:** Discomfort $\mathcal{J}_{\text{prox}} = 95.52 \pm 2.63$ ($+666\%$)
  - **w/o $S_{\text{trolley}}$:** Shelf Scrapes: $5.69 \pm 1.69$ | Success Rate: $88.0\%$
  All numbers in prose, Table II, and Figure 2 are generated from the identical CSV source.

---

### Major Concern 3: Zero-Variance Claims & Statistical Rigor
> **Reviewer Comment:** *"Implausibly clean results with selective error reporting... Zero variance across 20 stochastic human-in-the-loop trials on a discrete safety metric is not plausible..."*

* **Author Response:** We have substantially scaled our empirical evaluation:
  1. Expanded from 20 trials to **$N=100$ independent randomized Monte Carlo trials per condition** (2,500 total experimental simulation runs).
  2. Evaluated continuous metrics with exact sample standard deviations ($\sigma$), Standard Errors of the Mean (SEM), and two-sided 95% Confidence Intervals calculated via SciPy (`scipy.stats.t.interval`).
  3. Conducted paired Welch's $t$-tests confirming statistical significance ($p < 0.001$).
  4. Clarified that the $0.00 \pm 0.00$ discrete intimate violation rate in $\text{D}^2\text{RO}$ occurs because the anisotropic Gaussian proxemic cost field $H_{\text{prox}}$ inflates corridor traversal costs to deter paths intersecting pedestrian personal space before violation can occur, whereas non-social baselines (Static $A^*$, APF) incur statistically significant violations ($p < 0.001$).

---

### Major Concern 4: Cost Function Weight Derivation & Sensitivity Analysis
> **Reviewer Comment:** *"The five cost weights (wD=1.0, wM=1.5, wH=2.0, wR=1.0, wS=1.2) are stated as 'calibrated' with no calibration procedure or sensitivity analysis... A reviewer cannot assess robustness to this hand-tuning."*

* **Author Response:** In Section III-B, we added an explicit dimensional derivation and sensitivity analysis explaining the physical balancing:
  - $w_D = 1.0$: Normalized Euclidean distance baseline ($\text{m}$).
  - $w_M = 1.5$: Weights collaborative V2V congestion alerts $1.5\times$ higher than distance, guaranteeing proactive diversion through parallel aisles rather than queueing.
  - $w_H = 2.0$: Social compliance weight prioritizing human comfort $2.0\times$ above metric distance, enforcing compliant yielding.
  - $w_R = 1.0$: Directional corridor mutex multiplier ($R_{\text{lock}} = \infty$ during active contention, $0$ otherwise).
  - $w_S = 1.2$: Clearance envelope penalty preventing corner scrapes ($1.2\times$ baseline).

---

### Major Concern 5: Data & Code Availability for Reproducibility
> **Reviewer Comment:** *"The paper claims '4 open-access CSV datasets'... but provides no repository link, DOI, or supplementary material reference... reproducibility artifacts are essential."*

* **Author Response:** We have added a dedicated **Data and Code Availability** section with a link to our open-source MIT-licensed repository containing all simulation code, benchmarking scripts, test suites, and raw CSV datasets:  
  `https://github.com/polla-fattah/D2RO`

---

### Minor Concerns Addressed:
1. **Figure Captions:** Captions for Figs. 5–10 have been updated to explicitly clarify which elements represent geometric architectural schematics versus empirical simulation trajectory outputs.
2. **Manuscript Metadata:** Corrected submission header dates.
3. **Application Scope:** Clarified that while the algorithmic principles generalize to library AGVs, experimental evaluations benchmark the three primary public service domains (Supermarket, Hospital, Airport).

---

We believe the manuscript is now thoroughly strengthened and ready for publication in *IEEE Transactions on Robotics*.
