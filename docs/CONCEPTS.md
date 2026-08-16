# Concepts used in this project

Two vocabularies meet here: the **research** concepts the paper argues with, and
the **engineering** concepts the repository is built from. This is a reference
for both, with pointers to where each one actually lives in the code.

Companion documents: [`ENGINEERING_NOTES.md`](ENGINEERING_NOTES.md) for how the
pipelines fit together and why, [`OUTSTANDING_WORK.md`](OUTSTANDING_WORK.md) for
what is still open.

---

# Part I — Research concepts

## Planning and search

**Topological roadmap.** The floorplan is an undirected graph of waypoints, not
an occupancy grid. From it each agent derives its own *directed* cost graph, so
`(u,v)` and `(v,u)` can differ — necessary because reservation is directional.
→ `d2ro/core/graph.py`

**D\* Lite.** Incremental replanning: when edge costs change, repair only the
affected subgraph instead of searching from scratch. This is what makes a
constantly-changing cost field affordable at 20 Hz. → `d2ro/core/dstar_lite.py`

**Heuristic admissibility.** The heuristic must never overestimate: `h ≤ c*`.
Plain Euclidean distance is admissible only while `w_D ≥ 1`. At `w_D = 0.5` an
edge costs `0.5d` while the heuristic claims `d`, so the search silently returns
**suboptimal paths**. Fixed by scaling: `h = min(w_D) · d`. Verified against
Dijkstra over 150 scenarios and the whole weight grid.
→ `d2ro/tests/test_dstar_optimality.py`

## Cost formulation

**Weighted multi-objective edge cost.** Four soft terms summed with
dimensionless weights `[w_D, w_M, w_H, w_S] = [1.0, 1.5, 2.0, 1.2]`.

**Soft term vs hard constraint.** The distinction the paper turns on. A weight
multiplying a `{0, ∞}` quantity has no operative magnitude — `w·∞ = ∞` and
`w·0 = 0` for every `w`. Reservation is therefore feasibility, not an objective
term, and cannot be swept in a sensitivity study.

**Dimensional normalisation.** All penalties expressed in *equivalent detour
metres*. Without it the terms are incommensurable — the proxemic penalty was
two orders of magnitude larger than edge distance, so the planner was minimising
discomfort alone and the distance term was inert. → `d2ro/core/units.py`

## Social navigation

**Proxemics / Hall's zones.** Personal space as graded cost rather than a
binary obstacle. Modelled as a **2D asymmetric Gaussian** aligned to the
pedestrian's heading — wider in front than behind, because approaching someone
head-on is more intrusive than passing behind them. → `d2ro/core/human.py`

**Anticipatory vs reactive.** A cost field evaluated over a planning horizon
routes *around* a person; a repulsive force law fires once they are already
close. The difference is why APF records the highest exposure of any planner
that completes its missions.

## Multi-agent coordination

**MAPF.** Multi-agent path finding — the classical framing, which optimises
throughput among robots and prices no human comfort.

**V2V mesh with exponential decay.** Peer-to-peer telemetry where observations
become time-decayed edge penalties. Decay matters: stale information expires on
its own, so a dropped packet cannot permanently poison the routing graph.
→ `d2ro/core/mesh_network.py`

**Perception horizon extension.** The mesh's purpose — an agent acts on a
blockage beyond its own sensing radius.

**Directional reservation with a total order.** Symmetric conflicts need
symmetry breaking; the total order supplies it without a central arbiter.

**Cost-projected diversion.** What the reservation *actually* does, discovered
by measurement rather than assumed: agents leave the contested corridor rather
than queueing for it. Head-on encounters are statistically unchanged and total
waiting is 0.03 s, so calling it a "mutex" was wrong.

**Velocity obstacles / ORCA.** Reciprocal collision avoidance. In a corridor
narrower than twice the safety envelope the half-plane constraints admit no
feasible velocity and the agent halts.

**APF local minima.** Repulsive and attractive vectors cancel at concave
corners.

## Metrics

**Person-time, not robot-time.** The exposure counter increments once *per
human per tick*, so two people near the robot for one second is two
person-seconds. → `d2ro/core/metrics.py`

**Person-seconds, not ticks.** Tick counts are artefacts of `dt = 0.05 s` and
mean nothing if the step changes. Rank tests are invariant to the rescale, but
effect sizes need a real unit.

**Exposure rate.** Person-seconds *per minute of mission*. Total exposure
conflates how intrusive an agent is with how long it is present — and the two
can point in opposite directions.

**The four metric families.** Navigation efficiency and throughput; social
comfort and pedestrian safety; deadlock robustness and conflict resolution;
computational cost and mesh traffic.

## Experimental design

**Ablation vs factorial.** Removing one component at a time vs crossing factors
so interactions are visible.

**Matched control.** A baseline differing in exactly one respect. The
matched-controller arm shares D²RO's kinematics and safety envelope and differs
only in routing policy, so the comparison isolates routing from vehicle
dynamics.

**Equal-competence control.** The sharpest idea in the study. Comparing a
socially-weighted *distributed* planner against a socially-blind one cannot
separate "social" from "distributed" — the social half wins regardless. Local
Social D\* Lite holds social competence fixed and varies only the coordination
architecture.

**Mechanism isolation.** Construct the topology a mechanism exists for, instead
of hoping a randomised scenario produces it.

**Base rate.** The missing piece: *per-event effect × frequency of the event =
expected benefit*. We have the first and not the second.

## Statistics

**Paired / within-subject design.** Every planner sees the same seed, so the
crowd a baseline faces is the crowd D²RO faces. This licenses paired tests,
which are far more powerful than independent-samples ones.

**Wilcoxon signed-rank** for continuous paired outcomes that fail normality;
**paired t** where they pass; **exact McNemar** for paired binary outcomes.
Comparing 100% against 12% as independent proportions throws away the pairing.

**Holm correction** within a declared family of comparisons.

**Bootstrap confidence intervals** for the mean paired difference, where the
distribution is too skewed to trust a parametric interval.

**Zero inflation and skew.** When 96% of trials record exactly zero, the mean
is not a summary of anything. Report median [IQR] alongside.

**Interaction contrast.** `(D − C) − (B − A)` — does the effect of one factor
depend on the level of the other?

**Confounding.** Total exposure mixed intrusiveness with mission duration. The
cells differed 9× in how long a mission lasted, and normalising **reversed the
interaction's sign** (−42.81 person-s → +3.22 person-s/min).

**Null results.** An unrejected null *bounds* an effect; it does not establish
absence. "No statistically detectable additional reduction" ≠ "adds nothing."

**Statistical vs practical significance.** Latency effects were detectable
(*p* ≤ 10⁻⁴) and negligible (≤ 0.55 s).

## Framing

**Attribution.** Is the effect a property of this component, or of the whole
system? Most of the experimental design exists to answer this.

**Boundary conditions as findings.** "When does this help?" is more useful, and
harder to attack, than "this helps."

**Bounded claims.** Cross-topology transfer *within one simulation family*, not
generality.

**Negative results about your own contribution.** Reporting that the
distributed layer is unnecessary in the broad scenario is a large part of why
the paper stopped being rejected.

---

# Part II — Engineering concepts

## Provenance

**Content fingerprinting.** Hash the inputs to decide whether the outputs are
still valid. A SHA-256 over all of `d2ro/` is written beside every CSV.
→ `d2ro/sim/run_experiments.py::_code_fingerprint`

**Fail-closed staleness.** The analysis *refuses* to report a dataset whose code
has changed, rather than warning. A warning gets ignored; a refusal does not.

**Cross-platform determinism.** Normalise line endings and sort paths globally
before hashing. Without either, a Windows and a Linux checkout disagree and
every dataset reads STALE on the other machine. Both were real bugs.

**Snapshot freshness.** The same idea applied to the WASM bundle, which embeds
a copy of the sources. → `scripts/check_web_bundle.py`

## Single source of truth

**One pipeline, one JSON.** `analysis_results.json` is the only thing
downstream reads. → `paper/scripts/analyze_results.py`

**Generated vs authored.** `paper/generated/` is machine-written and never
hand-edited; each file says so in its header.

**Placeholders over stale values.** When a dataset is unusable the generator
emits a visible placeholder, so a missing experiment can never be silently
represented by leftovers from an earlier run.

## Verification as code

**Claim verification.** Every number in the prose pinned against the data — 58
of them. Generated tables cannot drift; prose does.
→ `paper/scripts/verify_manuscript_claims.py`

**Release gating.** One command answering submittable / not, with twelve checks.
→ `paper/scripts/release_gate.py`

**Semantic linting.** Grep for *contradictions*, not just errors: superseded
terminology, aim counts, nulls stated as absence, p-values that appear nowhere
in the analysis output.

**Bounds over point estimates.** For quantities that do not reproduce — wall
clock timings — assert what survives a rerun.

**Test the checker.** `test_provenance_fingerprint.py` tests the guard itself.
If the writer and verifier ever disagree, every dataset reads STALE forever and
no amount of regeneration fixes it.

## Reproducibility discipline

**Deterministic seeding**, and **seed pairing** across arms.

**Subprocess isolation** with row-count completeness checks, so one crash cannot
silently truncate a dataset. → `run_full_suite.py`

**Atomic writes.** Never leave a half-written CSV.

**`PYTHONDONTWRITEBYTECODE=1`.** Stale `.pyc` files have made this repo execute
old code and produce impossible-looking errors.

## Document engineering

**Generated fragments.** Tables are `\input`, never pasted.

**Conditional compilation.** `\ifanonymous` drives the author block, both
running heads, the repository URL and the acknowledgment from one switch.

**Provenance stamp in the document.** `\PaperCommitSHA` names the commit whose
sources produced the PDF.

**Escape hazard.** Editing `.tex` through anything that interprets backslash
escapes turns `\textbf` into TAB + `extbf`. Bit this project four times. Write
patch scripts as files with raw strings, never inline heredocs.

## Release and distribution

**Allowlist publishing.** Export a named subset to a separate public repo,
copying files rather than splitting history, so nothing private can travel.
→ `scripts/publish_public.py`

**Why not `git subtree split`.** It needs a single prefix, and moving files
changes the paths the fingerprint hashes.

**Dirty-tree detection** that distinguishes uncommitted *sources* from
regenerated artefacts — otherwise every build reports dirty.

---

## The thread running through both halves

Part II exists to make Part I checkable. Every mechanism in the engineering half
replaces *"we were careful"* with *"it cannot be otherwise"* — and every concept
in the research half replaces *"our system is better"* with *"this component
causes this effect, under these conditions."*

That pairing is what moved this manuscript from reject to minor revision.
