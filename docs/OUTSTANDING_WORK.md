# Outstanding Work — D²RO

> **START HERE after cloning on a new machine.** This file is the complete handover:
> what is done, what is blocked, what to run, and every manuscript claim that still
> needs correcting. Nothing required to continue lives outside the repository.

**Status date:** 15 August 2026
**Context:** Code rebuild in response to the final pre-submission audit is complete
and tested. Experiment execution is blocked by hardware instability on the original
workstation, not by the code.

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

# 2. regenerate all datasets (2-4 h; refuses to report success on short row counts)
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

## 1. The blocker (read this first)

Six of the seven experiments could not be run to completion on this machine.

**Symptom.** Long simulation runs abort with a Windows access violation
(`0xC0000005`), or surface logically impossible Python errors — an attribute holding
an agent object where the source can only ever assign a `set`; `math.exp` appearing
as a `float`. Short runs are unaffected: the 53-test suite passes consistently in
under a second.

**Assessment.** This is memory corruption at the process level, and it is
non-deterministic — the same command succeeds and fails on consecutive attempts.
The machine has reportedly been running under thermal stress and other well-behaved
applications crash on it too. **The most probable cause is failing RAM**, not the
D²RO code.

**Evidence pointing away from the code:**

- The one experiment that completed (`benchmark_comparison.csv`, 500 rows) produced
  clean, internally consistent, statistically sensible results.
- Failures occur at varying, arbitrary source locations, including lines that
  perform only float arithmetic.
- Free memory was ample (15 GB of 31.6 GB) when failures occurred.
- Unit tests never fail.

### Before assuming the code is at fault

1. Run a memory diagnostic: `mdsched.exe` (Windows Memory Diagnostic), or
   MemTest86 from USB for a thorough overnight pass.
2. Check CPU/GPU temperatures under load; thermal throttling and instability often
   travel together.
3. Try the suite on a different machine, or under WSL/Linux:
   ```bash
   python -m pytest d2ro/tests/ -q
   python run_full_suite.py
   ```
   If it completes there, the code is fine and the workstation is the fault.
4. If Windows Defender real-time scanning covers this folder, add an exclusion —
   scanners injecting into a process that writes files in a tight loop can produce
   this class of instability.

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
| D* Lite optimality | Validated against fresh Dijkstra over 750 randomised trials |
| Metric semantics (events vs exposure; one shared threshold for all planners) | Done |
| Cost-term normalisation to equivalent-detour metres | Done |
| Bounded onboard perception (7.2 m sensing radius) | Done |
| Experiments A and B rebuilt with programmatic precondition checks | Done |
| Time budgets recalibrated from measured mission durations | Done |
| Resume-and-append trap removed | Done |
| Dataset completeness verification | Done |
| Single statistics pipeline | Done |
| Table/figure generation from data | Done |

### Datasets

| Experiment | Rows | State |
|:--|--:|:--|
| Comparative benchmark | 500/500 | **Provisional** — complete, but generated before the arrival-tolerance fix; must be rerun |
| Component ablation | 0/500 | Blocked |
| Cross-domain generalisation | 0/300 | Blocked |
| Crowd-density scalability | 0/600 | Blocked |
| Fleet-size scalability | 0/600 | Blocked |
| Mechanism A — mesh anticipation | 0/100 | Blocked |
| Mechanism B — corridor mutex | 0/100 | Blocked |

---

## 3. To finish once the hardware is sound

```bash
# 1. regenerate every dataset (refuses to report success on short row counts)
PYTHONDONTWRITEBYTECODE=1 python run_full_suite.py

# 2. recompute all statistics
python paper/scripts/analyze_results.py

# 3. regenerate all tables and figures
python paper/scripts/generate_tables_and_figures.py
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
2. **Rewrite results and discussion** around whatever the reruns produce.
3. **Validate the ORCA baseline against a reference implementation** before any
   ORCA failure claim is made (see §4.5).
4. **Clean-room reproduction** on a machine that has never seen the project.

---

## 4. Findings that already change the manuscript

These hold regardless of the pending reruns.

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
- [ ] **[blocks submission]** Run the full suite to completion on sound hardware; all
      seven datasets must report `OK` with matching row counts.
- [ ] Confirm `analyze_results.py` reports every dataset as `ok` — **not**
      `provisional`, `STALE` or `unverified`. If it does not, the numbers do not
      match the code and must not be published.
- [ ] Re-check §4.1–4.3 conclusions against the regenerated data; they were computed
      before the arrival-tolerance fix and may change.

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
- [ ] **[blocks submission]** Rewrite the deployment section (~line 610) into
      future/conditional tense. It currently states that EKF/UWB/LiDAR fusion and
      load-cell modulation are in place; none of it is implemented.
- [ ] Decide the `α_turn` question (see §5): either drop it from Eq. (4) and describe
      the kinodynamic cornering model that genuinely exists, or schedule the
      heading-augmented state space as future work.

### D. Rewrite around the real numbers
- [ ] Remove the stale "+48.3%" mesh claim (`paper.tex:98`).
- [ ] Replace "2,500 total trials" (`paper.tex:101`) with the true count.
- [ ] Fix README trial counts (says 2,500 in three places, 2,700 in one).
- [ ] Rewrite the APF failure-mode discussion — with a fair time budget APF
      completes 100% of missions (see §4.1).
- [ ] Frame the headline as an explicit trade-off (social compliance bought with
      makespan), not as a clean sweep.
- [ ] Replace every hand-typed number with `\input{}` of the generated tables.

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
| `paper/generated/*.tex` | Generated LaTeX tables for `\input` |

A baseline snapshot of the pre-rebuild CSVs, `paper.tex`, `references.bib` and
figures was taken before any overwrite; ask if you need it restored.
