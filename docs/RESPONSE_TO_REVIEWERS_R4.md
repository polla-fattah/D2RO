# Response to Reviewers — Round 4

We thank the reviewer for a review that is unusually specific and, in two places,
correct about defects we had not found ourselves. Both blocking issues were
genuine: one experiment did not isolate the factor it named, and one analysis
discarded the pairing its own design established. We fixed the experiment and the
analysis rather than the wording around them.

Every number quoted below is produced by the committed pipeline and is checked
mechanically. The manuscript now pins 51 exact claims against
`experiments/data/analysis_results.json` (previously 36), and the release gate
refuses to certify a build in which any of them disagrees.

**Summary of what changed in the science, not the prose:**

| Comment | Status | What was actually done |
|---|---|---|
| 1 — factorial does not isolate `H_prox` | **Fixed (experiment rerun)** | Mesh and reservation disabled in all four cells; D* Lite active in all four |
| 2 — no factorial statistics | **Fixed (analysis added)** | Paired contrasts, signed-rank/t, Holm, McNemar for binary success |
| 3 — five-weight formulation survives | Fixed | Global sweep; now gated in CI |
| 4 — Figure 7 stale | Already fixed; verified | Generator plots four weights |
| 5 — Table III inconsistent | **Fixed (table rebuilt)** | Seven configurations, two blocks |
| 6 — degradation collapses Mesh ON/OFF | **Fixed (analysis rewritten)** | Paired within-seed effects per channel |
| 7 — 10% threshold unsupported | **Fixed (test added)** | Cross-channel contrasts; the threshold survives |
| 8 — Figure 4 not person-seconds | Fixed | Figure and paired tests both moved |
| 9 — Table I safety radius | Already fixed; verified | "Effective safety / swept-envelope radius" |
| 10 — graph called undirected | Already fixed; verified | Undirected roadmap → directed local cost graph |
| 11 — line-of-sight terminology | Fixed | Four occurrences corrected; gated |
| 12 — "generality is demonstrated" | Fixed | "Cross-topology transfer within the evaluated simulation family" |
| 13 — dBm | Fixed | Uncited range removed |
| Meta — QC misses semantic contradictions | **Fixed (gate extended)** | Six new mechanical checks |

---

## 1. [BLOCKING] The factorial did not isolate social routing

**The reviewer is right, and the criticism was precise.** The `social` flag set
`enable_mesh`, `enable_prox`, `enable_lock` and `static_route` together, so the
factor contrasted a frozen geometric route against the entire dynamic routing
stack. No `H_prox`-specific conclusion could follow from it.

We took the reviewer's first option rather than the fallback, because renaming the
experiment would have left the attribution question unanswered. The factorial was
**rerun** with:

- `enable_mesh=False` and `enable_lock=False` in **every** cell;
- `static_route=False` in **every** cell, so D* Lite replans throughout;
- only `enable_prox` and `enable_yield` varying.

The routing factor now toggles the proxemic cost term and nothing else. The
conclusion survives the stricter design, with different numbers:

| Cell | Success | Makespan (s) | Exposure median [IQR] |
|---|---|---|---|
| A: `H_prox` OFF, yield OFF | 100.0% | 19.20 ± 0.00 | 6.45 [6.21, 6.60] |
| B: `H_prox` OFF, yield ON | 12.0% | 173.89 ± 17.01 | 48.00 [38.51, 57.86] |
| C: `H_prox` ON, yield OFF | 100.0% | 38.23 ± 10.90 | 0.00 [0.00, 0.00] |
| D: `H_prox` ON, yield ON | 100.0% | 38.40 ± 11.04 | 0.00 [0.00, 0.00] |

The causal sentence the reviewer objected to is now licensed by the design, and
Section VI-D says why in the text rather than leaving the reader to check the
source. We also state the price, which the previous version buried: the routing
effect costs 19.03 s of makespan (95% CI [16.27, 22.31]).

## 2. [BLOCKING] The factorial was descriptive, not inferential

**Correct, and worse than the reviewer could see from the outside.** The pipeline
computed cell summaries and bootstrap intervals but **no p-value at all** for this
experiment — yet the manuscript cited `p < 10^-15` for both the routing contrast
and the interaction. Those figures were hand-entered, which contradicts the
paper's own strongest reproducibility claim. They were also wrong: the routing
contrast is Holm-adjusted `p = 1.5 × 10⁻⁹`, six orders of magnitude larger.

We are grateful this was caught. Pre-specified paired contrasts are now computed
across seed-matched trials, tested against zero (paired *t* where Shapiro–Wilk
passes, Wilcoxon signed-rank otherwise, with the test named in the table), and
Holm-adjusted within each outcome family:

| Contrast | Cells | Median [IQR] | Mean (95% CI) | Test | *p*(Holm) |
|---|---|---|---|---|---|
| `H_prox`, yield OFF | C − A | −6.45 [−6.60, −6.20] | −6.40 (−6.48, −6.31) | Wilcoxon | 1.5 × 10⁻⁹ |
| `H_prox`, yield ON | D − B | −48.00 [−57.86, −38.51] | −49.21 (−54.40, −44.16) | paired *t* | 2.1 × 10⁻²³ |
| Yielding, `H_prox` OFF | B − A | 41.60 [32.31, 51.50] | 42.92 (37.89, 48.08) | paired *t* | 4.7 × 10⁻²¹ |
| Yielding, `H_prox` ON | D − C | 0.00 [0.00, 0.00] | 0.11 (0.00, 0.32) | Wilcoxon | 0.59 |
| **Interaction** | (D−C)−(B−A) | −41.60 [−51.50, −32.31] | −42.81 (−47.99, −37.76) | paired *t* | 4.7 × 10⁻²¹ |

Three consequences worth flagging:

- **Binary success now gets paired treatment.** Exact McNemar on the same matched
  trials, as the reviewer asked. Yielding on a shortest-path route produces 44
  discordant pairs all in one direction (*p* = 4.5 × 10⁻¹³); on a social route,
  zero discordant pairs (*p* = 1).
- **"Yielding contributes nothing" is now a measured null, not an inference from
  two means.** The contrast is 0.11 person-s with CI [0.00, 0.32] and *p* = 0.59.
  We report it as a null and say explicitly that bounding an effect is not the
  same as proving its absence.
- **Median [IQR] is now reported for exposure**, per the reviewer's request and
  per our own stated policy. 96% of trials in Cells C and D record exactly zero,
  which the means alone concealed.

We also found and fixed a defect the reviewer could not have seen: the factorial
table printed `100.0% [0.0, 0.0]` as a Wilson interval for every cell, because the
analysis never emitted `success_ci95` and the formatter defaulted silently.

## 3. [MAJOR] Five-weight formulation not fully converted

Fixed globally. The Introduction's Eq. (1), the sensitivity section and the
Conclusion all now state four weighted soft terms subject to a reservation
feasibility constraint. `w_R` survives only in Section III's explicit explanation
of why it was removed, which we take to be the reviewer's intent.

One further instance was found beyond those listed: the ablation discussion
claimed that "scaling `w_M` or `w_R` by any factor from 0.5 to 1.5 changes
makespan by 0.0 s". `w_R` is not in the sensitivity dataset at all, so this was a
statement about an experiment that was never run. Corrected.

## 4. [MAJOR] Figure 7 stale

The generator had already been corrected to four weights before this review
arrived, and the figure and caption are consistent with the 510-row dataset. We
have verified this rather than assumed it, and the CI gate now fails on `w_R`
appearing in any weighted-objective or sensitivity caption.

## 5. [MAJOR] Table III inconsistent with its own caption

**Fixed, and the root cause was worse than a stale caption.** The label map in the
generator had drifted from the experiment: four of the seven configuration names
did not match, so those rows were **silently dropped** while the caption continued
to claim five ablated terms.

The table is rebuilt on the reviewer's suggested structure:

*Routing-cost ablations* — Full; w/o mesh; w/o proxemics; reservation lifted.
*Safety attribution* — Full; `w_S = 0` with controller retained; controller off
with `w_S` retained; both off.

The safety block makes the causal structure plain: median fixture contacts run
3 → 5 → 48 → 94. The reactive controller, not the `w_S` cost term, accounts for
almost all of the improvement — which is a result against our original framing and
we report it as such.

The generator now **raises** on an unrecognised configuration instead of omitting
the row, so this class of silent drop cannot recur.

## 6. [BLOCKING] Degradation analysis collapsed Mesh ON and Mesh OFF

**Correct.** `analyse_grouped` grouped by `channel` only, so Mesh-ON and Mesh-OFF
records fell into the same bucket and the structure did not represent the
controlled comparison at all. The code comment claiming "grouped by channel AND
arm" described an intention, not the implementation.

Replaced with a paired analysis that preserves the design. For each channel
condition we compute the within-seed difference — ΔT_anticipation = T(Mesh ON) −
T(Mesh OFF), and the corresponding backtracking and makespan effects — with
bootstrap CIs. These paired effects are now plotted against loss and latency
(new Figure 8), as the reviewer requested. The mesh advantage is significant in
every channel condition tested; no interval approaches zero.

## 7. [MAJOR] The 10% packet-loss threshold needed support

The threshold now has a test behind it. Per-condition effects cannot answer a
question about *change between* conditions, so we contrast each channel against
the clean channel, pairing on trial and on the other factor:

| Channel | Δ mesh advantage | 95% CI | *p*(Holm) |
|---|---|---|---|
| 10% loss vs 0% | −0.80 s | [−1.50, −0.26] | 0.16 |
| 20% loss vs 0% | −4.26 s | [−5.73, −2.90] | 6.6 × 10⁻⁶ |
| 100 ms vs 0 ms | −0.45 s | [−1.17, −0.06] | 2.8 × 10⁻⁶ |
| 200 ms vs 0 ms | −0.55 s | [−1.30, −0.14] | 1.0 × 10⁻⁴ |

The reviewer's condition for retaining the wording is met: at 10% loss the change
is neither statistically detectable nor practically material against an advantage
of roughly 11 s; at 20% it is both, eroding about 38%. Latency is statistically
detectable but practically negligible across the range tested, which is consistent
with the mechanism — a delayed alert still arrives, a dropped one does not.

We note one honest tension in the 10% row: the rank test does not reject, while a
mean-based bootstrap interval marginally excludes zero. We rest the claim on the
small magnitude and the non-rejection together, and state the 20% result as the
one that carries weight.

## 8. [IMPORTANT] Figure 4 and person-seconds

Fixed at the source rather than the label. The figure now plots
`exposure_person_s`, and the benchmark's paired comparisons were also moved off
the tick column — the Wilcoxon *p* is unchanged, ranks being invariant under a
positive rescale, but the effect size and its interval now carry a unit that means
something independent of the 0.05 s integration step.

Two prose sentences still reporting ticks were found and converted (APF exposure
and the ORCA/MAPF completeness note). One of them also quoted a Holm-adjusted *p*
from a superseded run.

## 9–13. [IMPORTANT / MINOR]

**9. Table I safety radius.** Already corrected to "Effective safety /
swept-envelope radius", with the 0.24 m physical inscribed radius stated in the
text. Verified against the built PDF.

**10. Graph formulation.** Already corrected: an undirected physical roadmap
*G = (V, E)* from which each agent maintains a directed local cost graph
*Ḡᵢ = (V, Aᵢ)* carrying directional penalties and lock states, exactly as the
reviewer proposed.

**11. Line-of-sight.** Four occurrences corrected to range-limited sensing,
including the Table VI caption. The single remaining use is the sentence that
draws the distinction explicitly, which the gate exempts by pattern.

**12. Cross-domain claim.** Changed to "Cross-topology transfer within the
evaluated simulation family is therefore demonstrated", with an added sentence
stating that the three domains share one physics abstraction and one sensing
model, so the result establishes independence from a tuned topology rather than
transfer to a real facility.

**13. RF attenuation.** The numerical range is removed. We had no measurement to
support it and were not willing to attach a borrowed citation to a number we did
not verify; the qualitative point about metal fixtures and the case for Sub-GHz or
DSRC links stands without it.

---

## On the meta-comment: automated checks now cover semantics

This was the most useful comment in the review, and it identified the mechanism
behind most of the others. Our checker validated numbers and was blind to
structure, which is exactly how a four-term abstract coexisted with a five-term
introduction across two revisions.

The release gate now runs the reviewer's suggested checks, plus two of our own:

1. **No superseded terminology** — scanned across `paper.tex` *and*
   `paper/generated/`. This matters: "five cost terms" survived the previous sweep
   precisely because it lived in a generated caption. Violations name file and
   line.
2. **`w_R` never presented as an operative weighted term**, exempting the passage
   that explains its removal.
3. **Exactly four aims** — declared aims must equal assessed aims.
4. **No "control ticks"** in exposure figures or captions.
5. **No "inscribed radius = 0.40 m"**.
6. **No line-of-sight claims** unless the sentence draws the distinction.
7. **Every p-value quoted in prose must appear in `analysis_results.json`.** This
   is the check that would have caught the invented `p < 10^-15`, and it is the
   one we most needed.

The gate found real problems on its first run, including a **damaged conclusion**
that no reviewer had yet flagged: two overlapping sets of aim assessments had
accumulated, with A1's opening sentence overwritten and A2–A4 duplicated, leaving
an orphaned fragment quoting a superseded 29.94 s routing cost. Repaired.

## What we have not done

In the interest of not overstating this revision:

- **ORCA is still not validated against RVO2.** The manuscript continues to report
  ORCA and MAPF as properties of our implementations, not of the algorithms, and
  no contribution rests on them.
- **Weights are still calibrated one at a time.** The sensitivity study finds a
  plateau but says nothing about interactions between weights; joint calibration
  remains future work and is described as such.
- **Pedestrians are non-reciprocal.** They do not model the robot, so reported
  exposure is a property of a one-sided interaction.
- **The distributed layer remains conditional.** The local-social baseline still
  matches D²RO's social compliance exactly (*p* = 1) while running 8 s faster. We
  have not weakened this finding; the conclusion states that a deployment whose
  topology never produces out-of-sight blockages or contested single-file
  corridors would be right to omit the distributed layer.
