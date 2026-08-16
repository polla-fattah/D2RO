# Engineering notes — D²RO / SW-DGO

> Written for whoever picks this up next, including future-you six months from
> now with no memory of why any of it is like this. It records the pipelines,
> the decisions and the reasons — especially the reasons, because most of the
> odd-looking choices here are scar tissue from a specific failure that reached
> a reviewer.

**Status at time of writing:** minor revision, manuscript submittable, public
code release live at `github.com/polla-fattah/SW-DGO`.

---

## 1. The two repositories

| | Private (`D2RO`) | Public (`SW-DGO`) |
|---|---|---|
| Contains | Everything: manuscript, data, code, reviewer correspondence | Code, tests, datasets, simulator, analysis |
| Is | The working repository and source of truth | A generated export, one squashed commit |
| Pages site | **Deleted** — see §7 | `polla.dev/SW-DGO/` |

**The public repo is generated, never edited.** `scripts/publish_public.py`
copies an allowlist of paths into a staging tree and builds a fresh
single-commit history there. Editing `SW-DGO-public/` directly loses your work
on the next run.

Working directories:

```
…/Research/Projects/D2RO/              private, the one you edit
…/Research/Projects/SW-DGO-public/     staged export, regenerated
```

### Why an allowlist and not `git subtree split`

The obvious approach — move everything public under one prefix, split it out —
would have been wrong. The dataset provenance fingerprint hashes each source
file's path **relative to the repository root**. Moving `d2ro/` to
`public/d2ro/` changes every recorded path, changes the fingerprint, and marks
all eleven datasets STALE, costing a 35-minute regeneration for a cosmetic
rearrangement — plus rewriting every import, test path and CI path.

Copying files also means no private history is transferred at all, so an
unpublished draft cannot leak through a forgotten branch or a dangling object.
The script refuses to finish if anything matching `paper/`, `.tex`, `.pdf` or
`.bib` reaches the staging tree.

---

## 2. Pipelines

Five, in dependency order. Each stage refuses to run on stale input from the
one before it.

```
  d2ro/  ──────────────► experiments/data/*.csv        run_full_suite.py     ~35 min
                         + *.provenance.json
                                │
                                ▼
                         analysis_results.json          analyze_results.py    ~10 s
                         analysis_report.md
                                │
                    ┌───────────┴────────────┐
                    ▼                        ▼
        paper/generated/*.tex        paper/figures/*.pdf
                                       generate_tables_and_figures.py
                                │
                                ▼
                         paper/paper.pdf                build_latex.py
                                │
                                ▼
                         SUBMITTABLE / NOT              release_gate.py
```

### 2.1 Experiments → data

```bash
PYTHONDONTWRITEBYTECODE=1 python run_full_suite.py
```

Eleven experiments, 4,650 rows. Runs each in a **subprocess** with row-count
completeness checks, so one crash cannot silently truncate a dataset. Writes
atomically. ~35 minutes.

`PYTHONDONTWRITEBYTECODE=1` is not superstition: stale `.pyc` files have made
this repo execute old code and produce impossible-looking errors.

Each CSV gets a `.provenance.json` recording a SHA-256 of the entire `d2ro/`
package. **This is what makes everything downstream trustworthy.**

### 2.2 Data → statistics

```bash
python paper/scripts/analyze_results.py
```

Recomputes the fingerprint and compares. Mismatch → dataset marked `STALE`, and
nothing downstream will report it. Emits `analysis_results.json`, the single
source of truth for every number in the paper.

### 2.3 Statistics → artefacts

```bash
python paper/scripts/generate_tables_and_figures.py
```

Writes `paper/generated/*.tex` and the data-driven figures. **Never edit
anything in `paper/generated/`** — it says so in every file header.

Emits a *placeholder* rather than a table when a dataset is unusable, so a
missing experiment can never be represented by leftover values from an earlier
run.

### 2.4 Artefacts → PDF

```bash
python paper/scripts/build_latex.py     # or pdflatex ×3 + bibtex
```

Three passes plus BibTeX. The stamp in `paper/generated/commit.tex` names the
commit whose *sources* produced the document.

### 2.5 Certification

```bash
python paper/scripts/release_gate.py            # full
python paper/scripts/release_gate.py --no-net   # skip Crossref
```

**Twelve checks.** Every one exists because that exact failure reached a
reviewer at least once. See §4.

### 2.6 Web bundle (separate track)

```bash
python scripts/build_web_bundle.py    # after any d2ro/ change
python scripts/check_web_bundle.py    # CI runs this
```

The browser demo executes a **snapshot** of `d2ro/` embedded in
`docs/python_bundle.js`. Editing the package does not refresh it. The bundle now
records a fingerprint of its sources and the checker fails on drift.

### 2.7 Publishing

```bash
python scripts/publish_public.py --git
cd ../SW-DGO-public && git push --force origin main
```

Force-push because the script rebuilds history each run.

---

## 3. File map

```
d2ro/                             the simulation package — FINGERPRINTED
├── core/agent.py                 TrolleyAgent: D* Lite + four cost terms + mesh
├── core/dstar_lite.py            incremental replanner
├── core/graph.py                 directed cost graph; reservation as constraint
├── core/human.py                 pedestrian + asymmetric Gaussian proxemics
├── core/mesh_network.py          V2V broadcast, exponential decay, loss, latency
├── core/metrics.py               exposure counters (person-time)
├── core/units.py                 SI calibration, cost normalisation
├── baselines/                    Static A*, APF, ORCA, local MAPF
├── environments/                 supermarket, hospital, airport
├── sim/run_experiments.py        all eleven experiments + _code_fingerprint()
└── tests/                        67 tests

experiments/data/                 raw CSVs + provenance + analysis_results.json
paper/paper.tex                   manuscript (single file)
paper/generated/                  GENERATED — never edit
paper/figures/                    data-driven + qualitative figures
paper/scripts/                    analysis, verification, gate, build
docs/index.html                   public landing page
docs/landing.css                  its styling (standalone; not styles.css)
docs/simulator.html               the WASM simulator
docs/styles.css                   simulator styling only
docs/python_bundle.js             GENERATED snapshot of d2ro/
docs/*.md                         reviewer correspondence — NEVER PUBLISH
scripts/publish_public.py         the allowlist exporter
```

---

## 4. The twelve gate checks, and the failure behind each

| Check | The failure it prevents |
|---|---|
| All datasets `ok` | A PDF went out with a provenance table saying every dataset was STALE |
| Prose claims match data | Prose drifts after regeneration; generated tables cannot |
| No undefined refs | — |
| No literal `??` in PDF | A submitted PDF contained six unresolved `Table ??` |
| Commit stamp clean | A PDF claimed `e3d6582-dirty`, built from a tree not matching its commit |
| A release tag exists | The manuscript cited `v2.0-review2` when the repo had no tags at all |
| No superseded terminology | Four-term abstract coexisted with five-term introduction for two rounds |
| No control characters | `\textbf` became TAB + `extbf`, rendering as "extbfeffective" |
| Anonymity (when blind) | Author names, running head, lab, and account name in URL |
| Aims declared = assessed | Conclusion said "three aims" then discussed A1–A4 |
| Every quoted *p* exists in the data | **`p < 10^-15` was cited for contrasts the pipeline never computed** |
| No reference resolves to wrong work | `literature/D2RO.bib` had 4 of 25 DOIs pointing at unrelated papers |

The eleventh is the most important. It is what makes "no hand-entered numbers"
true rather than aspirational.

---

## 5. Decisions worth remembering

### Reservation is a constraint, not a fifth weight
`C_mutex` takes only `{0, ∞}`. A reserved edge is unavailable at any
coefficient; an unreserved one contributes `w_R · 0 = 0`. The coefficient had
**no operative magnitude in any reachable state**, which is why perturbing it
moved nothing. The framework is four soft terms + one hard constraint.
`Edge.weight_r` survives as a documented no-op so older datasets stay loadable.

### The fingerprint covers `d2ro/` including tests
So editing a test forces a full regeneration. This is deliberate — a guard that
guesses which changes matter is one you learn to override — but budget for it.
**Batch all `d2ro/` edits before regenerating.**

### Timings are bounds, not point estimates
Rerunning the same code on the same machine moved median repair time from
0.002 ms to 0.004 ms under load. A ±60% band could not absorb 2×. Widening the
band would have made it check nothing, so the *claim* changed instead: the paper
states upper bounds and says why. **The right response to a check that fires is
usually to fix the claim, not the check.**

### The equal-competence control
The single most valuable experimental decision. Comparing against a socially
blind baseline cannot separate "social" from "distributed". Local Social D* Lite
holds social competence fixed and varies only the coordination architecture — and
shows the distributed layer contributes nothing measurable in the broad scenario
while being decisive in its target topologies. That negative result about our own
system is a large part of why the paper stopped being rejected.

### Normalisation can reverse a sign
Total exposure conflates intrusiveness with dwell time. Cells differed 9× in
mission duration. Per minute, the interaction flips from −42.81 to +3.22. Always
ask whether a total is really a rate.

### Person-seconds, never ticks
Tick counts are artefacts of `dt = 0.05 s`. Wilcoxon is rank-invariant so *p* is
unchanged, but effect sizes need a real unit.

### The landing page does not load `styles.css`
That file is the simulator's application shell — full-height flex, dark
surfaces, semantic accents. Every property had to be fought. They are now
independent.

---

## 6. Traps that bit repeatedly

**Escape mangling — four times.** Editing `.tex` or `.py` through a heredoc or
any tool that interprets backslash escapes turns `\textbf` into TAB + `extbf`
and `\newcommand` into newline + `ewcommand`. **Always write patch scripts as
files with raw strings, never inline heredocs.** Now gated by a control-character
check.

**Cross-platform fingerprint — twice.** (a) Raw-byte hashing made CRLF and LF
checkouts disagree. (b) `os.walk` returns subdirectories in filesystem order,
alphabetical on NTFS and arbitrary on ext4, so content order differed. Both fixed
by normalising line endings and sorting the full path list. Tests assert both.

**The false `-dirty` stamp.** It was computed *after* the pipeline rewrote its
own outputs, so every build looked dirty. Now excludes generated artefacts and
tests sources only.

**Windows cannot delete git objects.** They are read-only; `shutil.rmtree` fails
and re-staging silently keeps the old tree — worse than failing, because
verification then passes against stale content.

**GitHub Pages served the whole repo.** Source was `master` / `/` rather than
`/docs`, so the unpublished manuscript and the reviewer's confidential report
were publicly downloadable. Deleted. **If Pages is ever re-enabled, set the
path explicitly and verify what is reachable.**

---

## 7. Review history

| Round | Outcome | What actually changed |
|---|---|---|
| 1–2 | Major revision | Airport seed defect (100 identical trials); ablation reconstruction |
| 3 | Major revision | Three blocking defects: matched baseline confound, `w_R` inert, D* Lite heuristic inadmissible for `w_D < 1` |
| 4 | Major revision | Factorial rerun with mesh/reservation off in every cell; real interaction statistics; degradation re-analysed as paired |
| 5 | **Minor revision** | Exposure rate normalisation; eleven consistency items |

Round 4 is the one to remember: the reviewer found that prose cited
`p < 10^-15` for contrasts the pipeline **never computed**. The real value was
`1.5 × 10⁻⁹`. That is where the p-value gate came from.

---

## 8. Open work

- **Base rate.** We report *when* the distributed layer helps, not *how often*
  the enabling topologies arise. Without it, per-event effects cannot become an
  expected benefit. Most useful single extension.
- **ORCA validation** against RVO2 on a canonical benchmark.
- **Joint weight calibration** — currently one-at-a-time.
- **Reciprocal pedestrian model.**
- **Search-engine cache check** for the previously-exposed manuscript
  (`site:polla.dev D2RO`, and the Wayback Machine).

---

## 9. Routine commands

```bash
# after changing d2ro/  (fingerprint changes → everything downstream must follow)
PYTHONDONTWRITEBYTECODE=1 python run_full_suite.py
python paper/scripts/analyze_results.py
python paper/scripts/generate_tables_and_figures.py
python scripts/build_web_bundle.py

# after changing prose only
python paper/scripts/verify_manuscript_claims.py
python paper/scripts/build_latex.py
python paper/scripts/release_gate.py

# before submitting
python paper/scripts/release_gate.py        # must print SUBMITTABLE

# publishing the public repo
python scripts/publish_public.py --git
```

**Anonymity:** `\anonymoustrue` in `paper/paper.tex` for double-blind,
`\anonymousfalse` for camera-ready. One switch drives the author block, both
running heads, the repository URL and the acknowledgment.
