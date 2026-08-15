I treated the uploaded **12-page PDF as the official manuscript under review**, and I re-audited the current `polla-fattah/D2RO` GitHub repository rather than relying on the previous review. The submitted manuscript is *Socially-Weighted Distributed Graph Optimization (D²RO) for Autonomous Multi-Agent Service Fleets in Crowded Environments*. 

## Reviewer recommendation: **Major Revision**

I would **not recommend acceptance in the present round**, but I also would **not recommend rejection**.

This is a very different situation from the previous version. The work has improved substantially. The authors have corrected several serious scientific mistakes, stopped overstating the results, rebuilt much of the implementation, improved the statistical design, and now expose negative findings rather than hiding them. The central idea is interesting enough to justify another revision cycle.

However, there are still several issues that affect the **validity of the conclusions**, not merely presentation. Most importantly, the officially submitted PDF does not correspond to the current GitHub state; the comparison baselines still do not share a matched motion/control model with D²RO; the real-time latency claim is based on a metric that is not actually measuring D* Lite replanning latency; the repository itself documents an open bug in the lock-wait metric; the five weights remain unvalidated; and the bibliography still contains demonstrably incorrect references.

So my current recommendation is:

| Criterion                    | Current assessment                               |
| ---------------------------- | ------------------------------------------------ |
| Research idea                | Good / potentially publishable                   |
| Honesty of interpretation    | **Much improved**                                |
| Core implementation          | Much improved                                    |
| Experiment design            | Improved, but issues remain                      |
| Statistics                   | Generally much improved                          |
| Reproducibility              | Improved, but submitted artifact is inconsistent |
| Baseline validity            | Still insufficient                               |
| Mathematical ↔ code fidelity | Improved, still incomplete                       |
| References                   | Not acceptable yet                               |
| Publication readiness        | **Major Revision**                               |

### What has improved substantially

The manuscript now presents the primary result as a **trade-off rather than universal superiority**. D²RO achieves 99% success, essentially eliminates intimate-space exposure in most trials, but takes 47.18 ± 13.40 s versus 18.00 s for Static A*. That is a much more scientifically credible headline. 

The experimental protocol is also much better. Trials are explicitly seed-paired, planners use a common 0.84 m arrival tolerance, the earlier unrealistic 35 s timeout was removed, and the analysis now uses paired tests, McNemar's exact test for binary success, Wilcoxon where appropriate, bootstrap intervals and Holm correction. 

I particularly appreciate that the authors now acknowledge that the previous APF failure result was wrong. APF actually completes 100% of its missions under the corrected timing model, and the paper now argues against it based on social exposure rather than falsely claiming navigational failure. 

Likewise, the paper now explicitly refuses to infer that ORCA or Local MAPF themselves are bad algorithms simply because the authors' implementations return 0% success. That restraint is correct and significantly improves the scientific tone. 

The ablation discussion is also now credible: the authors openly report that removing mesh and mutex actually improves makespan in the broad supermarket experiment, while the proxemics term is genuinely load-bearing. 

The current GitHub implementation has addressed many of my former code concerns. Physical velocity scaling has been corrected; D* Lite's moving-start update was repaired; social metrics have common semantics; the proxemic edge term is now genuinely integrated; the mesh implementation contains TTL forwarding, duplicate suppression, latency and packet-loss machinery; and dedicated tests have been added.

Those are meaningful improvements.

---

## Required revisions before acceptance

1. **The submitted PDF and the GitHub repository must be made identical and immutable. This is currently a blocking problem.**

   The official PDF that was submitted to you contains unresolved references such as **“Table ??”** and **“Fig. ??”** throughout the results section. For example, the mesh-ablation discussion refers to “Table ??,” the benchmark discussion says “Table ?? and Fig. 7,” and the cross-domain and scalability discussions contain the same problem.   

   More seriously, the provenance table on page 12 of the **official submitted PDF says all seven datasets are STALE**. Every experiment is marked as generated by one code fingerprint while the then-current code has another. 

   Yet the current GitHub repository now contains a generated provenance table saying all seven datasets are **complete**.  The latest repository commit also states that all seven datasets were regenerated and the manuscript rebuilt around them.

   This means the PDF sent to the journal is **not the manuscript currently represented by the repository**.

   The authors must create a release/tag such as `v1.0-review2`, regenerate all datasets, statistics, figures and PDF from that exact tag, put the Git commit SHA in the manuscript, and submit that exact PDF. The reviewer should not have to decide which of several states of the paper is authoritative.

2. **The Static A* and APF comparisons still confound the high-level planner with a different motion controller. This is the largest remaining scientific issue.**

   The manuscript says the experiments use non-holonomic unicycle dynamics. 

   D²RO actually uses bounded angular motion, waypoint steering, human yielding, inter-trolley spacing and collision correction.

   Static A*, however, directly does:

   `heading = atan2(...)`

   at every step and then moves directly along that heading at `max_speed * dt`. There is no bounded angular rate or comparable cornering/controller model.

   APF similarly directly converts the resultant potential-field vector into Cartesian velocity and integrates it holonomically; it does not use the same bounded unicycle controller as D²RO.

   Therefore the important result

   > D²RO = 47.18 s versus Static A* = 18.00 s

   cannot currently be interpreted purely as **“the time price of social awareness.”**

   Some of that difference may come from different low-level motion dynamics.

   I strongly recommend adding a **matched-controller Static A*** baseline: use exactly the same vehicle model, angular-rate limit, collision geometry, arrival criterion and low-level executor as D²RO, but freeze the high-level route and remove social/mesh/mutex costs. That comparison would isolate the contribution of SW-DGO much more cleanly.

   Ideally APF should also be subjected to the same kinematic constraints, or its timing comparison should be clearly qualified as cross-controller rather than planner-only.

3. **The claimed D* Lite “replan latency” is not what the code currently measures.**

   The manuscript repeatedly says D* Lite vertex repair requires roughly 0.09–0.19 ms and therefore uses under 0.4% of the 50 ms control budget. 

   But `TrolleyAgent.last_compute_time_ms` measures the elapsed time around the **entire `step()` call**: mesh processing, proxemic updates, safety-cost updates, collision/yielding logic, planning when triggered and kinematic motion.

   The scalability runner then averages `last_compute_time_ms` over **every agent tick**, including ticks in which no D* Lite repair occurred.

   That metric therefore cannot legitimately be called:

   > “D* Lite vertex repair latency.”

   They should instrument `compute_shortest_path()` directly and record only actual repair events. Report at least median, mean, 95th percentile and maximum repair time.

   Alternatively, if they intentionally want to measure the whole control cycle, rename it **controller-step compute time**. That may actually be an even stronger real-time result, but it is a different quantity.

4. **There is a documented open bug in the mutex waiting metric, and the manuscript relies on that broken metric for an interpretation.**

   This is important because I found the authors' own current repository documenting it.

   `docs/OUTSTANDING_WORK.md` states that `lock_wait_time` is reset to zero when `_release_corridor()` is called, while the experiments read it only at the end of the run. Therefore reported zero wait time cannot currently measure total waiting. The document explicitly labels this issue **OPEN** and says correcting it requires regeneration of the datasets.

   The code confirms:

   ```text
   self.lock_wait_time = 0.0
   ```

   during corridor release.

   But the manuscript uses `0.00 ± 0.00 s` waiting as **direct evidence** that the lock works through diversion rather than queueing. 

   That argument cannot remain until the metric is fixed and Experiment B is rerun.

   The qualitative interpretation may ultimately survive—the repository notes preliminary probing suggests waiting is small—but the published evidence must come from a correctly accumulated metric.

5. **The five weights need a sensitivity analysis before acceptance.**

   The paper still calls

   [
   [w_D,w_M,w_H,w_R,w_S]
   =====================

   [1.0,1.5,2.0,1.0,1.2]
   ]

   “calibrated,” while later admitting they were set by hand and that no sensitivity analysis has been conducted. 

   The repository's own outstanding-work document identifies this as unfinished work.

   Because the entire proposed method is explicitly a **weighted multi-component objective**, robustness to the chosen weights is not peripheral; it is central.

   At minimum, vary each weight over something like ×0.5, ×0.75, ×1.0, ×1.25 and ×1.5, preferably on a separate tuning/evaluation seed set. Show effects on success, makespan and social exposure. If no formal calibration was performed, replace “calibrated weights” with **“hand-selected nominal weights.”**

6. **The communication model has been improved, but latency is not correctly connected to the actual agent execution.**

   The current `MeshNetwork` has a substantially better design: TTL, multi-hop relaying, duplicate suppression, packet loss and `deliver_at` timestamps are implemented.  Dedicated unit tests also exercise those features.

   However, the actual `TrolleyAgent.process_inbound_mesh()` calls:

   `fetch_inbound(self.agent_id)`

   without supplying `current_sim_time`.

   `fetch_inbound()` defaults its time argument to infinity, in which case it immediately returns all packets regardless of their `deliver_at` timestamp.

   In other words, the network class can model latency, but the actual D²RO agent currently bypasses it.

   The fix is straightforward: pass simulation time into `process_inbound_mesh()` and then into `fetch_inbound(agent_id, current_time=...)`, followed by an integration test using a real `TrolleyAgent`, not merely mesh stubs.

   Furthermore, all reported experiments appear to instantiate `MeshNetwork` with the default **zero latency and zero packet loss**. Therefore the paper should not imply that the experimental results establish robustness to communication delay/loss. Either add a communication-robustness experiment or explicitly describe the reported evaluation as ideal-channel simulation.

7. **Experiment A is much better, but its manuscript description still does not exactly match the code.**

   The paper says Cart B is **10+ m behind Cart A** and outside sensing range. 

   The actual implementation checks something different: it computes the distance **from the follower to the blockage** and rejects trials unless that distance exceeds the 7.2 m sensing radius. The leader starts at `N_mid_1`; the follower starts at `N_back_1`.

   So the defensible statement is:

   > “The blockage is initially outside the follower's 7.2 m sensing radius.”

   Not necessarily:

   > “The follower is 10+ m behind the leader.”

   The manuscript should state the actual precondition.

   Also, the sensing implementation is **range-limited**, not true line-of-sight sensing: humans are selected based on Euclidean distance, without shelf occlusion testing. The paper should use “range-limited sensing” unless ray/visibility occlusion is added.

   Finally, “backtracking distance” is currently operationalized as cumulative **increase in Euclidean distance to the goal**.  That is reasonable, but should be explicitly defined. Alternatively measure true reverse/repeated edge traversal.

8. **Experiment B is now substantially more credible, but the terminology should be tightened.**

   The code now genuinely creates agents approaching the same designated single-file corridor from opposite ends, seeds the arrival offset before sampling, and counts head-on events as discrete geometric encounters rather than ticks.

   This resolves one of the major defects from the previous version.

   But the empirical result is very revealing: head-on encounters are unchanged, deadlock counts are zero in both arms, and the mechanism raises mission success through rerouting rather than classical mutual exclusion. The paper itself acknowledges this. 

   I would therefore avoid calling it a **mutex lock** in the strongest computer-science sense. “Directional reservation with cost-projected diversion” or “distributed bottleneck intent reservation” describes the demonstrated behavior much more accurately.

9. **The mathematical formulation should describe the evaluated algorithm, not a partly future algorithm.**

   Equation (4) includes an angular turn penalty (\alpha_{\text{turn}}|\Delta\theta|). Yet the paper later acknowledges that (\alpha_{\text{turn}}) is **not implemented** because the graph state is not heading-augmented. 

   I would not leave an unimplemented term inside the central mathematical definition of the evaluated system.

   Either remove the turn term from the evaluated formulation and place it under future work, or clearly label the more general formulation and separately state:

   [
   \alpha_{\text{turn}}=0
   ]

   in all reported experiments.

   Similarly, the implemented `S_trolley` includes a static shelf-clearance contribution plus a dynamic peer Gaussian, whereas the displayed equation mainly describes the inter-trolley component. The mathematical expression should match the actual code.

10. **The shelf “scrape” metric has the same event-versus-exposure semantic problem the authors correctly fixed elsewhere.**

    In the full configuration, the paper reports roughly 193 ± 170 shelf scrapes per trial. 

    The code increments `shelf_corner_scrapes` whenever a trolley is found inside the expanded shelf region during a control update.

    That means 193 does not necessarily mean **193 separate physical scrapes**. It may represent 193 control cycles requiring a collision/clearance correction.

    The authors already recognized this distinction for human exposure—the common metrics module separately records encounters and duration.

    The same treatment should be applied here:

    **distinct fixture-contact events**, **contact exposure time**, and optionally **minimum clearance**.

    Until then, call the current metric “shelf-overlap correction ticks” rather than “scrapes.”

11. **The benchmark statistics are much better, but the treatment of failed missions in makespan comparisons needs clarification.**

    The table reports **successful-mission makespan** for D²RO as 47.18 ± 13.40 s. But the inferential comparison uses `travel_time_s` for all paired trials—including the D²RO timeout/failure—so the quoted mean paired difference of 30.51 s is not simply 47.18 − 18.00.

    This is not necessarily wrong, but it needs explicit explanation.

    Better options are to report both:

    * time-to-completion among successful paired trials; and
    * a failure-aware analysis where timeout is treated as censored/non-completion.

    At a minimum, do not place a successful-only descriptive mean next to an inferential effect computed from all trials without explaining the difference.

12. **The ORCA and Local MAPF baselines should either be validated or visually de-emphasized.**

    I agree with the manuscript's current caution: the authors correctly state that 0% success may reflect implementation defects and that their substantive claims do not depend on these baselines. 

    However, Figure 7 still displays ORCA and MAPF as 0% beside D²RO, which visually communicates a comparison the text then tells the reader not to trust.

    Before final acceptance I would prefer either validation against a reference implementation such as RVO2/canonical MAPF tests, or moving those two implementations into a supplementary diagnostic analysis while keeping Static A* and APF as the primary validated baseline comparison.

    The repository itself still lists reference-baseline validation as outstanding work.

13. **The bibliography still requires a full reference-by-reference audit. Several entries are definitely wrong.**

    This remained unfixed in the latest `paper/references.bib`.

    For example, reference [11] attributes the negotiation-based decentralized MAPF paper to Keskin, Guler and Sen in *IEEE Transactions on Intelligent Vehicles*. The actual 2024 publication is by M. Onur Keskin, Furkan Cantürk, Cihan Eran and Reyhan Aydoğan in *Autonomous Agents and Multi-Agent Systems*, volume 38, article 10. ([Springer][1])

    Reference [13] is also incorrect. *Learn to Follow* is an AAAI 2024 paper by Alexey Skrynnik, Anton Andreychuk, Maria Nesterova, Konstantin Yakovlev and Aleksandr Panov, volume 38(16), pp. 17541–17549. ([AAAI Publications][2])

    Reference [6], the Dergachev/Yakovlev locally confined MAPF work, is a **CASE 2021 conference paper**, pp. 1489–1494, DOI 10.1109/CASE49439.2021.9551564—not the *Robotics and Autonomous Systems* article currently listed. ([IEEE Xplore][3])

    Reference [7] is also wrong. The relevant Gielis paper is Jennifer Gielis, Ajay Shankar and Amanda Prorok, *A Critical Review of Communications in Multi-robot Systems*, *Current Robotics Reports* 3, 213–225 (2022). ([Springer][4])

    The paper also says “HA-VLN 2.0 [21]”, but the reference supplied is not HA-VLN 2.0. The official HA-VLN 2.0 work is a later benchmark by Dong, Wu, He and collaborators; the earlier 2024 HA-VLN publication is also a different work/authorship than reference [21] as currently printed. ([GitHub][5])

    This is too many incorrect records to repair individually by guesswork. They need an automated DOI/publisher audit of **all references**.

14. **The current repository should have an actual release/CI reproduction gate before the final revision.**

    The repository has now become substantially more rigorous: provenance sidecars exist, generated tables exist, tests are present, and `pytest` is in the requirements.

    But the repository currently has no `.github/workflows` directory at the inspected commit, and I could not independently execute the suite in my environment because direct network cloning is unavailable here. Thus my assessment of execution is a **source/data audit**, not an independent replication.

    For the final revision, create CI that at least runs the unit tests and analysis/provenance checks. The full 2,700-run suite can remain a manually triggered/release workflow if runtime is too high.

---

## How I would judge the paper after these revisions

The core scientific story is now much stronger:

**Socially aware graph cost → major reduction in intimate-space exposure;
mesh → useful when information arrives before a meaningful divergence;
reservation → useful by converting peer intent into a route-level cost;
neither mechanism is universally beneficial;
fleet scaling has a real ceiling.**

That is a publishable story because it contains **conditions and limitations**, not merely a claim that D²RO beats everything.

The mechanism-A result is particularly interesting: the current generated data show mesh anticipation advancing rerouting by about 10.7 s, reducing backtracking from 2.73 m to 1.08 m, with both configurations still completing 100%.  That is a much more defensible claim than the older universal superiority narrative.

Likewise, Experiment B shows a genuine success-rate effect, 88% versus 36%, even though the interpretation of zero lock waiting must be repaired.

### My editorial position

If I were completing the official review form today, I would choose:

**Recommendation: MAJOR REVISION**

The paper is **not ready for acceptance in this version**, mainly because some of the remaining issues alter how important results must be interpreted. But unlike the earlier submission, I now think the underlying study is sufficiently promising and sufficiently improved that another revision is warranted.

The issues I would treat as **mandatory before acceptance** are: the submitted-PDF/repository provenance mismatch; matched low-level dynamics for the primary baseline comparison; correct timing instrumentation; the `lock_wait_time` bug plus Experiment B rerun; weight sensitivity; bibliography correction; and a clean tagged reproduction.

If those are resolved cleanly, I could realistically see the next version moving to **Minor Revision or Acceptance**, rather than returning for another major methodological cycle.

[1]: https://link.springer.com/article/10.1007/s10458-024-09639-8?utm_source=chatgpt.com "Decentralized multi-agent path finding framework and strategies based on automated negotiation | Autonomous Agents and Multi-Agent Systems | Springer Nature Link"
[2]: https://ojs.aaai.org/index.php/AAAI/article/view/29704?utm_source=chatgpt.com "Learn to Follow: Decentralized Lifelong Multi-Agent Pathfinding via Planning and Learning | Proceedings of the AAAI Conference on Artificial Intelligence"
[3]: https://ieeexplore.ieee.org/document/9551564 "Distributed Multi-Agent Navigation Based on Reciprocal Collision Avoidance and Locally Confined Multi-Agent Path Finding | IEEE Conference Publication | IEEE Xplore"
[4]: https://link.springer.com/article/10.1007/s43154-022-00090-9?utm_source=chatgpt.com "A Critical Review of Communications in Multi-robot Systems | Current Robotics Reports | Springer Nature Link"
[5]: https://github.com/UWMILab/HA-VLN?utm_source=chatgpt.com "GitHub - UWMILab/HA-VLN: Official implementation for \"HA-VLN 2.0: An Open Benchmark and Leaderboard for Human-Aware Navigation in Discrete and Continuous Environments with Dynamic Multi-Human Interactions\". · GitHub"
