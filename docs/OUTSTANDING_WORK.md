# Outstanding Work — D²RO

> **START HERE after cloning on a new machine.** This file is the complete handover:
> what is done, what is blocked, what to run, and every manuscript claim that still
> needs correcting. Nothing required to continue lives outside the repository.

**Status date:** 15 August 2026
**Context:** The code rebuild following the pre-submission audit is complete and
tested. All seven datasets have now been regenerated to completion, statistics and
manuscript artefacts are rebuilt from them, and the results/discussion/conclusion
have been rewritten around the real numbers. What remains is listed in §6.

---

## 0. Resuming on a new machine

```bash
git clone <your-repo-url> D2RO
cd D2RO

python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

# 1. sanity check - must be 53 passed
python -m pytest d2ro/tests/ -q

# 2. regenerate all datasets (~20 min; refuses to report success on short row counts)
PYTHONDONTWRITEBYTECODE=1 python run_full_suite.py

# 3. statistics  -> experiments/data/analysis_results.json + analysis_report.md
python paper/scripts/analyze_results.py

# 4. tables + figures -> paper/generated/*.tex, paper/figures/*
python paper/scripts/generate_tables_and_figures.py
```

If step 1 does not report **53 passed**, stop and fix that before anything else.

**Recovering the pre-rebuild data.** The datasets as they stood before this work are
in commit `2239939` ("adding the data files"). To inspect one without disturbing the
working tree:

```bash
git show 2239939:experiments/data/benchmark_comparison.csv > /tmp/old_benchmark.csv
```

**Two habits that cost time here — worth keeping:**

- Always run the suite with `PYTHONDONTWRITEBYTECODE=1`. Programmatic edits can evade
  Python's bytecode cache validation and make the interpreter run *old* code, which
  produces impossible-looking errors.
- If anything inexplicable appears right after a refactor, **bisect your own change
  first** before theorising about the environment.

---

## 1. The former blocker — RESOLVED

The execution problem that previously stopped six of seven experiments was
**environmental, not algorithmic**, and it is now closed.

On a different machine the entire suite runs to completion with **zero retries**:
all seven datasets, 2,700 rows, in ~20 minutes (against the 2–4 h previously
estimated under repeated failure). No access violations, no impossible-attribute
errors, no non-deterministic aborts.

```
[OK] 1   Benchmark comparison        rows=500/500    70.6s
[OK] 2   Component ablation          rows=500/500   180.1s
[OK] 3   Cross-domain benchmark      rows=300/300   160.5s
[OK] 4A  Crowd-density scalability   rows=600/600   276.0s
[OK] 4B  Fleet-size scalability      rows=600/600   523.9s
[OK] A   Mesh anticipation           rows=100/100     8.0s
[OK] B   Corridor mutex lock         rows=100/100    11.7s
```

The earlier failures were confined to one workstation. **This has no bearing on the
research and must never appear in the manuscript** — it was a local machine fault,
not a property of the method, the code, or the results. It is recorded here only so
that a future reader of this file understands why the datasets were once missing.

If the suite ever fails again, the diagnosis order is: run it on a second machine
first; only if it also fails there should the code be suspected.

### A note on stale bytecode (unrelated, but bit us once)

During this work, programmatic edits written within the same second and at identical
file sizes evaded Python's `mtime + size` bytecode cache validation, so the
interpreter executed **old** `.pyc` files against new data structures. This produced
its own crop of impossible errors. If you or a collaborator edit modules with
scripts, clear the cache before believing any symptom:

```bash
find . -name "__pycache__" -type d -not -path "./.git/*" -exec rm -rf {} +
```

The suite is now launched with `PYTHONDONTWRITEBYTECODE=1` to avoid this entirely.

---

## 2. What is finished and trustworthy

All code changes are complete, reviewed and covered by **53 passing tests**.

| Area | State |
|:--|:--|
| `S_trolley` as a genuine edge-cost term | Done — was previously never assigned, making the "5-component" cost function a 4-component one |
| Multi-hop V2V mesh (TTL, relaying, duplicate suppression, latency, packet loss) | Done — 10 dedicated tests |
| Distributed corridor reservation (grant/deny, FIFO fairness, priority, lease expiry) | Done — 10 dedicated tests |
| D* Lite optimality | Validated against fresh Dijkstra over 150 randomised scenarios comprising 750 successive repairs |
| Metric semantics (events vs exposure; one shared threshold for all planners) | Done |
| Cost-term normalisation to equivalent-detour metres | Done |
| Bounded onboard perception (7.2 m sensing radius) | Done |
| Experiments A and B rebuilt with programmatic precondition checks | Done |
| Time budgets recalibrated from measured mission durations | Done |
| Resume-and-append trap removed | Done |
| Dataset completeness verification | Done |
| Single statistics pipeline | Done — competing legacy writers now deleted, not merely unused |
| Table/figure generation from data | Done |

### Datasets

All seven datasets are complete and verified. `analyze_results.py` reports every one
as `ok` — not `provisional`, `unverified` or `STALE` — meaning each carries a
provenance stamp matching the current code fingerprint.

| Experiment | Rows | State |
|:--|--:|:--|
| Comparative benchmark | 500/500 | ✅ ok |
| Component ablation | 500/500 | ✅ ok |
| Cross-domain generalisation | 300/300 | ✅ ok (airport seed defect fixed — see below) |
| Crowd-density scalability | 600/600 | ✅ ok |
| Fleet-size scalability | 600/600 | ✅ ok |
| Mechanism A — mesh anticipation | 100/100 | ✅ ok |
| Mechanism B — corridor mutex | 100/100 | ✅ ok |

**Note on the provenance guard.** The fingerprint is a SHA-256 over the whole `d2ro/`
package, so *any* source edit marks *every* dataset `STALE` and requires a full
rerun. This is intended. Budget ~20 minutes whenever you touch the package.

---

## 3. Rebuilding everything from scratch

The full chain, in order (~20 min end to end):

```bash
# 1. regenerate every dataset (refuses to report success on short row counts)
PYTHONDONTWRITEBYTECODE=1 python run_full_suite.py

# 2. recompute all statistics
python paper/scripts/analyze_results.py

# 3. regenerate all data-driven tables and figures
python paper/scripts/generate_tables_and_figures.py

# 4. (only if the layouts changed) regenerate the qualitative illustrations
python paper/scripts/generate_topology_figures.py
python paper/scripts/generate_heatmaps_and_trajectories.py
```

Individual experiments can be run alone, which is useful on a flaky machine:

```bash
python run_full_suite.py --only 2      # component ablation
python run_full_suite.py --list        # show all keys
```

Then remaining work:

1. **Weight sensitivity study (Phase 5)** — not yet written. Vary each of the five
   weights by ×{0.5, 0.75, 1.0, 1.25, 1.5} and report success/makespan/social
   trade-offs. This answers the reviewer's "calibrated with no calibration
   procedure" objection, which is still open.
2. ~~Rewrite results and discussion~~ — **done**; see §4.
3. **Validate the ORCA baseline against a reference implementation** before any
   ORCA failure claim is made (see §4.5).
4. **Clean-room reproduction** on a machine that has never seen the project.

---

## 4. Findings that already change the manuscript

Findings 4.7–4.9 were discovered during the completed rerun and are the most
consequential; 4.1–4.6 predate it and have now been re-verified against real data.

### 4.7 Airport cross-domain results were n=1, not n=100 (FIXED)

`AirportScenarioSuite.get_scenario` scenario "A" called `random.seed(303)`
internally, clobbering the per-trial seed set by the runner. All 100 airport trials
were therefore byte-identical — makespan 71.25 ± 0.00, replans 968.00 ± 0.00. The
supermarket and hospital suites escaped this only by accident: their hard-coded seeds
sit in scenario "D", which the runner never calls.

Fixed by removing the call (`d2ro/environments/airport.py`). With per-trial variation
restored the airport domain reports **95.0% success, makespan 74.63 ± 35.71,
replans 959.16 ± 359.83** — replacing the previously reported 80.0%.

### 4.8 The corridor mutex works, but not by the mechanism the paper claimed

Mechanism B shows a large, real effect: success 88.0% vs 36.0% (p = 1.5e-4),
corridor occupancy 40.01 s vs 89.41 s. But:

- head-on encounters are **statistically unchanged** (1.08 vs 1.00, p = 1);
- the deadlock counter reads **0.00 in both arms**, so `N_deadlock = 0.00` cannot be
  credited to the lock;
- `lock_wait_s` is **0.00 ± 0.00** — agents essentially never queue.

Instrumented traces (25 seed-paired runs) explain it. The lock operates by
**cost-projected diversion**: `_apply_lock_costs` turns a peer's claim into an
infinite edge cost and D* Lite reroutes. Lock ON visited 2.16 nodes outside the
corridor and issued 21.7 replans; lock OFF visited 0.00 and issued 9.5. The manuscript
now describes this accurately and claims conflict *resolution*, not deadlock freedom.

Probe scripts used: `probe_lock.py`, `probe_lock2.py` (session scratchpad — rewrite if
needed; they only import the package, they do not modify it).

### 4.9 `lock_wait_time` is destroyed before it is read (OPEN, minor)

`TrolleyAgent._release_corridor` sets `self.lock_wait_time = 0.0`, and it is called
both on docking and on corridor exit. The experiments sum this attribute at the *end*
of the run, so any accumulated wait is already zeroed — which is why `lock_wait_s` and
`mutex_wait_s` are identically 0.00 everywhere. Peak-value probing shows the true
figure is small anyway (0.00 s in 8 of 10 seeds, ≤0.20 s in the rest), so the
reported conclusion does not change — but the metric as implemented cannot measure
what it claims. Fix by accumulating into a separate total that release does not reset.
**Note this requires a full 20-minute suite rerun** (provenance fingerprint).

### 4.10 Superseded findings, re-verified

- §4.1 (APF is not 0%) **confirmed** — APF now completes 100% at 34.54 ± 0.16 s.
- §4.3 (headline is a trade-off) **confirmed** — 99.0%/47.18 s vs A* 100%/18.00 s,
  intimate exposure median 0 vs 128.
- §4.5's hypothesis that Local MAPF's 0% was "substantially an artefact" **did not
  survive**: under the unified 0.84 m arrival radius MAPF still measures 0.0%.
  The ORCA caveat in §4.5 stands and remains blocking.

### 4.1 The APF "0% success" claim is wrong

The manuscript states APF achieves **0.0% success** and builds a local-minima
failure argument on it. With a fair time budget, **APF completes 100% of missions**
(37.40 ± 0.32 s). The old 0% was an artefact of the 35 s timeout, which was
calibrated for the earlier 30×-too-fast kinematics — not a property of the
algorithm. Section VI's failure-mode discussion needs rewriting.

ORCA and Local MAPF still measure 0%, but see §4.5 — those two results need
scrutiny before any failure-mode claim is made about them.

### 4.2 Social compliance is better described by median than mean

D²RO's intimate-space exposure has **median 0 [IQR 0, 0]** — most trials have zero
intrusion — with a mean of 9.41 driven by rare outliers. Reporting
"0.59 ± 5.90" implies a symmetric distribution that does not exist. The generated
table and figure now report median [IQR], with paired bootstrap intervals for the
differences.

### 4.3 The headline result is a trade-off, not a clean sweep

| | D²RO | Static A* |
|:--|--:|--:|
| Success | 99.0% | 100.0% |
| Makespan | 47.18 ± 13.40 s | 18.00 ± 0.00 s |
| Intimate exposure (median) | **0** | **128** |

D²RO pays ~2.6× makespan for a ~128-tick reduction in personal-space intrusion.
That is a defensible engineering trade-off and a stronger paper than "wins
everything". It should be framed as such.

### 4.4 Unequal arrival tolerance — baselines were handicapped (FIXED in code)

The planners did not share a common definition of "mission complete":

| Planner | Arrival radius |
|:--|--:|
| D²RO | 28.0 px = **0.84 m** |
| Local MAPF | 14.0 px = 0.42 m |
| APF / ORCA | 12.0 px = 0.36 m |

D²RO was scored with a **2.3× more lenient** arrival criterion than the methods it
was compared against, which inflates its success rate directly. Now unified to a
single `ARRIVAL_RADIUS_M = 0.84` (≈ one cart length) for every planner.

**The benchmark numbers in §4.1–4.3 predate this fix** and must be regenerated.
They are retained only as provisional evidence that the pipeline works.

### 4.5 Are the 0% results genuine algorithmic failure? — partly, and it differs by method

Instrumented single-trial traces (180 s budget, 4 carts):

**ORCA — looks like genuine algorithmic failure.**
Carts travelled only 1.9–19.2 m of a ~17 m mission and remained 10.9–16.2 m from
goal, stalled for **3258–3548 of 3600 control ticks** (91–99% of the run). That is
the velocity-obstacle infeasibility mode the paper describes: in narrow aisles the
half-plane constraints admit no feasible velocity and the agent halts. The claim
appears defensible — but see the caveat below.

**Local MAPF — substantially an artefact, not a clean failure.**
In the traced trial **2 of 4 carts docked successfully**, and the other two reached
within **1.2 m and 1.3 m** of their goals before the clock expired. They were not
livelocked or trapped; they were nearly finished. Under the old 0.42 m criterion
they were scored as total failures. This undermines the manuscript's
"permanent token-swapping live-lock" narrative, which should not be asserted until
the experiment is rerun with equal tolerances.

**Caveat on ORCA that must be resolved before publishing any ORCA claim.** The
reviewer previously found genuine bugs in this implementation. A stall rate above
90% is extreme, and an in-house implementation failing at 0% while the published
algorithm is widely used in practice is more likely to indicate an implementation
defect than a fundamental limitation. Before the paper asserts an ORCA failure
mode, the implementation should be validated against a reference (e.g. RVO2) on a
canonical benchmark. If it cannot reproduce reference behaviour on a known case,
the honest framing is "our implementation failed", not "ORCA fails".

### 4.6 Claims still to remove or correct

- `paper.tex:98` — "+48.3% deadheading makespan inflation" (stale; unsupported)
- `paper.tex:101` — "2,500 total trials" (wrong; state the true figure after rerun)
- `README.md` — says 2,500 in three places and 2,700 in one
- Deployment section (~line 610) — "D²RO addresses…", "localization is maintained
  via EKF…", "D²RO modulates…" describe systems that are not implemented. Must
  become future/conditional tense.
- Sensitivity analysis — the word "sensitivity" does not appear in the manuscript.

### 4.5 Bibliography

`paper/references.bib` still contains the incorrect entries the reviewer identified,
while `literature/D2RO.bib` already holds correct metadata for at least the Keskin
reference. The manuscript bibliography should be rebuilt from the verified library.

---

## 5. Deliberate design decisions

Recorded so they are not mistaken for oversights.

- **`α_turn` not implemented.** Equation (4) includes a turn penalty
  `α_turn·|Δθ|`. Implementing it correctly requires heading-augmented graph search
  — effectively rewriting D* Lite's state space, which is high-risk before a
  resubmission for a term the novelty does not rest on. The cornering deceleration
  in the motion layer is real and measurable. **Recommendation:** describe that
  accurately and drop `α_turn` from Eq. (4), or schedule the state-space change as
  future work.
- **Weak references reverted.** An attempt to hold mesh agents weakly destabilised
  long runs and solved no real leak — Python's cyclic collector already reclaims the
  agent↔mesh cycle. Strong references restored.
- **Worker-thread execution reverted.** Running the suite in a large-stack thread
  made stability worse, not better. Isolation now comes from per-experiment
  subprocesses.

---

## 6. Prioritised checklist

Work top to bottom. Items marked **[blocks submission]** must be resolved before the
paper can be sent anywhere.

### A. Regenerate the evidence
- [x] **DONE** Run the full suite to completion; all seven datasets report `OK` with
      matching row counts (2,700 rows, zero retries).
- [x] **DONE** `analyze_results.py` reports all seven datasets as `ok`.
- [x] **DONE** §4.1–4.3 re-checked against regenerated data. §4.1 and §4.3 hold;
      §4.5's "MAPF was only an artefact" hypothesis did **not** survive — MAPF still
      measures 0% under the unified arrival radius.

### B. Close the two open scientific questions
- [ ] **[blocks submission]** Validate the ORCA implementation against a reference
      (RVO2) on a canonical case. A >90% stall rate more likely indicates an
      implementation defect than an ORCA limitation. If it cannot reproduce reference
      behaviour, the honest claim is "our implementation failed", not "ORCA fails".
- [ ] Re-examine the Local MAPF result. In the traced trial 2 of 4 carts docked and
      the rest finished within ~1.3 m, which does not support a "permanent live-lock"
      narrative.

### C. Answer the reviewer's remaining objections
- [ ] **[blocks submission]** Weight sensitivity study (not yet written): vary each of
      the five weights by ×{0.5, 0.75, 1.0, 1.25, 1.5}; report success, makespan and
      social-exposure trade-offs. The word "sensitivity" does not currently appear in
      the manuscript.
- [ ] **[blocks submission]** Rebuild `paper/references.bib` from the verified
      `literature/D2RO.bib`. References [6], [11], [13], [14], [21] are wrong; audit
      every remaining entry rather than assuming only those are affected.
- [x] **DONE** Deployment section rewritten into conditional tense and retitled
      "Considerations for a Physical Deployment", with an explicit statement that none
      of the hardware described forms part of the evaluated framework.
- [ ] Decide the `α_turn` question (see §5): either drop it from Eq. (4) and describe
      the kinodynamic cornering model that genuinely exists, or schedule the
      heading-augmented state space as future work.

### D. Rewrite around the real numbers
- [x] **DONE** Stale "+48.3%" mesh claim removed.
- [x] **DONE** Trial count corrected to 2,700 throughout the manuscript.
- [ ] Fix README trial counts and superseded results table.
- [x] **DONE** APF failure-mode discussion rewritten; APF completes 100% of missions
      and is now criticised on social grounds (highest intimate exposure), not success.
- [x] **DONE** Headline framed as an explicit trade-off in the abstract, §VI-C and the
      conclusion.
- [x] **DONE** Every hand-typed table replaced with `\input{}` of a generated file.
      `paper.tex` now contains no hand-entered result numbers.

### E. Final gate
- [ ] Clean-room reproduction on a machine that has never seen the project: clone,
      fresh venv, run tests, run suite, regenerate statistics/figures/PDF, and confirm
      every manuscript number traces to committed raw data with no manual edits.
- [ ] Record the exact commit hash in the manuscript.

---

## 7. Where things live

| Path | Contents |
|:--|:--|
| `run_full_suite.py` | Suite driver with subprocess isolation, retries, completeness checks |
| `paper/scripts/analyze_results.py` | The single statistics pipeline |
| `paper/scripts/generate_tables_and_figures.py` | Tables and figures, generated from data only |
| `experiments/data/analysis_results.json` | Machine-readable single source of truth |
| `experiments/data/analysis_report.md` | Human-readable statistical report |
| `paper/generated/*.tex` | Generated LaTeX tables and figure floats for `\input` |
| `paper/scripts/generate_topology_figures.py` | Qualitative Figs. 5-7 (illustrative, not statistical) |
| `paper/scripts/generate_heatmaps_and_trajectories.py` | Qualitative Figs. 8-10 (illustrative, not statistical) |

### One rule about artefact ownership

There are exactly **two** kinds of figure script, and they must never overlap:

* **Data-driven** (`generate_tables_and_figures.py`) reads only
  `analysis_results.json`, and refuses to emit an artefact whose dataset is
  missing or stale. It owns every table, Figure 1 and the two scalability figures.
* **Qualitative** (`generate_topology_figures.py`,
  `generate_heatmaps_and_trajectories.py`) run the simulator to draw illustrative
  floorplans and trajectories. They own Figs. 5-10 and read no CSV.

Three legacy scripts were removed for violating this rule: `generate_paper_plots.py`
also wrote `fig1_benchmark_comparison.pdf`, so running it silently replaced the
provenance-checked Figure 1 with one built by non-provenance-aware code;
`sync_data_to_manuscript.py` and `verify_and_update_statistics.py` both wrote a
second, competing statistics report. **Do not reintroduce a script that writes an
artefact the data-driven pipeline owns.**

A baseline snapshot of the pre-rebuild CSVs, `paper.tex`, `references.bib` and
figures was taken before any overwrite; ask if you need it restored.
