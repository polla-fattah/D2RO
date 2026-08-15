# Reference Audit — Phase E

**Tool:** `paper/scripts/audit_references.py` (Crossref, DOI-first, all entries).
**Before:** 0 of 21 entries verified clean.
**After:** 16 of 20 verifiable entries clean; the remaining 4 are documented,
accepted deviations rather than errors.

The bibliography has been rebuilt from DOI-resolved metadata. Citation keys were
deliberately left unchanged, so no `.tex` edit was required and no citation could
silently break; where a key name now disagrees with the work it points at
(`koenig2002dstar` → a 2005 article), a comment in the `.bib` records why.

---

## 1. What was actually wrong

The reviewer named five bad references and judged there were too many to repair by
guesswork. That was correct and, if anything, understated.

| Key | Was | Now (DOI-verified) |
|:--|:--|:--|
| `dergachev2021distributed` | *Robotics and Autonomous Systems* | IEEE **CASE 2021**, 1489–1494 |
| `skrynnik2024learn` | *AAMAS*, missing co-author Nesterova | **AAAI 2024** 38(16), full author list |
| `keskin2024negotiation` | Keskin, Guler, Sen — *IEEE T-IV* | **Keskin, Cantürk, Eran, Aydoğan** — *AAMAS* 38 |
| `gielis2022codesign` | did not match any real record | **Gielis, Shankar, Prorok** — *Current Robotics Reports* 3 |
| `vandenberg2008orca` | *IEEE T-RO* 2008 | **ISRR 2011** book chapter (the canonical ORCA paper) |
| `ma2017lifelong` | *Autonomous Robots* journal | **AAMAS 2017** conference paper |
| `chen2020relational` | *IEEE RA-L*, authors Liu/Liu/Zeng/Manocha | **IROS 2020**, Chen/Hu/Nikdel/Mori/Savva |
| `koenig2002dstar` | AAAI-02 | **IEEE T-RO 2005**, the version held in `literature/` |
| `almutib2012dstar` | 2012 | **2011** |
| `azlan2024intcart` | 5 authors, 2024 | **7 authors, 2025** |
| `clark2021team` | Clark, R.; Punnoose; Anand; Trawny | **Clark, L.; Andre; Galante; Krishnamachari; Psounis** |
| `nugraha2024ips` | Nugraha, A.B.; Priyambodo | **Nugraha, M.H.; Abdul; Bramantyo; Rijanto; Saputra; Mahendra** |
| `edwige2024swarmslam` | journal article, "Edwige et al." | **Master's thesis**, single author Loems |
| — | 21 of 22 typed as `@article` | 9 `@inproceedings`, 8 `@article`, 2 `@incollection`, 1 `@mastersthesis`, 2 `@unpublished` |

**Seven of these were not in the reviewer's list.** They surfaced only because every
entry was checked rather than the five already known to be wrong.

## 2. `literature/D2RO.bib` is not a trustworthy source either

The handover notes previously suggested rebuilding from `literature/D2RO.bib`. That
turned out to be unsafe. Resolving every DOI in that file:

- **18 of 25** resolve to the work claimed;
- **4 resolve to entirely unrelated papers** — `Dergachev2021Distributed` pointed at
  *"Step Path Simulation for Quadruped Walking Robot"*, `Ma2021Distributed` at a soft
  aerial vehicle paper, `Ma2017Delay` at a keyphrase-extraction paper, and
  `VandenBerg2011Reciprocal` at a dead DOI;
- **3 carry no DOI at all**.

Three of the corrections in §1 (Clark, Nugraha, Azlan author lists) were wrong *in
that file too* and were fixed from the DOI record, not from it.

## 3. Two entries resolved from the PDFs rather than from metadata

- **`edwige2024swarmslam`** — the PDF in `literature/` is a **Master's thesis**
  (Université Libre de Bruxelles, supervised by Mauro Birattari, academic year
  2023–24), single author. It is now `@mastersthesis`, and the manuscript no longer
  writes "Edwige *et al.*" for a one-author thesis; it cites *Loems*.
- **`havln2024benchmark`** — the PDF genuinely *is* HA-VLN 2.0, marked
  *"Under review as a conference paper at ICLR 2026"* with **anonymous authors**
  (double-blind). See §5: this one still needs a decision.

## 4. Accepted deviations (flagged by the tool, correct as recorded)

| Key | Flag | Why it is accepted |
|:--|:--|:--|
| `stern2019multi` | Crossref year 2021 | That is the AAAI OJS deposit date; the paper is SoCS **2019** |
| `vandenberg2008orca` | container = *Springer Tracts in Advanced Robotics* | That is the series; the `booktitle` names the symposium volume, which is more useful to a reader |
| `ma2017lifelong` | venue wording | "AAMAS" vs Crossref's expanded conference name — same venue |
| `edwige2024swarmslam` | unverifiable | A Master's thesis is not in Crossref; verified by hand from the PDF |

## 5. Outstanding — needs an author decision

**`havln2024benchmark` has no author field**, which BibTeX warns about. The PDF held
in `literature/` is the **anonymous double-blind ICLR 2026 submission**, so there are
no authors to record from it. The reviewer stated that the official HA-VLN 2.0 is a
later benchmark by Dong, Wu, He and collaborators, and that the earlier 2024 HA-VLN
paper is a different work with different authorship.

Three options, none of which should be chosen without the authors' input:

1. cite the **arXiv/published HA-VLN 2.0** with its real author list;
2. cite the **earlier HA-VLN (2024)** paper, if that is what the argument actually
   relies on;
3. keep citing the anonymous submission, which is defensible but unusual and will
   read oddly to a reviewer.

No author names have been invented to silence the warning.

## 6. Tooling changes made during this audit

The audit tool now **resolves the DOI when an entry has one**, instead of searching
by title. Title search returns whatever ranks highest and will confidently hand back
a *different* paper, producing "author mismatch" findings that are the search's fault
rather than the entry's — which is exactly what it did for `slyusar2016manet` and
`chen2020relational` on the first pass. Comparison also now normalises LaTeX accents
(`{\"u}` = `ü`) and `\&` vs `&amp;`, and keeps multi-word surnames intact
("Mohamad Azlan", "van den Berg") instead of truncating them to the last token.

Without those fixes the tool reported failures on correct entries, which would make
it useless as the CI gate planned for Phase F.

## 7. Reproducing

```bash
python paper/scripts/audit_references.py
```

Exit status is non-zero while any entry is flagged.
