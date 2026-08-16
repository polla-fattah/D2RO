Yes. I think they **deserve another round of review**.

I would **not reject permanently at this point**. This new manuscript is materially better than the previous one: the authors actually implemented most of the substantive methodological fixes rather than merely rewriting the discussion. The new paper now has the route×yield experiment, a local-social comparator, a corrected four-term objective with reservation as a constraint, corrected D* Lite admissibility, split safety ablation, person-seconds, and communication degradation in the mechanism-specific experiment. 

I am also **not counting the `-dirty` fingerprint issue against them in this round**, as you suggested.

However, I would still recommend **Major Revision**, because I found **two scientific/analysis problems that are genuinely important**, plus a surprisingly large number of internal contradictions left over from the previous formulation.

## Recommendation: Major Revision — another round is justified

This is no longer a paper I would reject because its experimental foundation is unreliable. The situation has changed substantially.

For example, they now admit that an ordinary local social planner obtains the **same social compliance as D²RO while being about 8 seconds faster**, which is a meaningful negative result against their own system.  They also now separate safety planning from the reactive safety controller and show that the controller, rather than (w_S), accounts for most of the fixture-contact improvement.  This kind of self-correcting reporting substantially increases my confidence in the work.

But I would send them the following comments.

---

# Reviewer comments — next round

### 1. **[BLOCKING] The new route × yielding “factorial” still does not isolate social routing as cleanly as the manuscript claims.**

This is the most important remaining scientific issue.

The paper says that the experiment varies:

[
\text{route}\in{\text{frozen shortest path},\text{social}}
]

and

[
\text{yielding}\in{\text{off},\text{on}},
]

and concludes that the reduction from 6.43 to 0.03 person-seconds is attributable specifically to (H_{\mathrm{prox}}). 

However, the implementation of the “social” factor does not merely switch social routing on. It constructs the agents with:

> `enable_mesh=social, enable_prox=social, enable_lock=social, ... static_route=(not social)`

so the factor simultaneously changes:

* proxemic graph cost;
* V2V mesh;
* corridor reservation;
* dynamic replanning/frozen routing.

Therefore this experiment is really closer to:

[
\text{frozen geometric route}
\quad\text{vs.}\quad
\text{full dynamic D²RO routing stack},
]

not simply:

[
H_{\mathrm{prox}}\text{ OFF}
\quad\text{vs.}\quad
H_{\mathrm{prox}}\text{ ON}.
]

The broad benchmark suggests that mesh and reservation contribute little in this topology, so I do **not** think this invalidates the observed result. But it prevents the strong causal sentence:

> “The near-zero social exposure ... is therefore attributable to (H_{\mathrm{prox}}).”

The authors should rerun this factorial with **mesh and reservation disabled in every cell**. Ideally, keep the same dynamic D* Lite planner throughout and vary only:

[
H_{\mathrm{prox}}\in{\mathrm{OFF},\mathrm{ON}}
]

and

[
\text{reactive yielding}\in{\mathrm{OFF},\mathrm{ON}}.
]

That would directly answer the attribution question.

If they want to retain the present experiment, it should be renamed **dynamic routing-stack × yielding**, and the (H_{\mathrm{prox}})-specific causal claim should be weakened.

---

### 2. **[BLOCKING] The “2 × 2 factorial” is presented descriptively, but no factorial statistical analysis is actually performed.**

Table II is informative, but it contains cell summaries rather than statistical evidence for the claimed interaction. The four cells are:

* Frozen/no-yield: 6.43 ± 0.27 person-s;
* Frozen/yield: 49.35 ± 18.38;
* Social/no-yield: 0.03 ± 0.16;
* Social/yield: 0.62 ± 3.58.



The manuscript then makes statements such as:

> “Routing produces the social benefit; yielding does not.”

and

> “The interaction is strongly negative.”



But the statistics pipeline merely groups the four cells descriptively. Its own comment says the quantities of interest are “differences and an interaction,” yet it does not actually calculate them.

This is especially important because 0.03 ± 0.16 versus 0.62 ± 3.58 is extremely zero-inflated and skewed. The authors cannot infer “no contribution” or an interaction simply from those means.

They should report explicit inferential contrasts for:

[
\text{routing main effect},
]

[
\text{yielding main effect},
]

and especially:

[
(\text{social,yield}-\text{social,no-yield})
--------------------------------------------

(\text{frozen,yield}-\text{frozen,no-yield}).
]

A paired permutation approach, suitable repeated-measures model, aligned-rank factorial analysis, or carefully defined pre-specified paired contrasts would all be defensible. Binary success needs a corresponding paired/repeated binary treatment.

I would also report exposure as **median [IQR]** here, consistent with the manuscript's stated policy for highly skewed outcomes, rather than mean ± SD alone.

---

### 3. **[MAJOR] The manuscript has not been fully converted from the former five-weight formulation to the new four-soft-term + constraint formulation.**

The formal Section III formulation is now correct and much better:

[
C_i =
w_D C_{\mathrm{geom}}
+w_M C_{\mathrm{mesh}}
+w_H C_{\mathrm{social}}
+w_S C_{\mathrm{kinematic}}
]

subject to a reservation feasibility constraint. The authors explicitly explain why (w_R) was mathematically meaningless. 

Unfortunately, several other parts of the same paper still state the old formulation.

For example, the Introduction still defines:

[
w_R C_{\mathrm{mutex}}
]

as a fifth weighted component. 

Section VI-I begins:

> “The proposed cost function is a weighted sum ... depend delicately on the **five weights**”

and says each weight is perturbed. 

Yet only a few paragraphs later it correctly states that reservation is **absent from the sensitivity study** because it is a feasibility constraint. 

The Conclusion then reverts again to a:

> “5-component edge traversal cost function”

containing (w_RR_{\text{lock}}). 

This must be globally corrected.

This is more than stylistic because the actual mathematical object being proposed changes from a five-term objective to a constrained optimization problem.

---

### 4. **[MAJOR] Figure 7 is clearly stale and contradicts both the revised method and the current dataset.**

Page 14 is particularly problematic.

The text correctly says reservation is not a weighted sensitivity parameter. Yet Figure 7 still plots:

* (w_D)
* (w_M)
* (w_H)
* **(w_R)**
* (w_S)

and the caption says:

> “Sensitivity of the **five cost weights**.”



The current released sensitivity dataset contains 510 rows corresponding to the nominal condition plus perturbations of the **four operative weights**; (w_R) remains fixed rather than being varied.

Even more importantly, the current figure generator itself still contains:

> `weights = ["w_D", "w_M", "w_H", "w_R", "w_S"]`

So this is not merely an old caption—the generation pipeline itself was not fully updated after the scientific reformulation.

That conflicts with one of the manuscript's strongest reproducibility claims: that every figure is generated automatically from the current analysis.

The figure generator must be fixed and Figure 7 regenerated with **four** weights only.

---

### 5. **[MAJOR] Table III is also inconsistent with the current experiment and with its own caption.**

The caption currently states:

> “Component ablation of the **five cost terms** ... Each row removes exactly one term from Eq. (1).”

But the displayed table contains only:

* Full D²RO;
* without mesh;
* without proxemics.



Meanwhile the current raw ablation dataset actually contains **seven configurations**, including:

* reservation lifted;
* (w_S) cost only removed;
* safety controller only removed;
* both removed.

And the prose immediately above/below discusses these omitted safety configurations numerically. 

This table should be reconstructed to reflect the current experimental design. I suggest something like:

**Routing-cost ablations**

* Full;
* no mesh;
* no proxemic cost;
* reservation constraint lifted.

**Safety attribution**

* Full;
* (w_S=0), controller retained;
* controller off, (w_S) retained;
* both off.

That would make the causal structure very clear.

---

### 6. **[MAJOR] The communication-degradation analysis pipeline appears to collapse Mesh ON and Mesh OFF trials into the same channel group.**

This deserves careful checking by the authors.

The degradation CSV contains both `mesh_enabled=0` and `mesh_enabled=1` records under the same channel identifier.

But the analysis currently calls:

> `analyse_grouped("mesh_degradation.csv", "channel", ...)`

and `analyse_grouped` groups **only by the supplied `group_key`**. It does not additionally split by `mesh_enabled`.

So the analysis data structure does not actually represent:

[
\text{Mesh ON versus Mesh OFF at each loss/latency condition}.
]

The code comment says it is “grouped by channel AND arm,” but the implementation shown does not do that.

The authors should fix this before interpreting degradation.

For each channel condition they should calculate the **paired treatment effect**:

[
\Delta T_{\text{anticipation}}
==============================

## T_{\text{Mesh ON}}

T_{\text{Mesh OFF}},
]

and corresponding paired effects on backtracking and makespan.

Then plot those effects, with confidence intervals, as a function of packet loss and latency.

This is a better measure than simply plotting or quoting the absolute Mesh-ON lead time because it preserves the controlled design of Mechanism A.

---

### 7. **[MAJOR] The claimed “10% packet-loss tolerance threshold” needs statistical support.**

The revised communication experiment is much better placed than the previous one because it now degrades communication where communication actually matters. That is a strong improvement. The paper reports anticipation falling from roughly 11 s to around 6–7 s under 20% loss. 

But the paper then says:

> “anticipatory rerouting tolerates packet loss up to about 10% ... and degrades materially beyond that.”



There are no uncertainty intervals or tests attached to this threshold.

After fixing Comment 6, the authors should analyze either:

* channel condition × mesh arm with a repeated-measures model; or
* paired Mesh-ON/OFF effect at each channel condition, followed by a trend/model across loss and latency.

The word **“10% tolerance”** should only remain if the data support a statistically and practically meaningful change around that point. Otherwise say simply that degradation becomes progressively visible at higher packet-loss rates.

---

### 8. **[IMPORTANT] Figure 4 has not fully adopted the new person-seconds metric.**

The prose now correctly describes intimate exposure as person-seconds. Table II even explicitly explains why the metric is person-time. 

Yet Figure 4(c) still says:

> “Intimate-space exposure (control ticks)”

and plots values 128/204. 

The figure generator also still uses the legacy `intimate_exposure` field and labels it in control ticks rather than the newly exported person-seconds.

The primary figure should now use **person-seconds**. Person-ticks can remain as an internal or supplementary diagnostic if desired.

---

### 9. **[IMPORTANT] The corrected safety-radius explanation is contradicted by Table I.**

The revised text correctly states that 0.40 m is an **effective safety radius**, not the inscribed radius of the 0.72 × 0.48 m chassis, whose actual inscribed radius is 0.24 m. 

But Table I still labels:

> “Inscribed Safety Radius (r_{\text{robot}}) — 0.40 m”



Change this to something like:

**Effective safety / swept-envelope radius: 0.40 m**

and, if relevant, separately state the physical geometric half-width of 0.24 m.

---

### 10. **[IMPORTANT] The graph should probably not be described mathematically as simply “undirected.”**

Section III begins with an:

> “undirected planar topological graph (G=(V,E)).”



But the framework subsequently relies explicitly on directional costs and on treating ((u,v)) and ((v,u)) differently when reservation information is present.

The implementation likewise represents corridors through directed edges/arcs.

A cleaner formulation would be:

* an **undirected physical roadmap** (G=(V,E)), from which
* each agent maintains a **directed local cost graph** (\vec G_i=(V,A_i)).

That would make the mathematics agree with the actual directional reservation mechanism.

---

### 11. **[IMPORTANT] “Line-of-sight” terminology is still used where the simulator only implements range-limited sensing.**

The paper deserves credit for explicitly acknowledging later that sensing is:

> “range-limited rather than line-of-sight ... without ray-casting against shelf occlusion.”



But elsewhere the manuscript still repeatedly calls this **line-of-sight sensing**, and Table V's caption even says the blockage is “out of line of sight.” 

Those are different assumptions.

Every occurrence should say something like:

> “outside the follower's onboard sensing radius”

unless actual visibility/occlusion ray-casting is implemented.

---

### 12. **[IMPORTANT] The cross-domain result supports transfer within three simulations, but “generality is therefore demonstrated” is too strong.**

The authors show something valuable: the same planner and weights operate across supermarket, hospital and airport synthetic topologies without retuning. 

But all three are hand-designed domains within the same simulator, using the same physics abstraction and sensing model.

I would change:

> “Generality is therefore demonstrated”

to:

> “Cross-topology transfer within the evaluated simulation family is demonstrated.”

That is still a worthwhile result and is much harder for a reviewer to attack.

---

### 13. **[MINOR TECHNICAL] RF attenuation should not be expressed in dBm.**

The deployment discussion states that metal shelves attenuate 2.4 GHz signals by “−15 to −25 dBm.” 

Attenuation is a **relative loss** and should normally be reported in **dB**, whereas dBm is an absolute power level.

They should also provide a reference for that numerical range or remove the numerical claim.

---

## One more important point: their internal quality-control system is not yet catching manuscript contradictions

This may be the most useful meta-comment to give them.

They now have claim verification, dataset fingerprints, CI and automated generation. That is good. But the current paper simultaneously contains:

* four weighted terms in the abstract/formal model;
* five weighted terms in the Introduction;
* four weights in the sensitivity prose;
* five weights in Figure 7;
* a three-row table claiming to ablate five terms;
* four stated research aims;
* a conclusion saying there are “three aims.”

For example, the Conclusion literally says the framework has a five-component cost and that it is evaluated against “the three aims,” immediately before discussing **A1–A4**. 

That means their automated checker is validating **numbers**, but not validating the **semantic structure of the manuscript**.

I would ask them to add simple release checks for things such as:

* no `w_R` in weighted-objective/sensitivity captions;
* no “five weights” after the four-weight reformulation;
* exactly four aims;
* no “control ticks” in primary exposure figures;
* no “inscribed radius = 0.40 m”;
* no “line-of-sight” claims unless occlusion is implemented.

These are very easy CI gates and would stop the same class of regression recurring.

## Final judgment

Compared with the previous round, I think the authors have done enough substantive scientific work that **rejection would now be premature**.

They did not evade the difficult comments. They actually changed the code and experiments, and several of those changes weakened their original story—for example, the local-social baseline shows that the distributed layer is slower and provides no broad-scenario social advantage. That is a positive sign of research integrity. 

But I would still return this as:

**MAJOR REVISION — one further substantive round warranted.**

The two issues I would label as genuinely blocking are:

1. **the route×yield experiment still does not isolate the factor it claims to isolate and lacks interaction statistics**, and
2. **the communication-degradation analysis needs to preserve the Mesh ON/OFF pairing instead of grouping only by channel**.

The rest is largely a **consistency and regeneration problem**, albeit a surprisingly extensive one.

If they fix those two scientific issues, regenerate all affected tables/figures, and perform a complete semantic consistency sweep, my next decision could realistically move to **Minor Revision** rather than another Major Revision. If, on the other hand, the next response only edits wording around those two problems without correcting the experiment/analysis, I would then consider rejection justified.
