The paper proposes D²RO/SW-DGO, combining D* Lite, V2V congestion information, human proxemics, corridor locking, and a trolley safety-envelope term into a dynamic routing cost. The intended contribution is clear and relevant to socially aware multi-robot navigation in supermarkets, hospitals, and airports. 

### Reviewer recommendation

**Decision: Reject in current form / encourage resubmission after major reconstruction.**

For a less selective robotics journal, I might consider **Major Revision**, but for *IEEE Transactions on Robotics*, the current problems concern the reliability of the experimental evidence and theoretical claims themselves rather than presentation alone.

| Criterion              | Assessment                        |
| ---------------------- | --------------------------------- |
| Relevance              | Strong                            |
| Practical importance   | Strong                            |
| Novelty                | Moderate                          |
| Technical formulation  | Moderate, with important problems |
| Experimental rigor     | Weak                              |
| Reproducibility        | Weak                              |
| Internal consistency   | Very weak                         |
| Writing/presentation   | Moderate                          |
| Overall recommendation | **Reject / Resubmit**             |

### Main strengths

The paper addresses a genuinely important problem. Coordinating autonomous service robots in human-shared environments is more difficult than warehouse navigation, and the manuscript correctly emphasizes narrow corridors, dynamic pedestrians, social-space constraints, and distributed information sharing. 

The idea of incorporating distance, mesh-derived congestion information, proxemic costs, corridor reservations, and vehicle-clearance costs into one graph-planning architecture is intuitively useful. The five components are clearly identified mathematically. 

The ablation-study concept is also good. Removing the mesh, lock, proxemic, and safety terms separately is exactly the kind of analysis such a paper should perform. Table II attempts to demonstrate the contribution of the individual components. 

The multi-domain evaluation is another potentially valuable aspect. Testing supermarket, hospital, and airport layouts is more persuasive than validating against a single artificial grid. 

However, these strengths are currently undermined by the following problems.

### Major reviewer comments

1. **The experimental results contain severe contradictions.**

This is the largest problem in the manuscript.

Table I reports D²RO as having **100% success, 22.00 ± 4.50 s makespan, and 0 intimate-space violations**. 

But Figure 7 on the same page appears to report approximately:

**70% success**,
**27.8 s makespan**, and
**53.5 intimate violations**

for D²RO. 

These are not small numerical differences. They lead to completely different scientific conclusions.

For example, the text states:

> D²RO achieves 100.0% success, 0.0 deadlocks, and 0.0 intimate violations.

That claim is made explicitly in the results section. 

Yet Figure 7 visually contradicts it.

This alone would prevent acceptance. The authors need to go back to the original experimental logs, regenerate all tables and figures automatically from the same data source, and verify every result in the manuscript.

---

2. **It is unclear whether these are physical experiments or simulations.**

The abstract states that the method was:

> evaluated across 20 randomized Monte Carlo physical trials

and the manuscript repeatedly uses wording suggesting physical validation. 

However, Section VI says:

> “100% physically simulated Monte Carlo experiments”



These concepts are fundamentally different.

Furthermore, the Future Research section says hardware-in-the-loop and physical ROS 2 deployment are **future work**. 

Therefore, based on the manuscript, I cannot determine whether:

the experiments used real robots,

a custom 2-D simulator,

hardware-in-the-loop simulation,

or some combination.

The phrase **“physically simulated”** should not be used as a substitute for physical experimentation.

If all experiments are simulations, the paper must clearly say so throughout.

---

3. **The manuscript significantly overstates its theoretical guarantees.**

The authors repeatedly claim that D²RO provides **“provable deadlock freedom”** and “guarantees zero head-on corridor deadlocks.” 

However, I do not see an actual theorem and proof establishing this.

The proposed mechanism essentially assigns an infinite reverse-edge cost when another robot has locked the corridor:

[
R_{\text{lock}}(u,v,t)=\infty.
]



This is a useful mechanism, but it does not by itself constitute a proof of distributed deadlock freedom.

A true guarantee would need to deal with simultaneous lock acquisition, message delay, packet loss, network partition, robot failures, lock expiration, starvation, competing lock requests and possibly cyclic reservations involving more than two robots.

The algorithm currently says to acquire the corridor lock and then broadcast the lock request. 

The distributed mutual-exclusion protocol itself is therefore insufficiently specified.

The authors should either provide a proper theorem under clearly stated communication and topology assumptions or replace words such as **“provably,” “guaranteeing,” and “deadlock freedom”** with experimentally supported wording.

---

4. **ORCA and Artificial Potential Fields are incorrectly conflated.**

The manuscript describes the failure as resulting from repulsive forces from walls and humans cancelling the attractive goal force:

[
|F_{\text{net}}|\rightarrow0.
]



That is a reasonable explanation for classical **Artificial Potential Fields**.

It is not an accurate description of how **ORCA** operates.

ORCA uses reciprocal velocity obstacles and velocity-space constraints; it does not calculate the same attractive/repulsive force vectors as an APF.

Yet throughout the manuscript, “ORCA / Potential Field” appears to be treated as essentially one baseline. The benchmark table identifies “Reactive Avoidance (ORCA),” while the discussion explains its failure in APF terms. 

The authors must separate these algorithms and implement them independently.

This is an important conceptual issue, not simply terminology.

---

5. **The baseline comparison is inadequate for the claimed contribution.**

Comparing primarily against Static A* and ORCA does not adequately establish state-of-the-art performance for a distributed multi-agent planning paper.

The literature review itself discusses decentralized MAPF, M*, MAPD, PRIMAL, Learn-to-Follow, and a method combining reciprocal collision avoidance with localized MAPF. 

In fact, the authors describe Dergachev and Yakovlev's work as using continuous reciprocal avoidance with local MAPF when deadlock occurs, and then say:

> “D²RO leverages this exact synthesis”



That makes comparison against that class of method particularly important.

Showing that the proposed architecture outperforms a static shortest-path planner and a purely reactive controller is not enough to demonstrate superiority over modern hybrid approaches.

---

6. **The novelty needs to be defined much more carefully.**

All five principal elements are based on established ideas:

D* Lite,

cost-map modification,

Gaussian social/personal-space fields,

distributed congestion communication,

and reservation/mutex mechanisms.

The potentially novel contribution seems to be their particular integration and distributed cost formulation rather than the individual methods.

That can still constitute valuable research, but the paper currently presents SW-DGO as if it were a fundamentally new optimization paradigm.

The authors should explicitly state what mathematical or algorithmic mechanism is new compared with existing socially aware planning and distributed MAPF systems.

---

7. **The five-component cost function has no dimensional treatment or weighting strategy.**

The central equation is:

[
C=D+W_{\text{mesh}}+H_{\text{prox}}+R_{\text{lock}}+S_{\text{trolley}}.
]



But these terms represent very different quantities.

Distance has spatial units.

Mesh congestion has an arbitrary penalty amplitude.

The proxemic term is an integrated Gaussian discomfort cost.

The lock term can equal infinity.

The trolley term is another Gaussian-like penalty.

Why can these quantities simply be added with equal numerical importance?

There should normally be explicit weights such as

[
C=
w_D D+
w_M W_{\text{mesh}}+
w_H H_{\text{prox}}+
w_R R_{\text{lock}}+
w_S S_{\text{trolley}},
]

together with normalization, parameter-selection methodology, and sensitivity analysis.

Without this, reproducibility is extremely difficult.

---

8. **The “anisotropic” Gaussian proxemics model appears mathematically isotropic.**

The paper states that pedestrian personal space is represented using an:

> “anisotropic 2D Gaussian potential field”

but then gives a formulation based on

[
\exp\left(-\frac{|p-h_j|^2}{2\sigma^2}\right).
]



That is an **isotropic radial Gaussian**, assuming the equation has been rendered correctly.

An anisotropic human-proxemic field would normally require separate longitudinal/lateral scales, orientation, or a covariance matrix.

This is particularly important in socially aware navigation because human personal space is often direction-dependent.

Either the terminology or the formulation must be corrected.

---

9. **There is an important simulation-frequency inconsistency.**

The paper specifies:

[
dt = 0.05,s
]

while also repeatedly claiming **60 FPS** operation. 

A 0.05-second simulation step corresponds to:

[
1/0.05 = 20~\text{Hz},
]

not 60 Hz.

This raises concern that some simulation parameters or performance claims were not checked carefully.

---

10. **The embedded-hardware timing claims are insufficiently supported.**

The abstract reports vertex-repair times below 0.16 ms on low-cost embedded hardware. 

The contribution section explicitly mentions Raspberry Pi 5 and Jetson Orin Nano. 

But I could not find a proper experimental-hardware subsection specifying processor, clock, operating system, implementation language, compiler settings, number of vertices/edges, number of runs, timing methodology, or separate results for the Pi and Jetson.

Later, deployment on these platforms is described as **future research**. 

Therefore the current wording appears stronger than the evidence provided.

---

11. **The scalability experiment contains a confounding variable.**

Table IV increases pedestrian density from 2 to 24 people but simultaneously increases the fleet from 2 carts to 10 carts. 

Consequently, the experiment does not isolate crowd-density scalability.

The authors cannot tell whether changes in latency or communication arise from:

additional pedestrians,

additional robots,

or their interaction.

Two separate experiments should be performed:

fixed robot fleet / increasing human density,

and fixed human density / increasing fleet size.

Ideally a two-factor experiment should also be included.

---

12. **Twenty trials are insufficient to support absolute claims such as “100%” reliability and “provably zero.”**

The manuscript reports 20 Monte Carlo trials per baseline. 

Twenty successful trials demonstrate that the approach worked in those twenty trials. They do not establish general deadlock freedom or guaranteed success.

At minimum, considerably more randomized experiments should be performed, preferably across multiple seeds and increasingly adversarial configurations.

Confidence intervals and statistical comparisons should also be provided instead of relying primarily on means and standard deviations.

---

13. **The experiment-generation methodology is insufficiently described.**

I would need much more information to reproduce the reported experiments.

The paper needs exact randomization procedures for human initial positions, human trajectories and loitering behavior, robot start/goal positions, fleet sizes, communication delays and losses, graph sizes, corridor widths, robot radii, velocities, turning constraints, timeout conditions, congestion-event thresholds, Gaussian parameters, mesh penalty parameters and all baseline parameters.

At present, numerous implementation constants appear throughout the paper—for example the 240-pixel sensing radius and 18-pixel/36-pixel safety margins—but there is no systematic parameter table.  

---

14. **The fixed pixel-to-meter conversion requires justification.**

The manuscript states that an 18-pixel buffer corresponds to **0.54 m**. 

That implies a particular global scale.

Yet the experiments cover supermarkets, hospitals, and airports. The manuscript needs to specify the physical scaling of all maps and demonstrate that the same pixel-to-meter relationship is consistently used.

For a robotics paper, physical dimensions should preferably be represented directly in SI units.

---

15. **Communication-performance claims need actual networking experiments or a much more complete network model.**

The paper claims bandwidth consumption below **2.5 KB/s**, but the presented tables primarily report numbers of V2V packets. 

Packet counts cannot determine bandwidth without packet size and time interval.

Latency, packet loss, retransmission behavior, medium access and packet collisions would also be important for a genuinely distributed system.

This is especially important because the method's corridor locking depends on reliable and timely communication.

---

16. **One networking statement appears technically incorrect.**

The paper groups:

> “Sub-GHz (868/915 MHz / IEEE 802.11p)”

together. 

IEEE 802.11p should not be presented as an 868/915 MHz Sub-GHz technology.

The communications section needs technical review.

---

17. **The figures themselves contain contradictory numbering and apparent generation artifacts.**

The page-5 and page-6 graphics visibly contain labels such as “Figure 8,” “Figure 9,” and “Figure 10” inside images that are actually published as Figures 4, 5 and 6.

Later, Figures 8–10 refer to completely different experimental plots.

This makes the paper look insufficiently checked before submission.

More seriously, Table II and Table III on page 7 visually overlap or interfere with each other, making portions difficult to read.

All figures should be regenerated at publication quality without internal temporary titles and with a single consistent numbering system.

---

18. **The manuscript claims open datasets but does not actually make reproducibility resources identifiable.**

The contributions claim:

> “10 camera-ready 300 DPI figures and 4 open-access CSV datasets.”



I do not see a repository identifier, DOI, supplementary-material reference, code repository, or dataset URL in the manuscript.

For a computational robotics paper with custom simulation experiments, providing code, maps, seeds and raw output data would greatly strengthen the submission.

---

19. **The bibliography requires careful verification.**

Some entries should be manually checked against the original publications. In particular, reference [2] begins with the unusual author entry **“H.-V. Authors”**, which looks placeholder-like rather than like a normal bibliographic record. 

Before resubmission, every reference should be independently verified for title, author list, year, pages, venue and DOI.

---

20. **There is an impossible manuscript-date issue if this is intended as a current submission.**

The manuscript states:

> “Manuscript received August 15, 2026; revised October 20, 2026.”



Today is August 15, 2026, so the stated revision date is in the future.

If this is simply template text, it should be removed immediately. It also reinforces the impression that the manuscript has been formatted to appear like an already-published IEEE article rather than prepared as a submission.

### Overall scientific assessment

There is a **potentially good paper underneath the current manuscript**.

The promising research question is essentially:

> Can socially weighted dynamic graph replanning, distributed congestion sharing, and explicit bottleneck reservations outperform conventional navigation approaches for autonomous service fleets in constrained human environments?

That is a legitimate and interesting question.

However, the present manuscript goes considerably beyond what its evidence supports. In several places it says the system **“proves,” “guarantees,” “eliminates,” or achieves “100%”** behavior when the experiments consist of relatively few custom simulations and the theoretical foundations for such guarantees have not been presented.

The most damaging issue is not the writing—it is that **the numerical evidence currently contradicts itself**.

### What I would require before reconsideration

I would ask the authors to reconstruct the experimental section from the original source data; resolve every table/figure discrepancy; clearly classify the work as simulation, HIL, or physical experimentation; implement independent APF and ORCA baselines; add stronger contemporary MAPF/social-navigation baselines; substantially increase randomized trials; report confidence intervals and statistical testing; disclose every simulator and algorithm parameter; normalize and justify the five cost components; correct the proxemics formulation; provide a genuine distributed-lock protocol or remove the deadlock-free theorem-like claims; independently vary fleet size and pedestrian density; provide code/data/seeds; and systematically audit every technical statement, figure, reference, and numerical claim.

Only after those changes would I consider the work ready for another peer-review cycle.

### Suggested confidential note to the editor

My recommendation would be approximately:

**Reject — potentially suitable for resubmission as a substantially revised new manuscript.**

The topic is relevant and the proposed integrated architecture has practical potential. However, fundamental inconsistencies between reported tables, figures, and experimental descriptions prevent assessment of the validity of the results. Claims of deadlock freedom, physical validation, social-compliance guarantees, and embedded real-time performance are presently insufficiently demonstrated. Most notably, Table I reports 100% D²RO success and zero intimate-space violations while Figure 7 apparently reports 70% success and approximately 53.5 violations for the same proposed method.  These issues require reconstruction and revalidation of the experimental study rather than ordinary manuscript revision.

**Therefore: I would not accept the paper in its present state.**

I would, however, encourage the authors to fix it rather than abandon it—the underlying D²RO concept appears capable of becoming a publishable robotics paper once the experimental evidence and theoretical claims are brought into alignment.
