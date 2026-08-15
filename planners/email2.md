Yes. I checked both the new PDF and the latest GitHub activity. This time I see **real, substantive changes in the experimental code**, not just rewritten claims. I would tell them that explicitly.

But I would also tell them **not to submit this PDF yet**. The code is now much more defensible, while the paper is still partly describing the old synthetic results and, more importantly, some of the genuine new results actually contradict the paper's central claims.

### What has genuinely improved

The biggest issue from our previous review appears to have been addressed. The current experiment runner no longer creates the ablation results from numbers such as `14.6 + random.uniform(...)`. It now instantiates the actual environment, actual `TrolleyAgent`s, switches individual components on/off through feature flags, advances humans and robots through the simulation loop, and records the resulting success, travel time, deadlocks, discomfort, and scrapes.

The cross-domain study is also now genuinely executed. The code creates separate supermarket, hospital, and airport environments, instantiates agents and humans, runs each simulation until completion/timeout, and records the measured results.

Likewise, the crowd-density experiment now actually spawns the requested number of humans, runs the agents, measures latency and discomfort, and writes the observed results. It is no longer adding noise around predetermined numbers.

They also fixed the ORCA problem we found. The revised implementation now excludes the agent itself using `peer.agent_id == self.agent_id`, and uses actual peer velocity to construct the relative velocity rather than simply using the current agent's own velocity. The commit also adds real `time.perf_counter()` measurement to the baselines.

And importantly, the Git history confirms that the old datasets were replaced. The `"adding the data files"` commit shows the previous artificial-looking ablation records being removed and replaced with a completely different dataset.

So, based on code inspection, **I would no longer accuse the current experimental pipeline of generating synthetic results.** I have not independently executed all 2,500 runs myself, so I would phrase it as “the current code appears to perform genuine simulations and generate measurements from them,” rather than claiming independent reproduction.

## But the genuine results created a new scientific problem

This is the part I would particularly tell your friends.

They did exactly what we wanted: they allowed the simulation to produce whatever results it actually produced.

And the real results are **far less perfect** than the old ones.

That is good scientifically.

For example, Table IV now reports cross-domain success as:

* Supermarket: **100%**
* Hospital: **92%**
* Airport: **80%**



And scalability now falls from **97% success with 2 carts to 78% with 12 carts**. 

Those results actually look much more believable than the previous “100% everywhere” story.

They should **embrace those results rather than try to make them look perfect**.

### 1. The abstract is still using the old result

The abstract says:

> D²RO achieves a **100.0% mission success rate**, zero deadlocks and zero intimate violations.



But the new Table II says:

**97.0% success**
**0.59 ± 5.90 intimate violations**



So the abstract is objectively wrong according to their current experiment.

The conclusion also still says:

> “100.0% mission success rate, 0.00 ± 0.00 ... intimate ...”



They need to regenerate the abstract and conclusion from the new data.

---

### 2. Figure 7 is STILL the old figure

This is almost funny now because the code may finally be correct, but the PDF has not caught up.

Table II says D²RO = **97%**.

Yet Figure 7 still visually labels D²RO as **0.0% success**. 

The figure also still contains old APF/social-violation values such as **165.5**, while Table II now reports APF as **226.39 ± 69.25**. 

They simply need to regenerate Figure 7 from the new CSV.

But they absolutely must do it before submitting.

---

### 3. Figure 8 is also still based on the old ablation experiment

This is even more obvious.

The new Table III says:

| Configuration | Makespan | Discomfort |
| ------------- | -------: | ---------: |
| Full D²RO     |  22.98 s |       0.63 |
| no Mesh       |  15.24 s |       0.43 |
| no Lock       |  15.24 s |       0.43 |
| no Proxemics  |  32.70 s |      71.56 |
| no Safety     |  21.26 s |       0.41 |



But Figure 8 still displays the old values:

**12.5, 48.9, 22.0, 95.5, 24.1**. 

That figure must be completely regenerated.

---

# More important: the new ablation results do NOT support some of their old claims

This is the biggest thing I would discuss with them as a friend.

Their old claim was:

> Removing the V2V mesh increases makespan by 48.3%.

The manuscript still says exactly that:

[
14.57s \rightarrow 21.61s
]

and claims the mesh enables rerouting 7.04 seconds earlier. 

But the **new genuine experiment says the opposite**.

Full D²RO:

[
22.98s
]

without mesh:

[
15.24s.
]



So in this particular experiment:

[
\text{No Mesh is faster than Full D²RO}.
]

That is not a formatting error.

That is a **scientific result**.

They cannot keep saying the mesh reduced makespan by 48.3%.

They either have to accept and explain this result, or design an appropriate experiment specifically testing the conditions under which anticipatory mesh communication should help.

---

# The same problem exists for the lock ablation

Look closely at Table III:

**without mesh:**

[
15.24\pm1.95,\quad J=0.43\pm1.99
]

**without lock:**

[
15.24\pm1.95,\quad J=0.43\pm1.99
]



The raw CSV is even clearer. Trial after trial, the no-mesh and no-lock configurations frequently have exactly the same output—for example trial 1 is 14.5/0.64 for both, trial 2 is 14.5/0.18 for both, etc.

I don't immediately interpret that as dishonesty. Given that the current code genuinely toggles the two independent flags, a more likely explanation is:

> **The chosen ablation scenario does not sufficiently activate either mechanism, or both disabled mechanisms happen to lead to the same effective trajectory.**

That is scientifically important.

If their claimed novelty includes mesh anticipation and bottleneck locking, the experiment must actually contain situations where those features matter.

## What I would advise them to do

I would tell them:

**Do not change the simulator until it gives the old result.**

Instead, construct controlled experiments corresponding directly to each claim.

For example, to test the mesh contribution, create a scenario where:

1. robot A encounters a blockage;
2. robot B is outside local sensing range;
3. B has an upstream junction where it can still choose another route;
4. compare exactly the same seed and situation with mesh ON and OFF.

Then measure:

[
\Delta T_{\text{anticipation}},
]

backtracking distance,

makespan,

and number of unnecessary aisle entries.

That would directly test their strongest new novelty claim.

For the lock mechanism, construct a single-file corridor where two robots approach from opposite ends, with no geometrically possible passing.

Compare:

**lock enabled vs lock disabled**

over randomized arrival timings.

Measure:

* head-on conflicts;
* timeout rate;
* waiting time;
* successful traversal;
* starvation.

That would demonstrate what the lock actually contributes.

Those can be additional **mechanism-specific experiments**. They should not replace the broader Monte Carlo evaluation.

---

# Their new results may actually lead to a better paper

This is something I would encourage them about.

Before, their paper suspiciously said:

> D²RO wins everything, 100%, zero violations, perfect scalability.

Now the genuine simulations are saying something much more interesting:

> D²RO performs strongly in the supermarket benchmark, but performance degrades in hospital/airport environments and as fleet size increases.

For example, airport success falls to **80%**, and 12-cart success falls to **78%**.  

That's not embarrassing.

That's research.

They should analyze **why**.

Maybe:

* mesh communication grows too noisy;
* mutex waiting increases;
* the graph becomes congested;
* the same weights are inappropriate across domains;
* airport topology behaves differently;
* crowd-induced costs over-penalize certain routes.

That discussion could be substantially more valuable than claiming 100% success everywhere.

---

# One more problem: they still have the unresolved citation

The new PDF still says:

> “HA-VLN 2.0 [?]”



Easy fix, but it should be done.

---

# What the Git history tells me

There really was a concentrated burst of activity after the criticism. Recent commits include:

* `"adding the data files"`
* `"fixing according to the new comments"`
* `"fixing the paper"`
* `"Other relivants"`

all on August 15. The code-fix commit specifically changes ORCA, baseline timing, ablation flags, and related experimental functionality.

One detail I would mention privately rather than accuse them over: the new data commit occurred shortly before the corresponding code-fix commit. That does **not necessarily mean anything improper**—they may have made and run the changes locally, then split the Git commits—but for clean reproducibility in the future, they should do this instead:

**code commit → tag code → run experiment → commit raw results → generate figures/tables.**

That gives reviewers an unambiguous provenance chain.

---

# What I would tell them now

Something short like:

> I checked your new GitHub changes. The experimental pipeline is substantially improved and, unlike the previous version, the ablation, cross-domain and scalability experiments now appear to execute the actual simulator rather than generating values around predetermined means. The ORCA self-interaction/relative-velocity problem and hard-coded timing measurements have also been addressed.
>
> However, please do not submit the current PDF yet. The manuscript has not been synchronized with the genuine new results. The abstract and conclusion still claim 100% success and zero social violations, while Table II reports 97% success and nonzero violations. Figures 7 and 8 still contain the old data. More importantly, the new ablation results do not support the previous claim that removing V2V mesh increases makespan by 48.3%; in the current genuine results, the no-mesh and no-lock configurations are actually faster than the full system and are nearly identical. This should be investigated scientifically rather than overwritten.
>
> I recommend keeping these genuine results, designing separate controlled experiments that specifically exercise anticipatory mesh propagation and corridor locking, regenerating every figure/table directly from the final CSVs, and rewriting the claims to match what the experiments actually show. The fact that hospital, airport and large-fleet performance is less than perfect is acceptable and actually makes the study more credible; explain those limitations rather than trying to preserve the previous 100% claims.

### My status now

Compared with the version we rejected:

**Experimental integrity:** 🟢 **much improved**
**ORCA implementation:** 🟢 **specific issue fixed**
**Measured timings:** 🟢 **improved**
**Cross-domain/scalability runs:** 🟢 **now appear genuine**
**Paper ↔ data synchronization:** 🔴 **not fixed**
**Figures:** 🔴 **old results remain**
**Mesh/lock contribution evidence:** 🔴 **current genuine ablation does not support the existing claims**
**Ready to submit:** 🔴 **No**

So I would **encourage them this time** rather than just repeat the rejection. They appear to have taken the core research-integrity criticism seriously. Their next job is not to “make the numbers better”; it is to make the **paper honestly follow the new numbers** and design targeted experiments for the contributions the current broad scenario does not adequately exercise.
