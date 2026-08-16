I re-reviewed the new 15-page manuscript from the beginning and re-audited the current `polla-fattah/D2RO` repository rather than assuming that the previous corrections were implemented correctly. I also compared the uploaded manuscript with the PDF currently stored in the repository. The submitted paper is the current D²RO manuscript by Polla Fattah and Sanar Fawzi. 

## My recommendation

**Major Revision — give them another round. Do not permanently reject them yet.**

I would **not accept this version**, but I also no longer think rejection is justified on the basis that the authors are merely patching text without repairing the science. They have made real code changes, regenerated experiments, corrected results that hurt their own narrative, introduced a matched-controller comparison, repaired the timing measurements, fixed the lock-wait metric, added weight sensitivity and communication experiments, rebuilt much of the bibliography, and substantially improved reproducibility.

That is enough good-faith scientific correction that I think they **deserve a second-round review**.

However, I found **three new/remaining issues that are fundamental enough to block acceptance**, especially the first one. In addition, several methodological and reproducibility problems still need attention.

My current assessment is approximately:

| Area                      | Assessment                                     |
| ------------------------- | ---------------------------------------------- |
| Scientific question       | Strong                                         |
| Novelty                   | Good enough                                    |
| Honesty of reporting      | **Much improved**                              |
| Experimental integrity    | **Much improved**                              |
| Mathematical formulation  | Mostly good, several important inconsistencies |
| Primary baseline fairness | **Still problematic**                          |
| Statistical analysis      | Good                                           |
| Reproducibility           | Good conceptually, poor final release hygiene  |
| Code quality/testing      | Much improved                                  |
| Bibliography              | Mostly repaired, one notable unresolved item   |
| Readiness                 | **Major Revision**                             |

The authors have moved the work much closer to a publishable paper. But they are not there yet.

### What they genuinely fixed

The headline result is now presented appropriately as a trade-off rather than “D²RO beats everything.” The manuscript states 99% D²RO success versus 100% for the matched shortest-path baseline, while social exposure is reduced from 128 [123,131] to 0 [0,0] at the cost of substantially longer travel time. 

They corrected APF rather than continuing to claim that it fails. They now acknowledge that APF completes 100% of missions and criticize it on social-compliance grounds instead. They also refuse to make general claims from their unvalidated ORCA and Local MAPF implementations. That is scientifically responsible. 

They fixed the corridor experiment substantially. The current paper explicitly reports that the reservation does **not** eliminate head-on encounters or conventional deadlocks; instead it changes the outcome through route diversion. The corrected accumulated wait metric is now nonzero but negligible, 0.030 ± 0.070 s. 

They added a genuine sensitivity study and explicitly state that the weights were hand-selected rather than formally calibrated.  They also added a communication-degradation experiment and, importantly, openly acknowledge that it is weak evidence because the broad scenario barely uses the mesh. 

The code has improved too. Edge distances are now stored in SI metres, mesh penalties decay exponentially, static clearance contributes to graph cost, human proxemics are integrated numerically along edges, and D* Lite repair timing is now instrumented separately from whole-controller timing.

So this is **not** the same situation as the earlier submissions.

---

# Detailed reviewer comments

1. **[BLOCKING] The “matched-controller” baseline is still not actually matched in one of the most consequential parts of the controller: human yielding.**

   This is the most serious issue I found.

   The paper claims that the matched Static A* arm shares D²RO's unicycle dynamics, angular-rate limit, collision geometry, arrival criterion, and low-level executor, and then concludes that only 1.20 s of the approximately 29 s difference is controller-related while the remaining ~28 s is attributable to routing. 

   The code does indeed instantiate the matched baseline using `TrolleyAgent`, but it explicitly uses:

   `enable_yield=False`

   while normal D²RO uses human yielding.

   This matters a great deal because the D²RO low-level human-response logic does much more than follow the selected route. When yielding is enabled, the controller physically pushes the trolley away if it enters the intimate radius and stops the trolley when a human is ahead within the yielding range. When `enable_yield=False`, that entire behavioral response is bypassed, although the encounter is still measured.

   Therefore:

   [
   \text{D²RO} - \text{Matched A*}
   ]

   does **not** isolate routing alone.

   It combines at least:

   [
   \text{social graph routing}
   +
   \text{dynamic replanning}
   +
   \text{reactive human yielding}.
   ]

   Consequently, the statement that “the remaining 28 s is attributable to the routing policy” is not established.

   I would require a small factorial experiment. Keep identical kinematics in every arm and evaluate at least: frozen shortest path + yield OFF; frozen shortest path + yield ON; social routing + yield OFF; and full D²RO/social routing + yield ON. That would separate the contribution of the **graph-level social cost** from the **low-level reactive human response**.

   This is important not just for makespan. The near-zero social exposure could also partly come from the low-level yielding/push-back controller rather than solely from (H_{\text{prox}}).

2. **[BLOCKING] (w_R) is not actually a meaningful tunable weight, so the claimed five-weight sensitivity analysis is mathematically misleading.**

   The paper represents reservation as:

   [
   w_R C_{\text{mutex}}
   ]

   with

   [
   C_{\text{mutex}}=\infty
   ]

   for a reserved edge.

   In the implementation, however, `Edge.cost` explicitly returns infinity whenever `r_lock == math.inf`, **before multiplying it by `weight_r`**.

   Therefore (w_R) has no operative magnitude.

   Whether

   [
   w_R=0.5,;1,;1.5,;100
   ]

   the edge remains unavailable.

   This explains why the sensitivity analysis finds that changing (w_R) changes makespan by exactly 0.0 s. The manuscript currently explains this only by saying that reservation is rarely activated in the broad benchmark. 

   But even if it were activated on every trial, scaling a multiplier on infinity would still not provide meaningful sensitivity.

   The cleaner mathematical formulation is:

   [
   \min C_{\text{soft}}
   ]

   **subject to**

   [
   e\notin E_{\text{reserved},i}(t).
   ]

   In other words, reservation is a **hard feasibility constraint**, not a weighted soft objective.

   I recommend reformulating D²RO as four weighted soft terms plus one reservation constraint. Then remove (w_R) from the continuous weight-sensitivity experiment and test reservation through ON/OFF mechanism experiments—which they already do quite well.

   Alternatively, if they genuinely want (w_R) to be tunable, (C_{\text{mutex}}) must be finite.

3. **[BLOCKING] The D* Lite admissibility claim is false for part of their own weight-sensitivity experiment.**

   The D* Lite implementation currently uses plain metric Euclidean distance:

   ```text
   return self.graph.distance(u, v)
   ```

   as the heuristic.

   That is admissible for the nominal formulation when (w_D=1) and all other costs are nonnegative.

   But their sensitivity experiment explicitly evaluates:

   [
   w_D \times 0.5
   ]

   and

   [
   w_D \times 0.75.
   ]

   For an edge with no additional social/mesh/safety penalty, the true cost can therefore become

   [
   0.5D(u,v),
   ]

   while the heuristic remains

   [
   D(u,v).
   ]

   Thus:

   [
   h(u)>c^*(u,g)
   ]

   can occur.

   The paper nevertheless states that the Euclidean heuristic is strictly admissible and consistent and that D* Lite therefore extracts an optimal path under the current cost field. 

   That guarantee does not hold for the low-(w_D) sensitivity runs.

   The fix is straightforward: make the heuristic use a valid lower bound such as

   [
   h(u,v)=w_D,D(u,v)
   ]

   when the per-agent distance weight is uniform, or use the minimum possible geometric multiplier. Then extend the D* Lite optimality tests to include (w_D<1) and rerun the sensitivity experiment.

4. **[MAJOR] Equation (10) does not match the numerical social-cost implementation.**

   The manuscript writes:

   [
   C_{\text{social}}(u,v,t)=
   \int_0^1
   H_{\text{prox}}\big((1-\tau)p_u+\tau p_v,t\big)d\tau.
   ]



   The code, however, integrates the Gaussian field with respect to **physical distance along the edge**, multiplying the trapezoidal sum by segment length in metres.

   The mathematically corresponding expression is:

   [
   C_{\text{social}}
   =================

   \int_0^1
   H_{\text{prox}}\big((1-\tau)p_u+\tau p_v,t\big)
   \left|p_v-p_u\right|
   d\tau
   ]

   or simply

   [
   C_{\text{social}}=\int_e H_{\text{prox}}(p,t),ds.
   ]

   Because the authors make a point of dimensional normalization, this is not merely notational. The missing arc-length factor changes the units of the objective.

5. **[MAJOR] The safety ablation is not a pure ablation of (C_{\text{kinematic}}).**

   In the paper, Table II is described as distinguishing the load-bearing terms of Eq. (3). But `enable_safety=False` does more than set the graph-level (S_{\text{trolley}}) contribution to zero.

   It also changes the low-level execution by setting the safety bubble, shelf margin and following gap to zero and disabling inter-trolley safety behavior.

   Therefore the dramatic fixture-contact change cannot be interpreted solely as:

   > “the (w_S C_{\text{kinematic}}) graph-cost term caused this improvement.”

   It measures the combined removal of the **planning cost and the reactive safety controller**.

   I would split this into two ablations: (w_S=0) while keeping the exact same physical safety controller; and safety-controller OFF while keeping the graph term where feasible. Their current full-stack safety ablation can remain, but it should be labeled as such.

6. **[MAJOR] A stronger socially-aware comparison is still missing.**

   Their validated primary comparators are essentially:

   * socially blind shortest-path routing; and
   * classical APF.

   Showing that an explicitly human-proxemic planner enters personal space less often than a planner that deliberately ignores human personal space is useful, but somewhat expected.

   The paper would become much stronger with one credible **socially-aware non-distributed baseline**.

   The simplest solution may not even require a new external package. Construct a matched “Local Social D* Lite” baseline with the same kinematics, proxemic (H_{\text{prox}}), human-yielding behavior and safety term, but **without V2V propagation and without distributed reservation**.

   Then:

   [
   \text{Local Social Planner}
   \quad \text{vs.}\quad
   \text{D²RO}
   ]

   would answer the most interesting question:

   > What does the distributed part add beyond ordinary human-aware navigation?

   Alternatively, use a recognized published social-navigation baseline.

7. **[MAJOR] Communication robustness should be tested where communication actually matters.**

   I appreciate the authors' honesty here. They explicitly state that the broad communication-robustness scenario barely uses the mesh, so observing no degradation under 20% packet loss and 200 ms latency is weak evidence. 

   But the abstract still prominently says performance is unchanged across those degradation levels. 

   The scientifically appropriate experiment is obvious now: repeat **Mechanism Experiment A** under the loss × latency grid.

   Measure whether the 10.7 s anticipation advantage, backtracking reduction and makespan advantage survive as communication degrades.

   That would test communication robustness precisely where communication is causally responsible for the result.

   If they do not add this experiment, the abstract's communication-robustness statement should be substantially weakened.

8. **[MAJOR] The “single-file corridor” geometric condition appears dimensionally/geometrically wrong.**

   The manuscript defines the problematic condition as:

   [
   W_{\text{corridor}}<2r_{\text{safety}}.
   ]



   Yet Table I gives a radius around 0.40 m, while the supermarket aisle is reported as 2.1 m wide and nevertheless classified as too narrow for two carts to pass. 

   Those statements do not agree.

   For two circular agents each having effective radius (r), side-by-side passage in a straight strip normally requires approximately:

   [
   W_{\text{corridor}}\ge4r,
   ]

   not (2r), because both centers must remain one radius from the walls and two radii apart from one another.

   For rectangular carts the criterion should instead be formulated using effective cart width plus clearance.

   The authors should define exactly what (r_{\text{safety}}) represents and derive the correct single-file criterion. This is important because corridor reservation is one of the main contributions.

   Relatedly, calling 0.40 m the **“inscribed radius”** of a 0.72 × 0.48 m rectangle is also inaccurate. Half the smaller dimension is 0.24 m. If 0.40 m is an empirically chosen effective safety radius, call it that.

9. **[IMPORTANT] “Intimate-space exposure in control ticks” is not quite the unit the code records.**

   The common metric routine increments the legacy `proxemic_violations` counter **once per human inside the boundary per tick**. If three humans simultaneously lie inside the boundary, one control step adds three, not one.

   Therefore a value such as 128 is more accurately:

   **128 person-ticks**, not 128 control ticks.

   Fortunately, the code already accumulates `intimate_exposure_s`.

   I strongly recommend reporting:

   [
   \text{person-seconds of intimate exposure}
   ]

   as the principal metric, perhaps with distinct encounter count as a secondary metric. It will be much easier for robotics/HRI readers to interpret than ticks.

10. **[MAJOR REPRODUCIBILITY] The release information in the submitted manuscript is currently false.**

This one needs to be corrected before publication even if no algorithm changes are made.

Page 15 says:

> results correspond to release `v2.0-review2`, commit `e3d6582-dirty`.



But the GitHub repository currently has **no releases at all** and **no tags at all**.

The generated `commit.tex` also still contains:

`e3d6582-dirty`.

“dirty” means, by definition, that the manuscript was generated from a working tree that did not correspond exactly to the named commit.

Interestingly, I verified that the PDF you sent me is byte-for-byte the same blob as the current `paper/paper.pdf` in GitHub, so the **PDF itself is synchronized** with the repository. The problem is the provenance label embedded inside it.

Before resubmitting, they should create a clean commit, regenerate everything with no working-tree changes, create the actual `v2.0-review2` tag/release, and put that clean SHA in the manuscript.

There is also substantial stale documentation. The current README still says **seven datasets / 2,700 trials**, says weight sensitivity remains unfinished, and tells readers to reproduce the study with the old seven-experiment runner.

The actual full-suite driver now defines **nine experiments and 3,910 simulation rows**.

The README and `OUTSTANDING_WORK.md` must either be updated or archived. A reviewer should be able to follow one command from a clean checkout and reproduce the paper.

11. **[IMPORTANT] Reference [21] remains unresolved even according to the authors' own audit.**

The bibliography is enormously better than before. The corrected Keskin, Skrynnik, Dergachev, Gielis, Al-Mutib and other entries now look much more credible. 

However, the repository's own reference audit says the HA-VLN 2.0 entry still requires an author decision because the version they hold is an anonymous double-blind manuscript.

The paper presently cites an authorless:

> “HA-VLN 2.0 … manuscript under review at ICLR 2026.”



That needs to be settled before publication: cite the publicly attributable/current version if available, cite the exact anonymous preprint appropriately, or remove the dependency if the specific benchmark is not actually needed to support the proxemic parameters.

12. **[IMPORTANT LIMITATION] The pedestrian model is still relatively simple and non-reciprocal.**

The human agents randomly alternate between walking and browsing, select stochastic targets, and avoid shelves. They do not meaningfully react to the robots as social agents.

Thus the study demonstrates:

> socially weighted robot navigation around synthetic moving pedestrians,

not full human-robot reciprocal interaction.

That does not invalidate the paper, but it should be stated explicitly in the limitations.

If the authors want stronger HRI claims, future validation should use recorded pedestrian trajectories, a reciprocal social-force pedestrian model, or physical human-in-the-loop experiments.

13. **[EDITORIAL / CONSISTENCY] Several smaller contradictions should be fixed in one final manuscript audit.**

The conclusion says:

> “we assess the outcome against the **three** aims”

and then immediately reports **A1, A2, A3 and A4**. 

Section VII-D still proposes a future “Weight Sensitivity & Calibration” study that perturbs each weight over a grid to determine whether the operating point is a plateau or ridge—even though Section VI-H has now performed exactly that experiment.  It should instead say future work will address joint/multivariate calibration, Pareto optimization, task-dependent tuning, or automatic weight selection.

Section III still says that **“mutual exclusion is coordinated”** by the directional reservation mechanism, although the Results section correctly and repeatedly states that the mechanism is **not mutual exclusion**.  The terminology should be made consistent throughout: “directional reservation with cost-projected diversion” is the evidence-supported term.

Finally, I would use the exact **3,910 simulations** rather than alternating between “3,900+”, “2,700” in repository documentation, and other historical counts.

---

# What would change my decision to acceptance?

The first three comments are the decisive ones.

If the authors:

**fix the matched social/yield-controller confound**,
**reformulate the reservation as a hard constraint rather than a fake tunable (w_R) weight**, and
**repair D* Lite's heuristic for (w_D<1) and rerun the sensitivity study**,

then I think the scientific foundation becomes substantially cleaner.

The social integral equation, safety ablation and single-file geometry also need correction, but those are technically straightforward compared with rebuilding the experimental framework they have already rebuilt several times.

I would strongly encourage the communication robustness test on Mechanism A and the local-social matched baseline because those two experiments would turn the paper from “plausible” into much more convincing.

## Why I would **not** permanently reject them

Earlier versions had reasons for rejection that went directly to scientific trust: synthetic result generation, tables contradicting figures, invalid baselines, incorrect timing, incorrect kinematics, stale data and overclaimed guarantees.

Those problems are largely gone.

The current repository contains actual simulation datasets with provenance, a much more disciplined analysis pipeline, paired statistics, explicit negative results, mechanism-specific experiments, expanded unit tests, corrected metrics and an extensively repaired bibliography. The authors have even published results that **weaken their own narrative**—for example, the broad benchmark shows mesh and reservation increasing makespan when their special operating conditions are absent.  That is exactly the kind of behavior I want to see from researchers revising a paper.

The remaining issues are serious, but they are **diagnosable and fixable**. They do not require inventing an entirely different research project.

### My official recommendation would therefore be:

**MAJOR REVISION — second round warranted.**

I would make this the **last major methodological round**, though. If the next revision merely rewrites the text around the matched-controller issue, (w_R), or the inadmissible low-(w_D) heuristic instead of actually correcting the implementation and rerunning the affected experiments, then I would recommend rejection. If they genuinely resolve those issues and the real results still support the conclusions, I think the paper could reasonably move toward **Minor Revision or Acceptance**.
