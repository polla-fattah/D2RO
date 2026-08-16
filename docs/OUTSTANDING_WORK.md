# Outstanding Work — D²RO

> **START HERE after cloning.** What is done, what is not, and how to reproduce it.
> Nothing required to continue lives outside this repository.

**Status date:** 16 August 2026
**Round:** 3 (second Major Revision). Reviewer correspondence in
[`email.md`](email.md) and [`email2.md`](email2.md); the plans that answer them are
[`REVISION_PLAN_R2.md`](REVISION_PLAN_R2.md) and
[`REVISION_PLAN_R3.md`](REVISION_PLAN_R3.md).

---

## 0. Reproducing everything

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m pytest d2ro/tests/ -q                     # must report 65 passed
PYTHONDONTWRITEBYTECODE=1 python run_full_suite.py  # ~30 min, 11 experiments, 4,650 rows
python paper/scripts/analyze_results.py             # every dataset must read ok
python paper/scripts/generate_tables_and_figures.py
python paper/scripts/verify_manuscript_claims.py    # prose must match the data
python paper/scripts/release_gate.py                # is this build submittable?
```

**Two habits worth keeping.** Always run the suite with `PYTHONDONTWRITEBYTECODE=1`;
stale `.pyc` files have previously made the interpreter execute old code and produce
impossible-looking errors. And if something inexplicable appears right after a
refactor, bisect your own change before blaming the environment.

**The provenance guard.** The fingerprint is a SHA-256 over the whole `d2ro/`
package, so *any* source edit — even a comment — marks *every* dataset `STALE` and
forces a full regeneration. This is intended. Budget ~30 minutes whenever you touch
the package, and batch code changes rather than regenerating between them.

---

## 1. Current state

| Area | State |
|:--|:--|
| Datasets | 11 experiments, 4,650 rows, all `ok` |
| Tests | 65 passing, including a D\* Lite optimality sweep across the weight grid |
| Manuscript | 16 pages, 0 undefined references, 43/43 prose claims verified |
| Bibliography | 21 entries, DOI-verified; 16/20 clean, 4 documented deviations |
| Licensing | MIT (code), CC BY 4.0 (data), all-rights-reserved (manuscript) |
| CI | tests, provenance, claim verification, reference audit, paper build |
| Release | **no tag yet — see §3** |

### The three round-3 blocking defects, and how they were fixed

| # | Defect | Fix | Consequence |
|:--|:--|:--|:--|
| 1 | Matched baseline set `enable_yield=False`, so `D²RO − matched` bundled routing, replanning and yielding | 2×2 route×yield factorial, identical kinematics per cell | Routing, not yielding, produces the social benefit (0.03 person-s with yielding off) |
| 2 | `Edge.cost` returned `inf` before applying `weight_r`, and `r_lock` is only ever 0 or ∞, so `w_R` was inert everywhere | Reformulated as 4 soft terms + 1 hard constraint; `w_R` dropped from the sensitivity grid | The framework is no longer described as a five-weight objective |
| 3 | D\* Lite heuristic used raw Euclidean distance, inadmissible for `w_D < 1` | `h = min(w_D)·d`, plus a test sweep over the whole grid | Previously reported `w_D < 1` results were **suboptimal paths** and are superseded |

Defect 3 was not theoretical: reverting the fix makes the new tests fail with D\* Lite
returning 8.5887 where Dijkstra's optimum is 8.4758.

### Findings that weaken our own claims, reported deliberately

- **The distributed layer does not pay for itself in the broad benchmark.** Local
  Social D\* Lite matches D²RO's social compliance exactly (*p* = 1) while running
  8.12 s faster. Mesh and reservation earn their cost only in the controlled
  mechanism experiments.
- **The safety effect is mostly the reactive controller, not the `w_S` graph term.**
  Median fixture contacts: 3 (full), 5 (cost removed), 48 (controller removed),
  93.5 (both).
- **Anticipation degrades at 20% packet loss** (lead time 11.01 → 6.20 s), so the
  robustness claim is bounded at ~10% loss rather than stated unconditionally.

---

## 2. Still open

### Blocking submission

- [ ] **Create the release.** See §3. The manuscript must cite a tag that exists.

### Not blocking, but expected by the reviewer

- [ ] **Validate ORCA against a reference implementation** (RVO2) on a canonical
      case. Both ORCA and Local MAPF return 0% success and are reported as
      diagnostics only; no claim depends on them, but the reviewer would prefer
      validation to demotion.
- [ ] **Joint weight calibration.** Section VI-H perturbs one weight at a time and
      finds a plateau; interactions between weights are untested. Future work should
      treat this as multi-objective (Pareto over makespan and exposure).
- [ ] **Reciprocal pedestrian model.** Simulated humans do not react to robots, so
      the reported exposure is an upper bound on what a real crowd would produce.
      Recorded trajectories or a social-force model would strengthen HRI claims.
- [ ] **Clean-room reproduction** on a machine that has never seen the project.

### Repository hygiene

- [ ] The web simulator under `docs/` (`index.html`, `simulator.js`,
      `python_bundle.js`) embeds a **snapshot** of the Python sources, rebuilt by
      `scripts/build_web_bundle.py`. Nothing enforces freshness, so editing `d2ro/`
      can silently leave the demo running old code. A hash check would close this.
- [ ] The demo's "Static A\* baseline" toggle does **not** match the paper's
      matched-controller arm: it leaves the V2V mesh enabled and disables the safety
      envelope, the opposite of the published configuration on both counts.

---

## 3. Making a release

The manuscript embeds its own provenance, and that creates an ordering problem: the
stamp is generated *before* the commit it would name, so a locally built PDF always
names its parent and reports `-dirty`. Round-3 review caught exactly this and was
right to.

**Therefore the committed `paper/paper.pdf` is never the submittable artefact.**

```bash
# 1. commit everything; the working tree must be clean
git status --short          # must print nothing

# 2. tag
git tag -a v3.0-review3 -m "Round-3 revision submitted to <venue>"
git push origin v3.0-review3
```

CI then checks out that tag on a clean tree, regenerates the artefacts (so the stamp
names the tagged commit with no `-dirty`), rebuilds the PDF, runs
`paper/scripts/release_gate.py`, and attaches the PDF to the GitHub release.
**Submit that file.**

`release_gate.py` refuses to certify a build when any dataset is not `ok`, the prose
disagrees with the data, the LaTeX log carries an unresolved reference, the PDF
contains a literal `??`, the commit stamp ends in `-dirty`, or no tag exists. Every
one of those failures has reached a reviewer of this project at least once.

---

## 4. Deliberate design decisions

Recorded so they are not mistaken for oversights.

- **`α_turn` is not implemented and has been removed from the formulation.** Pricing
  a heading change requires the search state to carry a heading, which is a rewrite
  of D\* Lite's state space for a term the novelty does not rest on. Cornering is
  bounded in execution (`ω_max = 2.5 rad/s`) but not priced in search.
- **Reservation is a constraint, not a weight** (§1, defect 2).
- **Single-file designation is fixed per edge** in the environment definitions, not
  computed from width at run time. A 2.1 m aisle would admit two 0.48 m carts on bare
  geometry; the designation follows from the operational clearance the fleet must
  maintain and from real aisle occupancy, and the manuscript says so plainly.
- **Sensing is range-limited, not occlusion-aware.** Pedestrians are selected by
  Euclidean distance with no ray-casting against shelves, so a trailing agent's
  perceptual disadvantage is if anything understated.
- **Weak references and worker-thread execution were both tried and reverted**; they
  solved no real problem and destabilised long runs.

---

## 5. Where things live

| Path | Contents |
|:--|:--|
| `run_full_suite.py` | Suite driver: subprocess isolation, retries, completeness checks |
| `paper/scripts/analyze_results.py` | The single statistics pipeline |
| `paper/scripts/generate_tables_and_figures.py` | Data-driven artefacts; refuses stale datasets |
| `paper/scripts/verify_manuscript_claims.py` | Prose ↔ data check (43 claims) |
| `paper/scripts/audit_references.py` | DOI-first bibliography audit |
| `paper/scripts/release_gate.py` | Submittability gate |
| `paper/scripts/generate_topology_figures.py` | Qualitative figures (illustrative only) |
| `experiments/data/analysis_results.json` | Machine-readable single source of truth |
| `.github/workflows/` | CI and release automation |

### One rule about artefact ownership

Two kinds of figure script exist and must never overlap. **Data-driven**
(`generate_tables_and_figures.py`) reads only `analysis_results.json` and refuses to
emit an artefact whose dataset is missing or stale. **Qualitative**
(`generate_topology_figures.py`, `generate_heatmaps_and_trajectories.py`) run the
simulator to draw illustrations and read no CSV.

Three legacy scripts were deleted for violating this: `generate_paper_plots.py` also
wrote `fig1_benchmark_comparison.pdf`, so running it silently replaced the
provenance-checked figure with one built by code that performs no staleness check.
**Do not reintroduce a script that writes an artefact the data-driven pipeline owns.**
