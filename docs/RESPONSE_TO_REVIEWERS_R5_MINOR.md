# Response to Reviewers — Minor Revision

We thank the reviewer for a careful final pass. All eleven points are addressed
below. One of them — the exposure confound — changed a conclusion, and we are
grateful it was caught; the rest are corrections we should have made ourselves.

No simulations needed rerunning for any scientific reason. The suite was
nevertheless regenerated once, because our provenance fingerprint hashes the whole
`d2ro/` package and the docstring corrections of item 6 changed it. The regenerated
data is numerically identical, which is the expected result of a comment-only edit
and is itself a check that the edit was behaviour-neutral.

| # | Item | Type | Status |
|---|------|------|--------|
| 1 | Exposure confounded with mission duration | **Scientific** | Fixed; conclusion revised |
| 2 | "yielding adds nothing" | Wording | Fixed; now gated in CI |
| 3 | "shortest-path" for the H_prox-OFF cell | Wording | Fixed |
| 4 | "beneficial only in the presence of" | Logic | Fixed |
| 5 | 4,600 vs 4,650 | Consistency | Fixed |
| 6 | Stale code docstrings | Documentation | Fixed (four files) |
| 7 | Figure 7 in ticks | Units | Fixed at source |
| 8 | "What disqualifies APF" | Wording | Fixed |
| 9 | Generality language in abstract | Wording | Fixed |
| 10 | Timing claims host-dependence | Wording | Fixed |
| 11 | LaTeX artifacts | Production | Fixed; now gated in CI |

---

## 1. Exposure interpretation — the reviewer is right, and the effect reverses

This was the most valuable comment in the review. We had read a difference in
*total* person-seconds as a difference in social behaviour, when the two cells
differ nine-fold in how long a mission lasts.

We added exposure per minute of mission, computed from the existing factorial CSV
with no rerun, and the picture changes materially:

| Cell | Makespan | Total exposure | **Rate (person-s/min)** |
|---|---|---|---|
| A: `H_prox` OFF, yield OFF | 19.20 s | 6.43 | **20.11** |
| B: `H_prox` OFF, yield ON | 173.89 s | 49.35 | **17.02** |
| C: `H_prox` ON, yield OFF | 38.23 s | 0.03 | **0.04** |
| D: `H_prox` ON, yield ON | 38.40 s | 0.14 | **0.17** |

Per minute, yielding without `H_prox` does not make the robot more intrusive — it
makes it **slightly less** so (−3.09 person-s/min, 95% CI [−4.78, −1.40],
*p* = 0.002), which is what one would expect of an agent that stops rather than
drives through. The 42.92 person-second inflation is almost entirely the
consequence of missions running nine times longer before timing out.

**The interaction changes sign under normalisation**: −42.81 person-s on the total,
**+3.22 person-s/min** on the rate (95% CI [1.50, 4.93], *p* = 0.002). We now report
both, in a second block of Table III, and say plainly that the large negative
interaction is carried by mission duration rather than by moment-to-moment
behaviour.

The revised claim is the one the reviewer proposed: yielding without a route-level
social gradient causes prolonged obstruction and mission failure, thereby increasing
total accumulated exposure. We have removed "actively harmful" as a description of
its social behaviour and replaced it with "operationally disastrous", which is what
the 100% → 12% success collapse actually establishes.

We keep the total as the primary measure — a pedestrian crowded for fifty
person-seconds is not consoled by the robot having also failed its mission — but the
two are now reported together and the attribution is explicit.

Incidentally, the routing effect survives normalisation and is strengthened by it:
20.11 → 0.04 person-s/min, a factor of roughly 450 (*p* = 2.5 × 10⁻⁶⁸).

## 2. "Yielding adds nothing"

Corrected in the abstract, the results section and the conclusion to *"provides no
statistically detectable additional reduction on an already social route."*

We have also added this to the automated release gate, which now fails the build on
any phrasing that states a null as an absence of effect. The distinction is easy to
lose during editing, and we would rather it be enforced than remembered.

## 3. "Shortest-path" for the `H_prox`-OFF condition

Correct — that cell retains `C_kinematic`, so it is non-social geometric/kinematic
routing rather than a pure Euclidean shortest path, and the benchmark already
contains a genuine Static A\* arm. Every occurrence in the factorial discussion now
reads *"when the proxemic routing cost is absent."*

## 4. "Beneficial only in the presence of a social cost gradient"

Also correct, and we had not noticed that our own data contradict it: with `H_prox`
active, yielding shows no detectable benefit either. Replaced with the reviewer's
formulation — the effect of reactive yielding is route-context dependent: without a
social gradient it induces prolonged obstruction; with one it provides no detectable
additional reduction. In neither regime does the reactive layer substitute for the
routing layer, which is the attribution the experiment was built to establish.

## 5. Trial count

**4,650** throughout. The contribution list said "over 4,600"; the suite totals
700 + 700 + 300 + 600 + 600 + 100 + 100 + 510 + 480 + 200 + 360 = 4,650.

## 6. Stale code documentation

Fixed, and more widely than the reviewer found. `run_weight_sensitivity()` described
five weights and 5×4+1 = 21 configurations; it now documents four and 4×4+1 = 17,
and states why reservation is excluded. We also swept the package and corrected
three further module docstrings still carrying the five-component formula:
`core/graph.py` (module and `Edge`), `core/grid_map.py`, and the weight-vector
comment in `core/units.py`.

The `weight_r` field is retained in `Edge` as a documented no-op with an explanatory
comment, rather than removed, so that older provenance-stamped datasets remain
loadable.

## 7. Figure 7 in ticks

Fixed at the source rather than the caption. The exposure counter increments once
per human per tick alongside `intimate_exposure_s += dt`, so person-ticks × 0.05 is
person-seconds exactly. The analysis pipeline now exports the converted series for
every grouped dataset, and Figure 7(c) plots person-seconds. No dataset needed
regenerating for this.

## 8. "What disqualifies APF"

Softened to: *"In our evaluation the limitation is social compliance rather than
mission completion."* The reviewer is right that this should match the caution we
apply to our ORCA implementation.

## 9. Generality language

The abstract now says the planner transfers across *"the three simulated topologies
evaluated"* rather than implying architectural generality. This matches the standard
already used in Section VI-F.

## 10. Timing claims

Every headline timing figure is now explicitly labelled *"on the evaluation host"*,
with a statement that these are wall-clock measurements, are not portable across
machines, and support an ordinal claim — repair costs microseconds, not
milliseconds.

## 11. Production artifacts

The `extbfeffective` and `extbfasymmetric` artifacts were a literal TAB character
where the backslash of `\textbf` had been consumed by an escape-interpreting edit.
Both repaired.

The duplicated numbering came from manual numbers inside `\subsubsection` titles,
which IEEEtran numbers itself, rendering "1) 1. Intrinsic Metric Geometry". Removed
— and we took the opportunity to retitle the fourth as "The Directional Bottleneck
Reservation *Constraint*", so a reader scanning headings no longer counts five
co-equal weighted components.

Both classes are now caught mechanically. The gate scans for LaTeX commands missing
their backslash, for manual numbers in auto-numbered titles, and for any literal
control character in the sources — the last being the reliable signature, since a
mangled escape leaves a different fragment for every command.

---

## On the two items the reviewer chose not to require

We agree with both judgements and have not attempted either. ORCA and Local MAPF
remain reported as properties of our implementations, excluded from the primary
figure, with reference-baseline validation listed as future work; no conclusion
depends on them. The work remains simulation-only and says so.

We would also note the one thing this round did *not* resolve, which we have added
to the limitations rather than leave implicit: we report *when* the distributed
layer helps but not *how often* those topologies arise, and without that base rate a
deployer cannot convert our per-event effects into an expected benefit. Measuring it
is the most useful single extension of this work.

## A note on the transmitted review

The final paragraph of the review as we received it was corrupted in transmission
("I find no remaining issue requiring substantial newconstrton ofh poosed med…").
We have interpreted it from context as stating that no substantial reconstruction of
the proposed method is required and that the remaining concerns are interpretation,
terminology consistency, normalisation of one exposure analysis, and production
cleanup. If any requirement was lost in that passage, we would be glad to address it.
