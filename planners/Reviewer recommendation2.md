# Peer Review — "Socially-Weighted Distributed Graph Optimization (D²RO) for Autonomous Multi-Agent Service Fleets in Crowded Environments"

**Recommendation: Major Revision (borderline Reject) — not acceptable in current form**

Below is the review as I'd submit it to the editorial board, followed by my summary recommendation.

## Summary of contribution
The paper proposes a 5-term edge-cost function combining D* Lite incremental replanning, V2V mesh telemetry, anisotropic Gaussian proxemics, corridor mutex locks, and a vehicle clearance term, evaluated on three simulated environments (retail, hospital, airport). The core idea — fusing global incremental search with social cost terms and distributed locking for single-file corridors — is a reasonable and not-unprecedented synthesis of existing techniques (D* Lite, ORCA-style local avoidance, proxemic potential fields).

## Major concerns

**1. Suspiciously fabricated/placeholder reference.** Reference [2] lists an author as "H.-V. Authors" — this reads as an unedited placeholder rather than a real name, and its co-authors ("J. Chen, S. Gao, and J. Zhang") cannot be verified as attached to any real "HA-VLN 2.0" CVPR paper. This alone is disqualifying until corrected; editors should verify every citation in this reference list independently, as this raises serious doubt about whether the literature review was genuinely conducted or partially fabricated/hallucinated.

**2. Internally inconsistent numbers.** The ablation results reported in prose (Section VI-B: 48.2, 95.3/94.7, 24.2) do not match the values in Table III (48.2, 94.7, 24.1) and Fig. 8 (48.8, 95.3, 24.2). Three different values are given for what should be the same measurement in three places. This is a basic data-integrity problem, not a typo.

**3. Implausibly clean results with selective error reporting.** D²RO reports exactly 100.0% success, 0.00 ± 0.00 deadlocks, and 0.00 ± 0.00 intimate violations across 20 randomized Monte Carlo trials — yet makespan for the *same* trials has real variance (22.00 ± 4.50 s). Zero variance across 20 stochastic human-in-the-loop trials on a discrete safety metric is not plausible for a "randomized" simulation; it suggests either the safety metrics weren't actually stochastic, or the numbers were not empirically derived. Real systems evaluated this way almost always show at least occasional edge-case failures.

**4. "Physically simulated" is an undefined/contradictory term.** Section VI opens with "100% physically simulated Monte Carlo experiments" — it's unclear whether this refers to physical hardware trials or a physics-based simulator. Given the described environment (2D floorplans rendered at 60 FPS with px-to-meter scale factors), this appears to be a lightweight 2D kinematic simulation, not physical hardware or a rigid-body engine (Gazebo/Isaac Sim, which the paper explicitly says it avoided). The "physically" framing overstates the experimental fidelity and should be removed or clarified.

**5. No ground-truth institutional affiliation or data/code availability.** The affiliation omits a named university, and the contact email (@research.org) is generic. The paper claims "4 open-access CSV datasets" and "10 camera-ready 300 DPI figures" but provides no repository link, DOI, or supplementary material reference. For a paper making strong empirical claims (100% success, sub-millisecond replanning), reproducibility artifacts are essential and currently absent.

**6. Weights are asserted, not derived or justified.** The five cost weights (wD=1.0, wM=1.5, wH=2.0, wR=1.0, wS=1.2) are stated as "calibrated" with no calibration procedure, sensitivity analysis, or ablation over weight values (only over whether a term is included at all). A reviewer cannot assess robustness to this hand-tuning, which is a common failure mode for cost-function-based planners deployed outside their tuned regime.

**7. Baselines are weak/mismatched.** ORCA is evaluated only as a *reactive local avoidance* method with no global planner behind it, guaranteeing it will fail in the exact scenario constructed to defeat it (a strawman comparison). A fairer baseline would combine ORCA with *some* global waypoint graph, or compare against a modern decentralized MAPF baseline actually cited in the related work (e.g., PRIMAL, Learn to Follow, or the Dergachev & Yakovlev hybrid approach that the paper says it draws its synthesis from in Section II-C).

**8. Manuscript metadata issue.** "Manuscript received August 15, 2026; revised October 20, 2026" — a revision date after the apparent submission/review date is inconsistent and should be corrected by the authors/editorial office before further processing.

## Minor concerns
- Figures 4–10 combine schematic floorplan mockups with plotted data in a way that make it hard to tell which elements are simulation output vs. illustrative diagram — captions should clarify.
- Table II shows D²RO with more V2V packets (39.10 ± 22.58) with very high relative variance (~58%) that isn't discussed.
- The claim that D* Lite guarantees optimality "with respect to the currently observed edge cost field" needs a formal proof or citation, not just an assertion, given this is listed as a "theoretical guarantee."
- Related work is reasonably thorough, but given concern #1, all citations should be re-verified for accuracy before acceptance.
- The four "target application fields" are described in detail but only three are actually evaluated (library/micro-fulfillment AGVs are dropped without comment).

## Recommendation to the editorial board
**I recommend Major Revision, bordering on Reject.** The technical framing (unifying incremental search, proxemics, and mutex locking) is a legitimate and interesting engineering synthesis, but the manuscript in its current state has (a) at least one apparently fabricated reference, (b) internally inconsistent reported results across text/table/figure, (c) implausibly zero-variance safety metrics that undermine confidence in the empirical claims, and (d) no data/code availability to support reproducibility. These are integrity and rigor issues that go beyond normal revision requests (e.g., weak baselines, missing sensitivity analysis). I'd ask the authors to:

1. Independently re-verify every reference, particularly [2].
2. Reconcile and re-report all ablation numbers with a single consistent source (ideally with raw data released).
3. Report actual variance/failure cases for safety metrics rather than exact zeros, or clearly justify why zero variance is expected.
4. Clarify simulation fidelity claims ("physically simulated") and provide code/data for reproducibility.
5. Strengthen baselines beyond a strawman ORCA-only comparison.

Would you like me to draft this as a formal reviewer report (e.g., for a journal's review portal, with numbered major/minor comments) or help revise the paper itself to address these issues?