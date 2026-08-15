# Revision Plan — Round 2 (Major Revision)

**Reviewer recommendation:** Major Revision — not acceptance, not rejection.
**Source:** `docs/email.md` (14 numbered points).
**Status date:** 15 August 2026.

This plan converts the reviewer's 14 points into ordered, executable work. Read §1
first: the sequencing constraint is the single thing most likely to waste days if
ignored.

---

## 0. Assessment: the review is correct

Every reviewer claim that can be checked against the source was checked. All of
them hold:

| # | Claim | Verified against | Verdict |
|:--|:--|:--|:--|
| 2 | Static A\* snaps heading (`atan2`) with no angular-rate limit; APF integrates holonomically; D²RO is rate-limited (`max_turn = max_omega*dt`) | `static_astar.py:115-118`, `artificial_potential_fields.py:141-143`, `agent.py:616-618` | **Correct** |
| 3 | `last_compute_time_ms` wraps the whole `step()`, and the runner averages it over *every* tick | `agent.py:463,632`, `run_experiments.py:188` | **Correct** |
| 4 | `lock_wait_time` is zeroed on corridor release before the experiment reads it | `agent.py:738` | **Correct** (we documented it ourselves) |
| 6 | `fetch_inbound(agent_id)` omits `current_time`, defaulting to `inf`, returning all packets regardless of `deliver_at` | `agent.py:137`, `mesh_network.py:176-184` | **Correct** |
| 6 | All experiments build `MeshNetwork` with default zero latency / zero loss | `run_experiments.py` | **Correct** |
| 11 | Descriptive makespan is successful-only; the paired test uses all trials | `analyze_results.py:300,315` | **Correct** |

There is no point contesting any of this. The plan below assumes all 14 points are
accepted and fixed.

**The honest risk, stated up front:** several of these fixes can *change the
results*, not merely their presentation. A matched-controller Static A\* will
probably narrow the 47.18 s vs 18.00 s gap substantially, because part of that gap
is currently controller mismatch rather than social routing. Fixing the mesh
latency bypass may alter Mechanism A. Fixing `lock_wait_time` may reveal non-zero
waiting and weaken the "diversion, not queueing" argument. **We must be prepared
for the headline to move, and to report whatever it becomes.** That is the whole
point of the exercise.

---

## 1. The sequencing constraint (read before starting)

The provenance fingerprint is a SHA-256 over the entire `d2ro/` package. **Any**
source edit marks **all seven** datasets `STALE` and forces a full regeneration
(~35 min on the current machine). Deleting one dead 246-line module already
triggered this once.

Therefore:

> **Batch every code change into Phase A. Do not regenerate datasets between
> individual fixes. Regenerate exactly once, in Phase C, when the code is frozen.**

Doing the eight code items separately would cost eight reruns (~4.5 h) and produce
seven intermediate dataset states that are individually meaningless. Doing them
together costs one.

Corollary: **do not start the manuscript rewrite (Phase D) until Phase C output
exists.** Numbers written before the regeneration will be wrong, and rewriting
prose twice is how the previous round went astray.

---

## 2. Phase A — Code changes (batched, one rerun after)

### A1. Matched-controller Static A\* — *reviewer #2, highest priority*

The largest remaining scientific issue. The 2.6× makespan claim currently conflates
"social routing costs time" with "D²RO has a rate-limited controller and the
baseline does not."

Add a new baseline that shares D²RO's **exact** low-level executor — same unicycle
model, `max_omega`, collision geometry, arrival radius, yielding layer — but with a
frozen shortest-path route and `w_M = w_H = w_R = 0`. That isolates SW-DGO.

Implementation options, in order of preference:
1. Instantiate `TrolleyAgent` with social/mesh/mutex weights zeroed and replanning
   disabled. Cheapest, and guarantees an identical executor by construction.
2. Failing that, refactor the motion layer out of `TrolleyAgent` into a shared
   executor both classes call.

Keep the *existing* unmatched Static A\* as a second, clearly-labelled baseline —
the difference between the two is itself an interesting measurement of how much of
the gap is controller versus planner.

Also apply the matched kinematics to APF, or explicitly label its timing comparison
cross-controller.

**Expected effect on results: large.** Plan for the headline to change.

### A2. Correct the latency instrumentation — *reviewer #3*

Two distinct quantities are currently conflated:

- Instrument `compute_shortest_path()` directly; record **only actual repair
  events**. Report median, mean, p95 and max — not a mean over all ticks.
- Rename the existing whole-`step()` measurement to **controller-step compute
  time** and keep it. As the reviewer notes, it may be the stronger real-time
  result; it is simply a different claim.

Emit both to CSV so the analysis can report them separately.

### A3. Fix the `lock_wait_time` reset — *reviewer #4*

`_release_corridor()` zeroes the accumulator that the experiments read at end of
run. Accumulate into a separate `total_lock_wait_time` that release never resets.
Add a unit test that asserts a known wait survives a release.

### A4. Connect mesh latency to agent execution — *reviewer #6*

`process_inbound_mesh()` must take `current_sim_time` and pass it to
`fetch_inbound(agent_id, current_time=...)`. Add an **integration** test using a
real `TrolleyAgent` (not a mesh stub) asserting that a packet with a future
`deliver_at` is not visible early.

### A5. Shelf-scrape metric semantics — *reviewer #10*

Currently counts control ticks spent overlapping the expanded shelf region, not
physical scrapes. Apply the same event/exposure split already used for human
proxemics: record **distinct fixture-contact events**, **contact exposure ticks**,
and optionally **minimum clearance**. Until then the metric must be called
"shelf-overlap correction ticks" in the text.

### A6. Promote the corridor-diversion probe to a real experiment — *supports #8*

The manuscript currently argues diversion-not-queueing from `lock_wait = 0` plus
diagnostic traces that are not in the released data. Add an experiment recording,
per trial: nodes visited outside the contested corridor, replan count, and wait
time. This makes the mechanism claim rest on committed data.

### A7. Heading-augmented search — *deliberately NOT implemented*

**Decision: no code change.** Implementing `α_turn` requires a heading-augmented
state space, which is effectively a rewrite of D\* Lite's search domain — high risk
for a term the paper's novelty does not rest on. The reviewer explicitly accepts
the alternative: remove it from the evaluated formulation, or state `α_turn = 0`.

Resolved as a manuscript change instead. **See D14 in Phase D.**

---

## 3. Phase B — New experiments (code, still before the rerun)

### B1. Weight sensitivity study — *reviewer #5, mandatory*

Vary each of the five weights by ×{0.5, 0.75, 1.0, 1.25, 1.5} holding others fixed
(25 configurations + nominal). Report success, makespan and social exposure.

**Use a separate seed set from the headline experiments** so that the reported
operating point is not tuned and evaluated on the same seeds.

Outcome either way is publishable: a broad plateau supports robustness; a narrow
ridge is an honest limitation. Until this exists, the text must say
**"hand-selected nominal weights"**, never "calibrated".

### B2. Communication robustness sweep — *reviewer #6*

All current results are ideal-channel. Either add a sweep over packet loss and
latency (e.g. loss ∈ {0, 5, 10, 20}%, latency ∈ {0, 50, 100, 200} ms) or state
plainly that the evaluation assumes an ideal channel. **Recommend doing the sweep**
— it directly answers "does the mesh survive realistic RF?", which the deployment
section gestures at.

### B3. ORCA / Local MAPF — validate or demote — *reviewer #12*

Two acceptable resolutions:
- **Validate** against RVO2 on a canonical benchmark; or
- **Demote** both to a supplementary diagnostic section and remove them from
  Figure 1, keeping Static A\* (matched + unmatched) and APF as the primary
  comparison.

**Recommendation: demote.** Validating a from-scratch ORCA against RVO2 is a
project in itself, and no claim in the paper depends on it. Demotion is cheap,
honest, and removes the figure that "visually communicates a comparison the text
then tells the reader not to trust."

---

## 4. Phase C — Single regeneration (code frozen)

```bash
python -m pytest d2ro/tests/ -q                          # must pass, count will rise
PYTHONDONTWRITEBYTECODE=1 python run_full_suite.py        # ~35+ min with new experiments
python paper/scripts/analyze_results.py                   # all datasets must report ok
python paper/scripts/generate_tables_and_figures.py
```

Gate: **every dataset `ok`**. Any `STALE`/`missing` means the code moved after
generation — stop and rerun rather than writing prose against it.

New generators will be needed for the sensitivity study, the communication sweep,
the diversion experiment and the split latency metrics.

---

## 5. Phase D — Manuscript revision (only after Phase C)

| Item | Change | Reviewer |
|:--|:--|:--|
| D1 | Rewrite the trade-off headline around the **matched-controller** comparison. This is the core narrative change | #2 |
| D2 | Split latency claims: D\* Lite repair (median/p95/max) vs controller-step time | #3 |
| D3 | Rebuild the Mechanism B argument on the corrected wait metric and committed diversion data | #4, #8 |
| D4 | Rename throughout: "mutex lock" → **directional reservation with cost-projected diversion** | #8 |
| D5 | Eq. (4): remove `α_turn` from the evaluated formulation (or state `α_turn = 0` in all experiments). Correct the `S_trolley` equation to match the implementation (static shelf clearance + dynamic peer Gaussian) | #9 |
| D6 | Experiment A: state the **actual** precondition (blockage outside the follower's 7.2 m radius, not "10+ m behind"); say **range-limited sensing**, not line-of-sight, unless occlusion is implemented; define "backtracking distance" explicitly | #7 |
| D7 | Makespan: report successful-only descriptives **and** a failure-aware/censored analysis; explain why the paired effect ≠ 47.18 − 18.00 | #11 |
| D8 | "calibrated weights" → "hand-selected nominal weights"; add the sensitivity section | #5 |
| D9 | State ideal-channel assumption, or report the robustness sweep | #6 |
| D10 | Rename the scrape metric per A5 | #10 |
| D11 | Move ORCA/MAPF out of Figure 1 into supplementary | #12 |
| D12 | Add the Git commit SHA and release tag to the manuscript | #1 |
| D13 | **Done.** Provenance table (was Table VII) removed from the manuscript — see below | #1 |
| D14 | **Action required.** Remove `α_turn` from Eq. (4) (carried over from A7, which was closed without code), and correct the displayed `S_trolley` equation to match the implementation — see below | #9 |

### D14 — the `α_turn` decision (ACTION REQUIRED in Phase D)

Carried here from A7, which was deliberately closed without code. **This is a
manuscript edit that must not be forgotten**: it is reviewer point #9, and the
inconsistency is currently visible in the central equation of the paper.

Equation (4) includes a turn penalty `α_turn·|Δθ|`. It is **not implemented** — the
graph state is not heading-augmented — so the displayed formulation describes a
system that was never evaluated. The reviewer will not accept an unimplemented term
inside the definition of the evaluated method.

Two acceptable resolutions; **take the first**:

1. **Remove `α_turn` from Eq. (4)** and describe instead the kinodynamic cornering
   deceleration that genuinely exists in the motion layer. Add the heading-augmented
   state space to Future Work.
2. Keep the general formulation but label it as such, and state explicitly that
   `α_turn = 0` in every reported experiment.

**Also in the same edit** (same reviewer point): the displayed `S_trolley` equation
describes only the inter-trolley Gaussian, whereas the implementation is a static
shelf-clearance contribution *plus* a dynamic peer Gaussian. Correct the equation to
match the code.

### D13 — why the provenance table was removed (already applied)

The table listed each dataset as `complete`/`STALE`. It is an **internal QA
artefact and does not belong in a manuscript**: it can only ever report that
everything is fine, which every published paper implicitly asserts anyway, or that
everything is broken — which is exactly what the submitted PDF did, and what the
reviewer led their required-revisions list with. Its expected value in the paper is
zero at best and self-harming at worst. It is also redundant internally, since
`analysis_report.md` already carries the same status table.

Replaced by one sentence in Data & Code Availability stating that all artefacts are
generated from committed data, plus the release tag and commit SHA. The SHA is
emitted by `generate_tables_and_figures.py` into `generated/commit.tex` as
`\PaperCommitSHA`, derived from `git rev-parse` at generation time and suffixed
`-dirty` if the tree has uncommitted changes — so a manuscript built from
uncommitted code says so instead of citing a commit it does not match.

The internal check has not been lost; it has been moved to where checks belong. The
CI gate in Phase F enforces it mechanically.

---

## 6. Phase E — References audit — *reviewer #13, mandatory*

The reviewer identified five wrong entries and correctly concluded there are too
many to fix by guesswork. **Audit every entry programmatically**, not just the five.

Known corrections supplied by the reviewer:

| Ref | Correction |
|:--|:--|
| [6] | Dergachev & Yakovlev — **CASE 2021**, pp. 1489–1494, DOI 10.1109/CASE49439.2021.9551564 (not *Robotics and Autonomous Systems*) |
| [7] | Gielis, Shankar & Prorok, *A Critical Review of Communications in Multi-robot Systems*, **Current Robotics Reports 3**, 213–225 (2022) |
| [11] | Keskin, Cantürk, Eran & Aydoğan, **Autonomous Agents and Multi-Agent Systems 38**, art. 10 (2024) — not Keskin/Guler/Sen in *IEEE T-IV* |
| [13] | Skrynnik, Andreychuk, Nesterova, Yakovlev & Panov, **AAAI 2024**, 38(16), 17541–17549 |
| [21] | Cited as "HA-VLN 2.0" but the entry is a different work — resolve which is intended |

Method: extract every DOI/title from `references.bib`, query Crossref, diff the
returned authors/venue/year/pages against the entry, and report mismatches. Rebuild
from `literature/D2RO.bib` where that is already verified. Treat *every* remaining
entry as suspect until machine-checked.

---

## 7. Phase F — Release gate — *reviewer #1 and #14, mandatory*

Reviewer point #1 is a **blocking process failure**, not a science problem: the
submitted PDF contained `Table ??` / `Fig. ??` and a provenance table saying all
seven datasets were STALE, while the repository said otherwise. A reviewer should
never have to decide which state of the paper is authoritative.

1. **CI** (`.github/workflows/`): run `pytest` and the provenance/staleness check on
   every push. The full 2,700-run suite stays a manually-triggered/release
   workflow.
2. **Build gate:** fail the build if `paper.log` contains any undefined reference
   (`??`) or if `analyze_results.py` reports any dataset not `ok`. Both failures
   that reached the reviewer would have been caught mechanically.
3. **Tag** `v2.0-review2`; regenerate datasets, statistics, figures and PDF from
   that exact tag; embed the commit SHA in the manuscript; submit **that** PDF.

**A subtlety to resolve in Phase F.** The commit stamp is generated *before* the
commit it names, so a locally built PDF can never cite its own commit — it cites
the parent and reports `-dirty`. The clean resolution is to stop committing
`paper.pdf` and have CI build it from the tag, where the checkout SHA is exactly
the tag's SHA and the tree is guaranteed clean. Until that exists, treat any PDF
whose stamp ends in `-dirty` as **not submittable**.

---

## 8. Suggested order and rough effort

| Phase | Work | Effort | Blocking? |
|:--|:--|--:|:--|
| A1 | Matched-controller Static A\* | **done** | **Yes** |
| A2 | Latency instrumentation split | **done** | **Yes** |
| A3 | `lock_wait_time` fix + test | **done** | **Yes** |
| A4 | Mesh latency wiring + integration test | **done** | **Yes** |
| A5 | Fixture-contact event/exposure split | **done** | No |
| A6 | Diversion evidence in Experiment B | **done** | No |
| B1 | Weight sensitivity (25 configs) | 1 d + runtime | **Yes** |
| B2 | Communication robustness sweep | 0.5 d + runtime | No |
| B3 | Demote ORCA/MAPF to supplementary | 2 h | **Yes** |
| C | Single regeneration + analysis | ~1 h wall | **Yes** |
| D | Manuscript revision | 2–3 d | **Yes** |
| E | Reference audit (automated) | 0.5 d | **Yes** |
| F | CI + build gate + tagged release | 0.5 d | **Yes** |

**Roughly 8–11 working days**, dominated by A1, B1 and D.

The reviewer states that if the mandatory items are resolved cleanly, the next
round could reach Minor Revision or Acceptance. The mandatory set is: PDF/repo
provenance, matched dynamics, timing instrumentation, the `lock_wait` fix plus
Experiment B rerun, weight sensitivity, bibliography, and a clean tagged
reproduction.

---

## 9. What not to do

- **Do not** regenerate datasets between individual code fixes (§1).
- **Do not** write manuscript numbers before Phase C completes.
- **Do not** defend the current Static A\* comparison. It is confounded, the
  reviewer proved it from the source, and the matched baseline is the stronger
  paper regardless of which way the number moves.
- **Do not** hand-fix the five named references and stop. The reviewer explicitly
  asked for an audit of all of them.
- **Do not** implement `α_turn` to satisfy point #9. Removing it from the evaluated
  formulation is the cheaper and equally acceptable resolution.
