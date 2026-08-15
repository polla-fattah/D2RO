Yes. I compared the revised manuscript against the specific concerns from my previous review. The authors **did make several meaningful improvements**, but they have **not yet satisfied the review sufficiently for acceptance**. More importantly, some major internal contradictions remain, including a serious new/remaining mismatch between Table II and Figure 7.

My second-round recommendation would therefore be:

**Decision: Major Revision / Reject and Resubmit — NOT Accept.**

For *IEEE Transactions on Robotics*, I would lean toward **Reject and Resubmit**, because several remaining issues concern the validity and consistency of the experimental evidence rather than minor editing.

## Audit of the previous reviewer comments

| #  | Previous concern                              | Status                       | Assessment                                                    |
| -- | --------------------------------------------- | ---------------------------- | ------------------------------------------------------------- |
| 1  | Tables/figures had contradictory results      | ❌ **Not fixed**              | Serious contradictions remain                                 |
| 2  | Physical experiment vs simulation unclear     | ⚠️ **Partially fixed**       | Abstract fixed, contributions still contradict it             |
| 3  | Unsupported “provable deadlock freedom”       | ❌ **Not fixed**              | Same strong claim remains without formal proof                |
| 4  | APF and ORCA incorrectly conflated            | ✅/⚠️ **Mostly fixed**        | Now separated experimentally and mathematically               |
| 5  | Weak baselines                                | ⚠️ **Improved**              | Added decentralized local MAPF, but more work needed          |
| 6  | Novelty insufficiently distinguished          | ❌ **Not really fixed**       | Still primarily integration of existing components            |
| 7  | Cost terms lacked weights/normalization       | ❌ **Not fixed consistently** | Abstract weighted; main formulation remains unweighted        |
| 8  | “Anisotropic” Gaussian was actually isotropic | ✅ **Fixed**                  | Proper directional asymmetric formulation added               |
| 9  | 0.05 s vs 60 FPS contradiction                | ✅ **Fixed**                  | 20-Hz physics vs 60-FPS rendering now explained               |
| 10 | Embedded hardware claims unsupported          | ❌ **Not fixed**              | Claims remain without hardware benchmarking details           |
| 11 | Crowd/fleet scalability confounded            | ✅ **Fixed**                  | Now appropriately decoupled                                   |
| 12 | Only 20 trials; weak statistics               | ⚠️ **Partially fixed**       | N=100 now, but statistical reporting remains problematic      |
| 13 | Insufficient simulation parameters            | ⚠️ **Improved**              | Parameter table added, but methodology still incomplete       |
| 14 | Pixel-to-meter scale unexplained              | ✅ **Fixed**                  | SI calibration now explicitly provided                        |
| 15 | Networking/bandwidth insufficiently specified | ⚠️ **Partially fixed**       | Packet size added; network model still weak                   |
| 16 | 802.11p/Sub-GHz technical error               | ❌ **Not fixed**              | Same statement remains                                        |
| 17 | Figure numbering/generation artifacts         | ⚠️ **Partially fixed**       | Some layout improved, but internal numbering artifacts remain |
| 18 | No identifiable code/data repository          | ✅ **Fixed**                  | Repository/data availability section added                    |
| 19 | Bibliographic/reference problems              | ⚠️ **Partially fixed**       | Bibliography improved, but unresolved `[?]` citations remain  |
| 20 | Future revision date                          | ❌ **Not fixed**              | Still says revised Oct. 20, 2026                              |

So approximately:

**5 fully addressed, 7 partially addressed, and 8 still inadequately addressed.**

The most important details are below.

---

# 1. ❌ The biggest problem is STILL there: Table II and Figure 7 contradict each other

This alone prevents acceptance.

Table II now reports:

* Static A*: 100% success
* APF: 0%
* ORCA: 0%
* Local MAPF: 0%
* **D²RO: 100%**
* D²RO makespan: **21.99 ± 2.39 s**
* D²RO intimate violations: **0.00 ± 0.00**



But the Figure 7 plots immediately underneath do not reproduce those numbers.

For example, the parsed figure reports the success bars as:

> 100.0%, 0.0%, 0.0%, 0.0%, **0.0%**

meaning that visually D²RO appears to have **0% success**, even though Table II says 100%. 

There are additional disagreements.

Table II says:

* APF intimate violations = **226.39 ± 69.25**
* Local MAPF = **102.44 ± 15.00**

while Figure 7 shows approximately:

* APF = **165.5**
* Local MAPF = **96.0**

 

This was the **single most serious concern in my first review**, and unfortunately it has not been resolved.

### Required correction

All plots and tables should be generated automatically from exactly the same raw CSV files.

No figure values should ever be manually typed.

Until this is done, I cannot trust the experimental conclusions.

---

# 2. ⚠️ Simulation vs physical experiments: improved in one place, contradicted elsewhere

This was substantially improved in the **abstract**.

The new abstract correctly says:

> “N = 100 randomized Monte Carlo kinodynamic simulation trials”



And Section VI also clearly calls them:

> “kinodynamic simulation experiments”



Excellent.

Unfortunately, the old wording was not removed from the contribution section.

It still says:

> “20 randomized Monte Carlo physical trials”



So the manuscript now says both:

**N = 100 simulations**

and

**20 physical trials.**

That must be corrected everywhere.

If no physical robots were experimentally tested, then the words **physical trials**, **physical experiments**, etc. should not appear.

---

# 3. ❌ “Provable deadlock freedom” still has no proof

This major concern has essentially not been addressed.

The revised manuscript still claims:

> “provably eliminating head-on deadlocks”

and

[
N_{\text{deadlock}}\equiv0
]



But the text merely explains the lock mechanism:

* reserve a direction;
* broadcast LOCK_REQUEST;
* set the reverse cost to infinity;
* opposing robot waits/detours.

That is **an algorithmic argument, not a formal proof**.

The paper still does not formally handle:

* simultaneous lock requests;
* conflicting distributed states;
* packet loss;
* communication latency;
* timeout;
* lock ownership;
* lock release;
* robot failure while holding a lock;
* starvation;
* cyclic multi-corridor dependencies;
* network partition.

Therefore the authors have two choices.

Either provide an actual theorem, assumptions, lemmas and proof, or simply say:

**“The proposed reservation mechanism eliminated head-on deadlocks in all evaluated simulation trials.”**

That would be scientifically defensible.

“Provably deadlock-free” currently is not.

---

# 4. ✅ APF vs ORCA distinction is much better

This was one of the most successful revisions.

The new experimental section explicitly separates:

**Artificial Potential Fields:**

> force-gradient reactive navigation

and

**ORCA:**

> velocity-obstacle half-plane linear programming.



Better still, the authors now distinguish their different failure mechanisms:

APF:

[
|F_{\mathrm{net}}|\approx0
]

through local force cancellation,

versus ORCA:

[
\cap H=\varnothing
]

or (v\rightarrow0) because feasible velocity constraints disappear. 

**This directly addresses my previous criticism.**

I would mark this reviewer comment as essentially resolved.

There is still some sloppy combined language in the introduction, but scientifically this is dramatically better.

---

# 5. ⚠️ The baseline study has improved substantially

The authors added:

* Static A*
* APF
* ORCA
* **Decentralized Local MAPF**
* D²RO



That is much better than the original comparison against essentially Static A* and reactive navigation.

However, there is now another concern.

Table II reports:

**Decentralized Local MAPF = 0% success.**



That is an extraordinarily poor result for a MAPF-style method and therefore needs careful justification.

The manuscript describes this implementation as:

> “Windowed local conflict arbitration and token-passing”



The authors need to explain exactly how this baseline was implemented, including parameters and whether it is a faithful implementation of the cited method.

Otherwise a reviewer may suspect that the baseline has been artificially weakened.

---

# 6. ❌ The central weighted-cost correction is internally inconsistent

This is another important problem.

The **abstract** now gives the improved formulation:

[
C =
w_DD+
w_MW_{\text{mesh}}+
w_HH_{\text{prox}}+
w_RR_{\text{lock}}+
w_SS_{\text{trolley}}.
]

Excellent. 

But Section I still gives:

[
C=D+W_{\text{mesh}}+H_{\text{prox}}+R_{\text{lock}}+S_{\text{trolley}}
]

with **no weights**. 

And the conclusion once again uses the **unweighted form**:

[
C=D+W_{\text{mesh}}+H_{\text{prox}}+R_{\text{lock}}+S_{\text{trolley}}.
]



Worse, although Section III says:

> “dimensionally weighted linear combination”

the displayed formulation thereafter begins directly with the individual terms rather than presenting and defining the actual (w_i) values. 

So my original concern is **not yet solved**.

The paper needs one canonical equation used everywhere, plus a table defining:

[
w_D,;w_M,;w_H,;w_R,;w_S
]

and explaining how those values were selected.

---

# 7. ✅ The proxemics formulation has been properly improved

This is another strong revision.

Previously an isotropic Gaussian was called “anisotropic.”

The revised paper now explicitly rotates into the pedestrian's body frame and defines different front/rear/lateral spreads:

[
\sigma_{\text{front}}=1.35,m,
]

[
\sigma_{\text{rear}}=0.60,m,
]

[
\sigma_y=0.90,m.
]



This is now genuinely directional/asymmetric.

**Reviewer concern resolved.**

---

# 8. ✅ The 20-Hz / 60-FPS inconsistency has been fixed properly

This is very well addressed.

The new parameter table distinguishes:

* physics integration: (\Delta t=0.05s) = **20 Hz**
* GUI rendering: **60 FPS**



This is exactly the clarification I wanted.

**Resolved.**

---

# 9. ✅ Pixel-to-meter conversion has also been fixed

They now explicitly state:

[
1\text{ px}=0.03\text{ m}.
]

They also convert chassis size, safety radius, shelf clearance, following distance and proxemic distances into SI units. 

This is a substantial methodological improvement.

**Resolved.**

---

# 10. ✅ Scalability confounding was fixed correctly

This was another very good change.

The old experiment increased humans and robots simultaneously.

Now they conduct two separate tests:

### Crowd-density scalability

Fixed:

[
N_{\text{carts}}=4
]

while humans increase from 2 to 30.

### Fleet scalability

Fixed:

[
N_{\text{humans}}=10
]

while robots increase from 2 to 12.



Figure 10 also explicitly labels the fixed variables. 

This directly responds to my comment.

**Resolved.**

---

# 11. ⚠️ Increasing from 20 to 100 trials is good, but the statistical reporting is still incomplete

The authors now use:

[
N=100
]

which is a major improvement. 

However, Table II says:

> “Mean ± Std. Dev. [95% CI]”

yet the table seems to provide only values such as:

[
21.99\pm2.39
]

with no actual 95% confidence interval.



That is not a 95% CI unless they explicitly state that ± represents CI rather than SD—and the heading says it is SD.

Also the manuscript repeatedly reports:

[
p<0.001
]

for D²RO performance. 

But I cannot find a clear description of:

* statistical test;
* null hypothesis;
* comparator;
* test statistic;
* degrees of freedom;
* multiple-comparison correction;
* effect size.

Thus the statistical improvement is only partial.

---

# 12. ⚠️ Simulation parameters are substantially better, but still insufficient for full reproducibility

The new parameter table is valuable. It gives physical scale, rates, robot dimensions, velocities, packet size, TTL and proxemic parameters. 

However, the experimental-methodology section still needs details such as:

* random seed policy;
* robot start/goal sampling;
* human trajectory generation;
* pedestrian speeds;
* loitering probabilities;
* dynamic obstacle generation;
* baseline parameter tuning;
* failure/timeout definition;
* number of robots in the main benchmark;
* graph node/edge counts;
* exact map dimensions;
* communication latency/loss assumptions.

So I would mark this as **significantly improved, but not fully resolved**.

---

# 13. ❌ Hardware timing claims remain problematic

The abstract still says:

> “under 0.15 ms on low-cost embedded hardware.”



The conclusion says the measurements were obtained:

> “on embedded microcontrollers.”



But I still do not see a dedicated benchmark describing:

* exact Raspberry Pi/Jetson model used for each measurement;
* CPU/GPU;
* clock;
* OS;
* programming language;
* compiler;
* optimization level;
* timing method;
* warm-up;
* number of repetitions;
* roadmap graph size.

If those timings actually came from the simulation host computer, then they cannot be described as embedded-hardware measurements.

So this major reviewer concern remains open.

---

# 14. ⚠️ Networking methodology improved slightly, but is still incomplete

The parameter table now identifies a **64-byte V2V packet** and TTL = 3. 

That helps.

But a distributed communication paper should still describe:

* simulated packet latency;
* jitter;
* packet loss;
* collision;
* retransmission;
* queueing;
* link failures.

The method's deadlock-avoidance claim depends heavily on timely communication, so an ideal network is a major assumption.

---

# 15. ❌ The IEEE 802.11p issue was not corrected

Unfortunately this exact sentence remains:

> “Sub-GHz (868/915 MHz / IEEE 802.11p)”



This should still be corrected.

802.11p should not simply be grouped as an 868/915 MHz Sub-GHz technology.

---

# 16. ⚠️ Figure presentation improved, but the internal numbering artifacts remain

For example the object eventually captioned as **Fig. 4** still contains internal text:

> “Figure 8: Spatial Human Proxemic…”



Similarly, the figure published as Fig. 5 contains “Figure 9,” and Fig. 6 contains “Figure 10.” 

That is a relatively easy production fix, but it was specifically pointed out previously and should have been corrected.

---

# 17. ✅ Code/data availability was properly addressed

This is a good revision.

The paper now contains a dedicated **DATA AND CODE AVAILABILITY** section and states that the source code, benchmarking harnesses, verification tests, raw datasets and figures are available under an MIT license. 

It also provides an explicit GitHub repository on page 9. 

That directly resolves my reproducibility-resource comment.

---

# 18. ⚠️ The references improved, but there is still a broken citation

The previous suspicious `"H.-V. Authors"` entry is gone, which is good.

The final bibliography now looks substantially more conventional. 

However, the text still contains:

> “HA-VLN 2.0 [?]”



And another `[?]` appears alongside Gaussian proxemics in the introduction. 

A submitted IEEE paper cannot contain unresolved citation placeholders.

---

# 19. ❌ The manuscript date problem is unchanged

It still states:

> “Manuscript received August 15, 2026; revised October 20, 2026.”



Today is August 15, 2026.

Therefore October 20, 2026 is still a future date.

This should simply be removed from the submitted manuscript/template.

---

# 20. There is also a new inconsistency in the abstract concerning Local MAPF

The abstract now states that Decentralized Local MAPF experiences:

> “+21.8% makespan penalty”



But Table II reports Local MAPF as:

**0% success and Timeout (35 s).** 

If every Local MAPF trial timed out, describing its result merely as a “+21.8% makespan penalty” is difficult to reconcile.

The authors need to trace that number back to the raw experiment output.

---

# My revised reviewer decision

The paper is **considerably better conceptually** than the first submission.

The strongest improvements are:

* APF and ORCA separated correctly;
* anisotropic proxemics corrected;
* experiments increased to N=100;
* physical/simulation wording corrected in the abstract;
* SI calibration added;
* 20-Hz physics vs 60-FPS rendering explained;
* decentralized MAPF baseline added;
* crowd/fleet scaling decoupled;
* code and data repository added.

Those are substantial changes.

However, the manuscript **cannot yet be accepted because the central quantitative evidence remains internally inconsistent**.

If I were writing the second-round recommendation to the editor, my key sentence would be:

> **The authors have made substantial progress in addressing the previous review, but the revision does not yet establish a reliable experimental record. In particular, Table II and Figure 7 continue to report mutually incompatible results for the proposed method and several baselines. In addition, simulation/physical-experiment terminology remains contradictory, the weighted objective is not consistently formulated, theoretical deadlock-freedom claims remain unsupported by formal analysis, and embedded-hardware performance claims are insufficiently documented. I therefore cannot recommend acceptance at this stage.**

### Final recommendation

**❌ Accept:** No
**❌ Minor revision:** No
**⚠️ Major revision:** Reasonable if the journal permits another round
**✅ My likely T-RO recommendation:** **Reject and invite a thoroughly corrected resubmission**

The key point is that they **should not add more features now**. They should concentrate on scientific consistency. I would tell them to regenerate **every table, figure, abstract number, result paragraph and conclusion number directly from one verified experimental dataset** before doing anything else. Once that is done, many of the remaining reviewer objections are quite fixable.
