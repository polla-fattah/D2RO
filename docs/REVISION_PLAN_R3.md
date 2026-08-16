# Revision Plan — Round 3 (Major Revision, final methodological round)

**Reviewer recommendation:** Major Revision, second round warranted. Not rejection.
**Source:** `docs/email2.md` (13 numbered comments, 3 blocking).
**Status date:** 16 August 2026.

> **The reviewer has set a hard condition.** They state this should be the *last*
> major methodological round, and that **if the next revision merely rewrites text
> around the three blocking issues instead of correcting the implementation and
> rerunning the affected experiments, they would recommend rejection.**
>
> Every blocking item below is therefore a code change plus a regeneration. None of
> them may be answered in prose.

---

## 0. The three blocking claims, verified against source

Checked before planning, as in Round 2. All three hold, and one is worse than
stated.

| # | Claim | Verified | Verdict |
|:--|:--|:--|:--|
| 1 | Matched baseline uses `enable_yield=False` while D²RO yields | `run_experiments.py` (matched arm construction) | **Correct** |
| 2 | `w_R` never multiplies anything | `graph.py` `Edge.cost` returns `inf` **before** applying `weight_r` | **Correct, and worse** |
| 3 | Heuristic inadmissible for `w_D < 1` | `dstar_lite.py:80-82` returns raw `graph.distance(u,v)` | **Correct** |

**On #2, the situation is stronger than the reviewer argues.** They note that
scaling a multiplier on infinity is meaningless. In fact `r_lock` is only ever
assigned `0.0` or `math.inf` (`agent.py:868`), nothing else, anywhere. So `w_R`
multiplies either zero or a value that has already short-circuited the cost
function. **It is inert in every reachable state, not merely usually inactive.**

This also means our own Round-2 explanation was wrong. Section VI-H currently
attributes the flat `w_R` sensitivity to the reservation being "rarely active in the
broad benchmark". The real reason is structural: the weight cannot have an effect
under any scenario. That sentence must be corrected, not merely supplemented.

**On #3, note why our tests missed it.** `test_dstar_optimality.py` validates against
Dijkstra over 150 randomised scenarios, but only at nominal weights. A test that
never varies `w_D` cannot detect a heuristic that is only inadmissible when
`w_D < 1`. The fix is not just the heuristic; it is the test's coverage.

---

## 1. What must be re-simulated, and what must not

Two independent forces require a rerun, and it is worth separating them.

**Mechanically:** the provenance fingerprint is a SHA-256 over all of `d2ro/`. Any
edit invalidates all nine datasets. The first code change forces regeneration
regardless of its size, so there is **no saving in skipping any individual code
fix** — batch them.

**Scientifically:** some fixes change results. Most importantly #3. At `w_D = 0.5`
and `0.75` the planner is currently running an inadmissible heuristic and may be
returning suboptimal paths, so the reported sensitivity figures
(`w_D ×0.5 → 63.8 s`, `×1.5 → 39.1 s`) are **suspect and must be regenerated
before they are quoted again**.

| Comment | Rerun? | Why |
|:--|:--|:--|
| #1 yield factorial | **Yes** | New arms |
| #3 heuristic | **Yes** | Changes routing at `w_D<1` |
| #5 safety-ablation split | **Yes** | New arms |
| #9 person-seconds | **Yes** | `intimate_exposure_s` is computed but never written to CSV |
| #7 comms on Mechanism A | **Yes** | New experiment |
| #6 local-social baseline | **Yes**, if added | New arm |
| #2 `w_R` → constraint | **Verify** | Should be behaviour-preserving; confirm, do not assume |
| #4 Eq. (10) arc length | **No** | Code is correct, equation is wrong |
| #8 corridor geometry | **No** | `is_single_file` is hardcoded per edge; no width rule exists in code |
| #10–#13 | **No** | Documentation, release hygiene, editorial |

---

## 2. Phase A — code (batched, single regeneration afterwards)

### A1. Yield/route factorial — *blocking, #1*

The current claim "≈28 s is attributable to the routing policy" is not established,
because the matched arm differs from D²RO in **two** ways at once: frozen route
*and* no reactive human response. The difference therefore confounds social graph
routing, dynamic replanning and reactive yielding.

**Design: a 2×2 factorial**, identical kinematics, collision geometry and arrival
criterion in every cell.

| Cell | Route | Yield | Note |
|:--|:--|:--|:--|
| A | frozen shortest path | OFF | today's "matched A\*" |
| B | frozen shortest path | ON | **expected to stall** — see below |
| C | social routing (D²RO cost field) | OFF | |
| D | social routing | ON | full D²RO |

Estimable effects:

- routing effect at yield OFF: `C − A`; at yield ON: `D − B`
- yielding effect on a frozen route: `B − A`; on a social route: `D − C`
- **interaction:** `(D − C) − (B − A)`

The interaction is the scientifically interesting quantity: it tests whether social
routing and reactive yielding are complementary or substitutes.

**Cell B is expected to fail, and that is a result, not a defect.** A frozen-route
agent that yields has no recourse when a pedestrian occupies its only path; a smoke
test during Round 2 showed exactly this (0% success, agents stalled to the time
budget). That observation is what motivated `enable_yield=False` in the first place
— but it was a decision made privately by us rather than a measurement reported to
the reader. The factorial converts it into evidence: *yielding without the ability
to replan is a trap*, which is itself an argument for the proposed method.

Report success separately from makespan, and state plainly that makespan in a cell
with near-zero success is not comparable (see A6 on censoring).

**This experiment also addresses exposure attribution.** Report intimate exposure
per cell, not just makespan. If `C` (social routing, no yielding) already achieves
near-zero exposure, the credit belongs to `H_prox`; if it does not, a share belongs
to the low-level push-back, and the manuscript must say so.

**Also define "yield" precisely in the paper.** `enable_yield` currently gates two
distinct behaviours — the positional push-back inside the intimate radius, and the
full stop when a human is ahead within range. Treat them as one composite *reactive
human response* and say so, rather than implying it is only a stop.

### A2. Reservation as a hard constraint — *blocking, #2*

Reformulate the objective as **four weighted soft terms subject to one feasibility
constraint**:

```
minimise   w_D·C_geom + w_M·C_mesh + w_H·C_social + w_S·C_kinematic
subject to e ∉ E_reserved,i(t)
```

Implementation: remove `weight_r` from `Edge` and from the cost expression; keep the
existing `r_lock == inf` short-circuit, which *is* the constraint, and document it as
such. Delete `w_R` from the sensitivity grid (21 configurations → 17).

**Verification requirement:** this should be behaviour-preserving, since `inf`
already short-circuits. Do not assume it — run the mechanism experiments before and
after on identical seeds and confirm the results are unchanged. If they differ,
something else was depending on `weight_r`.

### A3. Admissible heuristic + test coverage — *blocking, #3*

Set `h(u,v) = w_D_min · d(u,v)`, where `w_D_min` is the smallest distance weight
present in the agent's graph. This is a valid lower bound for any non-negative
combination of the remaining terms, and reduces to the current heuristic at
`w_D = 1`.

**Then extend `test_dstar_optimality.py` to sweep `w_D ∈ {0.5, 0.75, 1.0, 1.25,
1.5}`.** The existing 150-scenario Dijkstra comparison is sound but only ever ran
nominal weights, which is precisely why this defect survived. A fix without the test
extension leaves the same blind spot.

### A4. Split the safety ablation — *#5*

`enable_safety=False` currently removes the graph term **and** zeroes the safety
bubble, shelf margin and following gap, and disables inter-trolley safety behaviour.
The dramatic fixture-contact result therefore measures planner + controller
together.

Split the flag into `enable_safety_cost` and `enable_safety_controller`, then report
three arms: cost off / controller on; cost on / controller off; both off (the
current arm, relabelled **full-stack**).

Expect this to weaken the `w_S` graph-term claim. That is the point of doing it.

### A5. Local Social D\* Lite baseline — *#6, strongly recommended*

The reviewer's most valuable suggestion, and it needs no external package: a
`TrolleyAgent` with proxemics, yielding and safety **on**, dynamic replanning
**on**, but V2V mesh and reservation **off**. That is ordinary human-aware
navigation without the distributed layer.

`D²RO − LocalSocial` then answers the question a reader actually has: *what does the
distributed part add beyond human-aware navigation?* Without it, the validated
comparison is only against planners that ignore personal space, which the reviewer
fairly calls "somewhat expected".

Add it to the **benchmark**, not only the ablation, so it appears as a headline
comparator.

### A6. Metrics and export — *#9*

- Export `intimate_exposure_s` and `intimate_encounters` to CSV; they are already
  accumulated but never written.
- Report **person-seconds** as the primary social metric, with distinct encounters
  secondary. The current unit is person-ticks: `update_social_metrics` increments
  once per human per tick, so three humans inside the boundary add three, and "128
  control ticks" is really 128 person-ticks.
- Record per-trial timeout/censoring status explicitly so failure-aware makespan
  analysis is possible for cells like B.

### A7. Communication robustness where communication matters — *#7*

Repeat **Mechanism A** across the loss × latency grid and measure whether the
10.70 s anticipation lead, the backtracking reduction and the makespan advantage
survive degradation.

The existing broad-scenario sweep stays, but it is weak evidence by our own
admission, and the abstract currently overstates it. Either this experiment lands,
or the abstract's robustness sentence must be cut back to what the broad sweep can
support.

---

## 3. Phase B — one regeneration

```bash
python -m pytest d2ro/tests/ -q                      # incl. new w_D optimality sweep
PYTHONDONTWRITEBYTECODE=1 python run_full_suite.py
python paper/scripts/analyze_results.py              # every dataset must read ok
python paper/scripts/generate_tables_and_figures.py
python paper/scripts/verify_manuscript_claims.py
```

Expect appreciably longer than Round 2's 33 minutes: the benchmark gains the
factorial and local-social arms, and Mechanism A gains a 16-condition grid. The
sensitivity study gets cheaper (17 configurations).

**The total trial count will change.** Do not reuse 3,910; take the regenerated
figure and use it consistently everywhere, including the README.

---

## 4. Phase C — manuscript

| Item | Change | Comment |
|:--|:--|:--|
| C1 | Rebuild the attribution claim on the factorial; state routing, yielding and interaction separately | #1 |
| C2 | Reformulate Eq. (3) as 4 soft terms + 1 constraint; drop `w_R` from the sensitivity narrative and **correct the "rarely active" explanation**, which is wrong | #2 |
| C3 | Restate the admissibility claim with the corrected bound and note it holds for all evaluated `w_D` | #3 |
| C4 | Add the arc-length factor to Eq. (10): `∫ H_prox ds`, not `∫ H dτ` — the code is right, the equation is wrong | #4 |
| C5 | Relabel the safety ablation as full-stack and report the split arms | #5 |
| C6 | Report the local-social comparison as a primary result | #6 |
| C7 | Either report Mechanism-A-under-degradation or weaken the abstract | #7 |
| C8 | Define `r_safety`; derive the correct passing criterion (`W ≥ 4r` for two discs, or width-plus-clearance for rectangles); stop calling 0.40 m the "inscribed radius" of a 0.72 × 0.48 m chassis, whose true inscribed radius is 0.24 m | #8 |
| C9 | Report person-seconds; define the unit explicitly | #9 |
| C10 | Add pedestrian-model limitation: agents are non-reciprocal and do not respond to robots socially | #12 |
| C11 | Editorial sweep: "three aims" → four; rewrite Future Work item 1, since the sensitivity study it proposes has now been done (retarget to joint/multivariate calibration); remove "mutual exclusion is coordinated" from Section III; use one exact trial count | #13 |

**On C8, be honest rather than clever.** A 2.1 m aisle is not geometrically
single-file for 0.48 m-wide carts by any correct criterion. Either justify the
designation operationally (shelf overhang, standing shoppers, parked trolleys) and
say so, or change the designation — the latter alters topology and would require
another rerun. Recommend the former, stated plainly.

---

## 5. Phase D — release hygiene — *#10*

The manuscript currently claims release `v2.0-review2`, commit `e3d6582-dirty`,
while the repository has **no tags and no releases**. The `-dirty` suffix is our own
mechanism correctly reporting that the PDF was built from an unclean tree; the
reviewer read it exactly as intended.

1. CI: `pytest`, `analyze_results.py` provenance check, `verify_manuscript_claims.py`,
   and `audit_references.py`.
2. Build gate: fail on any `??` in `paper.log`, any dataset not `ok`, or a commit
   stamp ending `-dirty`.
3. Clean commit → tag `v3.0-review3` → regenerate everything → embed the clean SHA →
   submit that exact PDF.
4. **Update or archive `README.md` and `OUTSTANDING_WORK.md`.** Both still describe
   seven experiments and 2,700 trials, and the README still says weight sensitivity
   is unfinished. A reviewer must be able to reproduce the paper from a clean
   checkout with one command.

Also outstanding: **HA-VLN [21]** (#11) still needs an author decision — cite the
attributable version, cite the anonymous preprint explicitly, or drop the dependency
if the proxemic parameters do not actually rest on it.

---

## 6. Risk register — what could get worse

Stated up front, because two of these fixes can weaken the paper's claims and we
should not be surprised into defending them.

1. **The factorial may attribute much of the exposure benefit to reactive yielding
   rather than to `H_prox`.** If cell C does not achieve near-zero exposure, the
   social-cost term is less load-bearing than currently claimed.
2. **The safety split may show the graph term contributes little** relative to the
   reactive controller, weakening `w_S`.
3. **The corrected heuristic may change the sensitivity surface**, and the current
   plateau finding may not survive at low `w_D`.
4. **The `w_R` reformulation removes a "weight" from a paper whose framing is a
   five-component weighted objective.** The honest presentation is four weighted
   terms plus a constraint; the title and framing should not overstate five.

If any of these land badly, report them. That behaviour is the single thing the
reviewer has most consistently credited across three rounds.

---

## 7. Suggested order

| Phase | Work | Blocking? |
|:--|:--|:--|
| A3 | Heuristic + test sweep | **Yes** |
| A2 | Reservation as constraint | **Yes** |
| A1 | Yield/route factorial | **Yes** |
| A4 | Safety-ablation split | No |
| A6 | Metric export / person-seconds | No |
| A5 | Local-social baseline | Recommended |
| A7 | Mechanism A under degradation | Recommended |
| B | Single regeneration | **Yes** |
| C | Manuscript | **Yes** |
| D | CI, tag, docs, HA-VLN | **Yes** |

Do A3 first: it is small, self-contained, and its test extension guards the rest.
