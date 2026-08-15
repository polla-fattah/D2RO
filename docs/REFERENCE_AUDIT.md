# Reference Audit — Phase E

**Tool:** `paper/scripts/audit_references.py` (Crossref, all entries).
**Result: 0 of 21 verifiable entries passed clean.** The reviewer named five wrong
references and judged that there were too many to repair by guesswork. That judgement
was correct, and conservative.

> **Read this first.** The tool reports *candidates for review*, not verdicts. It
> matches on title, so it can retrieve the wrong record and then "find" disagreements
> that reflect its own bad match rather than a bad entry (see §3). Nothing here has
> been auto-corrected. Every entry must be fixed by a human against the publisher
> record.

---

## 1. Confirmed wrong — venue or authorship is materially incorrect

These are real errors. Crossref independently corroborates the reviewer on four of
them, and the audit found three more the reviewer did not list.

| Key | Recorded | Actual (Crossref) | DOI |
|:--|:--|:--|:--|
| `dergachev2021distributed` | *Robotics and Autonomous Systems* | **IEEE CASE 2021** | `10.1109/case49439.2021.9551564` |
| `skrynnik2024learn` | *Autonomous Agents and Multi-Agent Systems* | **Proc. AAAI 2024**, 38(16) | `10.1609/aaai.v38i16.29704` |
| `keskin2024negotiation` | Keskin, Guler, Sen — *IEEE T-IV* | **Keskin, Cantürk, Eran, Aydoğan**, *AAMAS* 38 | `10.1007/s10458-024-09639-8` |
| `gielis2022codesign` | (title unmatched as recorded) | **Gielis, Shankar, Prorok**, *Current Robotics Reports* 3, 213–225 | `10.1007/s43154-022-00090-9` |
| `vandenberg2008orca` | *IEEE Transactions on Robotics* | **ICRA 2008** (conference) | `10.1109/robot.2008.4543489` |
| `ma2017lifelong` | *Autonomous Robots* | **AAMAS** (conference) | — |
| `chen2020relational` | *IEEE RA-L* | **IROS 2020** (conference) | `10.1109/iros45743.2020.9340705` |

`skrynnik2024learn` is also missing co-author **Nesterova**.

**The last three were not in the reviewer's list.** They were found only because the
audit checked all 21 entries rather than the five already known to be wrong — which
is precisely why the reviewer asked for a full audit.

## 2. Confirmed wrong — year

| Key | bib | Crossref |
|:--|--:|--:|
| `stern2019multi` | 2019 | 2021 (also missing author **Barták**) |
| `wagner2011mstar` | 2011 (IROS) | 2015 (*Artificial Intelligence* journal version) |
| `azlan2024intcart` | 2024 | 2025 |

`wagner2011mstar` needs a decision rather than a correction: the conference (IROS
2011) and journal (*Artificial Intelligence*, 2015) versions are different works.
Cite whichever is intended, consistently.

## 3. Unresolved — no reliable Crossref match (manual check required)

Eight entries could not be matched by title. This does **not** prove them wrong; it
means the recorded title does not retrieve the work, which is itself a warning sign,
and for some it simply reflects poor indexing or a title typo.

`koenig2002dstar`, `dergachev2024decentralized`, `almutib2012dstar`,
`zafari2019survey`, `clark2021team`, `nugraha2024ips`, `kruse2013human`,
`havln2024benchmark`

`havln2024benchmark` is the one the reviewer flagged specifically: the manuscript
cites "HA-VLN 2.0" but the entry is a different work. Resolve which is intended.

## 4. Tool artefacts — ignore these, they are my matcher's fault

Recorded so nobody wastes time "fixing" a correct entry:

- `slyusar2016manet` matched a Meghanathan book chapter — wrong record retrieved.
- `chen2020relational` author diff lists a completely disjoint author set, i.e. the
  matcher landed on a different paper; the **venue** finding for it is nonetheless
  corroborated separately.
- `vandenberg2008orca` author diff (`Berg` vs `van den Berg`, `Lin` vs `Ming Lin`)
  is a name-particle formatting artefact, not an error.
- `azlan2024intcart` author diff is likewise a multi-part-surname formatting issue.
- "NO DOI in bib" is flagged on nearly every entry. That is a completeness gap, not
  an error — but DOIs should be added, since they are what makes the next audit cheap.

## 5. Recommended fix procedure

1. Do **not** hand-patch the seven confirmed entries and stop. Rebuild the whole
   bibliography from publisher records, adding a `doi` field to every entry.
2. Prefer `literature/D2RO.bib` (26 entries) where it already holds verified
   metadata; it was compiled from the actual PDFs in `literature/`.
3. Fix entry **types** as well as content: 21 of 22 entries are `@article`, including
   several conference papers. That uniformity is itself evidence the file was
   generated without checking.
4. Re-run `python paper/scripts/audit_references.py` until only §3-style
   unmatchable-but-verified entries remain, and record why each survivor is accepted.
5. Wire the audit into CI (Phase F) so a wrong reference cannot reach a submission
   again.

## 6. Reproducing

```bash
python paper/scripts/audit_references.py
python paper/scripts/audit_references.py --json audit.json    # full findings
```

Exit status is non-zero while any entry is flagged, so it can gate a release build.
