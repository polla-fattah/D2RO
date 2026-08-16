"""
Release gate: refuses to certify a manuscript that is not reproducible.

Round-3 review opened with a provenance failure, not a science failure: the
submitted PDF claimed release `v2.0-review2` at commit `e3d6582-dirty` while the
repository had no tags and no releases, and the `-dirty` suffix meant the PDF had
been built from a tree that did not match the named commit. Earlier still, a PDF
went out containing unresolved `Table ??` references and a provenance table saying
every dataset was STALE.

Every one of those failures is mechanically detectable, so none of them should ever
reach a reviewer again. This script is the check, and it is intended to run both
locally before submission and in CI on a tag.

Checks, in order of severity:

  1. every dataset reports `ok` (not missing / incomplete / STALE / unverified)
  2. every numeric claim in the prose matches analysis_results.json
  3. the LaTeX log contains no unresolved reference or citation
  4. the compiled PDF contains no literal "??"
  5. the commit stamp is a clean SHA -- no `-dirty` suffix
  6. the bibliography audit reports no unexplained entry (optional; needs network)

Usage:
    python paper/scripts/release_gate.py            # full gate
    python paper/scripts/release_gate.py --no-net   # skip the Crossref audit
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAPER = os.path.join(BASE, "paper")
DATA = os.path.join(BASE, "experiments", "data")

GREEN, RED, YELLOW, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[0m"
if os.name == "nt" and not os.environ.get("CI"):
    GREEN = RED = YELLOW = RESET = ""

failures: list[str] = []
warnings: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    mark = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
    print(f"  [{mark}] {name}" + (f" -- {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(f"{name}: {detail}" if detail else name)


def warn(name: str, detail: str) -> None:
    print(f"  [{YELLOW}WARN{RESET}] {name} -- {detail}")
    warnings.append(f"{name}: {detail}")


# --------------------------------------------------------------------------- #
def gate_datasets() -> None:
    path = os.path.join(DATA, "analysis_results.json")
    if not os.path.exists(path):
        check("datasets analysed", False, "analysis_results.json missing")
        return
    results = json.load(io.open(path, encoding="utf-8"))
    bad = {k: v.get("status") for k, v in results.items()
           if isinstance(v, dict) and v.get("status") != "ok"}
    check(f"all {len(results)} datasets report ok", not bad,
          "; ".join(f"{k}={v}" for k, v in bad.items()))


def gate_claims() -> None:
    script = os.path.join(PAPER, "scripts", "verify_manuscript_claims.py")
    r = subprocess.run([sys.executable, script], capture_output=True, text=True)
    tail = (r.stdout or "").strip().splitlines()
    summary = next((l for l in tail if "prose claims match" in l), "")
    check("prose claims match the data", r.returncode == 0, summary.strip())


def gate_latex_log() -> None:
    log = os.path.join(PAPER, "paper.log")
    if not os.path.exists(log):
        check("LaTeX log clean", False, "paper.log missing -- has the paper been built?")
        return
    text = io.open(log, encoding="utf-8", errors="ignore").read()
    undefined = re.findall(r"Warning: (Reference|Citation) `([^']+)' on page", text)
    check("no undefined references or citations", not undefined,
          ", ".join(f"{k} {v}" for k, v in undefined[:5]))
    overfull = text.count("Overfull \\hbox")
    if overfull:
        warn("overfull boxes", f"{overfull} overfull hbox(es) -- cosmetic, not blocking")


def gate_pdf_no_qq() -> None:
    pdf = os.path.join(PAPER, "paper.pdf")
    if not os.path.exists(pdf):
        check("PDF exists", False, "paper.pdf missing")
        return
    try:
        r = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True)
        text = r.stdout or ""
    except FileNotFoundError:
        warn("PDF ?? scan", "pdftotext unavailable; skipped")
        return
    # "??" is what an unresolved \ref renders as.
    hits = re.findall(r"(?:Table|Fig\.?|Section|Eq\.?)\s*\?\?", text)
    check("no unresolved '??' in the PDF", not hits,
          f"{len(hits)} occurrence(s), e.g. {hits[:3]}")


def gate_commit_stamp() -> None:
    stamp = os.path.join(PAPER, "generated", "commit.tex")
    if not os.path.exists(stamp):
        check("commit stamp present", False, "generated/commit.tex missing")
        return
    text = io.open(stamp, encoding="utf-8").read()
    m = re.search(r"\\newcommand\{\\PaperCommitSHA\}\{([^}]*)\}", text)
    sha = m.group(1) if m else ""
    check("commit stamp is a clean SHA", bool(sha) and not sha.endswith("-dirty")
          and sha != "unknown",
          f"stamp is '{sha}' -- the PDF was built from a tree that does not match "
          f"the named commit")


def gate_tag_exists() -> None:
    try:
        tags = subprocess.check_output(["git", "tag"], cwd=BASE, text=True).split()
    except Exception as exc:
        warn("git tags", f"could not read tags ({exc})")
        return
    check("repository has at least one release tag", bool(tags),
          "no tags exist; the manuscript must not cite a release that is not published")


def gate_references(skip_net: bool) -> None:
    if skip_net:
        warn("reference audit", "skipped (--no-net)")
        return
    script = os.path.join(PAPER, "scripts", "audit_references.py")
    try:
        r = subprocess.run([sys.executable, script], capture_output=True, text=True,
                           timeout=600)
    except Exception as exc:
        warn("reference audit", f"could not run ({exc})")
        return
    line = next((l for l in (r.stdout or "").splitlines() if "verifiable entries" in l), "")
    # Flagged entries are expected (documented deviations), so this warns rather
    # than fails; an entry whose DOI resolves to a different work does fail.
    if "POINTS AT A DIFFERENT WORK" in (r.stdout or ""):
        check("no reference resolves to the wrong work", False, "see audit output")
    else:
        check("no reference resolves to the wrong work", True)
    if line:
        print(f"         {line.strip()}")


def gate_semantic_consistency() -> None:
    r"""
    Semantic sweep over everything that reaches the reader.

    The claim checker validates NUMBERS. Round-3 review showed that is not enough:
    the manuscript simultaneously carried a four-term objective in the abstract and
    a five-term one in the introduction, a sensitivity figure plotting a weight the
    method section had just explained was not a weight, a three-row table whose
    caption claimed to ablate five terms, and four research aims summarised as
    "three aims". Every one of those is a semantic contradiction between parts of
    the paper, and none of them is a wrong number.

    Two properties matter here. First, the sweep must cover paper/generated/ as well
    as paper.tex -- "five cost terms" survived an earlier pass precisely because it
    lived in a generated caption rather than the prose. Second, a violation names
    the file and line, because a gate that says only "inconsistent" is a gate people
    learn to ignore.
    """
    targets = [os.path.join(PAPER, "paper.tex")]
    gen = os.path.join(PAPER, "generated")
    if os.path.isdir(gen):
        targets += [os.path.join(gen, f) for f in sorted(os.listdir(gen))
                    if f.endswith(".tex")]
    missing = [t for t in targets if not os.path.exists(t)]
    if missing:
        check("semantic consistency", False, f"missing: {missing}")
        return

    # (regex, what it means, exemption) -- exemption is a pattern that makes an
    # occurrence legitimate, checked on the same line.
    RULES = [
        (r"five weights|five-component|5-component|five cost terms|five soft|"
         r"five weighted",
         "superseded five-term objective wording", None),
        (r"inscribed safety radius[^.]{0,40}0\.40",
         "0.40 m described as the inscribed rather than effective radius", None),
        (r"exposure \(control ticks\)|intimate exposure[^.]{0,30}control ticks",
         "exposure reported in control ticks rather than person-seconds", None),
        # w_R is legitimate where the paper EXPLAINS that it was dropped -- the
        # method section argues at length why the coefficient was meaningless --
        # and illegitimate where it is presented as a live weighted term. The
        # exemption therefore keys on retrospective framing.
        (r"w_R\s*\\cdot|w_RR_|\bfive\b[^.]{0,20}w_R",
         "w_R presented as an operative weighted term",
         r"correction to earlier|was not faithful|had no operative|for every \$?w_R|"
         r"described \$w_R\$ as|previously"),
        (r"the three aims|three research aims",
         "aim count contradicts the four aims of Section II", None),
        (r"line[- ]of[- ]sight",
         "line-of-sight sensing claimed, but no occlusion ray-casting is implemented",
         r"range-limited rather than line-of-sight|rather than line of sight"),
        # An unrejected null is not an absence of effect. Round-4 review caught the
        # abstract asserting that yielding "adds nothing" while the body correctly
        # said the effect was merely undetectable.
        (r"yielding adds nothing|adds nothing on a social route|"
         r"contributes nothing on a social route",
         "a null result stated as an absence of effect", None),
        # A LaTeX control sequence whose backslash was eaten renders as literal
        # text. Two distinct forms occur; both are checked. This one is the
        # backslash simply dropped.
        (r"(?<!\\)\b(?:textbf|textit|emph|begin|end|item|section)\{",
         "LaTeX command missing its backslash (renders as literal text)", None),
        # The other form -- an escape-interpreting edit turning "\t" of \textbf
        # into a literal TAB, leaving "<TAB>extbf{" -- leaves a different fragment
        # for every command, so it is caught by its control character instead. See
        # gate_control_characters.
        # IEEEtran numbers subsubsections itself; a manual number inside the title
        # renders as "1) 1. Title".
        (r"\\subsubsection\{\s*\d+\.\s",
         "manual number inside an auto-numbered subsubsection title", None),
    ]

    violations = []
    for path in targets:
        rel = os.path.relpath(path, BASE).replace(os.sep, "/")
        for n, line in enumerate(io.open(path, encoding="utf-8",
                                         errors="ignore").read().splitlines(), 1):
            if line.lstrip().startswith("%"):
                continue
            for pattern, meaning, exempt in RULES:
                if not re.search(pattern, line, re.IGNORECASE):
                    continue
                if exempt and re.search(exempt, line, re.IGNORECASE):
                    continue
                violations.append(f"{rel}:{n} {meaning}")

    check("no superseded terminology in prose or generated artefacts",
          not violations, "; ".join(violations[:6])
          + (f" (+{len(violations) - 6} more)" if len(violations) > 6 else ""))


def gate_control_characters() -> None:
    r"""
    No literal control characters in the manuscript sources.

    This project has repeatedly corrupted LaTeX by editing it through a tool that
    interprets backslash escapes: `\textbf` becomes TAB + "extbf", `\newcommand`
    becomes NEWLINE + "ewcommand", `\begin` becomes BACKSPACE + "egin". Round-4
    review found two surviving instances rendering as "extbfeffective perception".

    The surviving fragment differs per command, so matching fragments is
    unreliable. The control character is the invariant: a TAB, form feed,
    vertical tab, backspace or bell has no legitimate place in this document, and
    its presence is near-proof that an escape was interpreted somewhere.
    """
    targets = [os.path.join(PAPER, "paper.tex")]
    gen = os.path.join(PAPER, "generated")
    if os.path.isdir(gen):
        targets += [os.path.join(gen, f) for f in sorted(os.listdir(gen))
                    if f.endswith(".tex")]

    FORBIDDEN = {"\t": "TAB", "\x0c": "form feed", "\x0b": "vertical tab",
                 "\x08": "backspace", "\x07": "bell"}
    hits = []
    for path in targets:
        if not os.path.exists(path):
            continue
        rel = os.path.relpath(path, BASE).replace(os.sep, "/")
        text = io.open(path, encoding="utf-8", errors="ignore", newline="").read()
        for n, line in enumerate(text.split("\n"), 1):
            for ch, name in FORBIDDEN.items():
                if ch in line:
                    hits.append(f"{rel}:{n} contains a literal {name}")
    check("no literal control characters in LaTeX sources", not hits,
          "; ".join(hits[:5]) + (f" (+{len(hits) - 5} more)" if len(hits) > 5 else ""))


def gate_anonymity() -> None:
    r"""
    When the manuscript is set to anonymous, nothing identifying may survive.

    Anonymising is easy to do incompletely: the author block is obvious, but the
    running head repeats a surname on every page, the acknowledgment names a
    laboratory, and a repository URL carries an account name. Desk rejection for a
    double-blind violation costs a review cycle, so the check is mechanical.

    Only runs when \anonymoustrue is set; in camera-ready mode the same strings are
    supposed to be present and their absence would be the bug.
    """
    tex = os.path.join(PAPER, "paper.tex")
    pdf = os.path.join(PAPER, "paper.pdf")
    if not os.path.exists(tex):
        return
    src = io.open(tex, encoding="utf-8", errors="ignore").read()
    if not re.search(r"^\s*\\anonymoustrue", src, re.M):
        print("  [note] manuscript is in NAMED mode; anonymity check skipped")
        return
    if not os.path.exists(pdf):
        warn("anonymity", "paper.pdf missing; cannot verify")
        return
    try:
        r = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True)
        text = (r.stdout or "")
    except FileNotFoundError:
        warn("anonymity", "pdftotext unavailable; skipped")
        return

    # Surnames, institution, contact domain and the account name inside any URL.
    IDENTIFIERS = ["Fattah", "Fawzi", "Koya", "koyauniversity", "polla-fattah",
                   "Autonomous Systems and Robotics"]
    found = sorted({w for w in IDENTIFIERS if w.lower() in text.lower()})
    check("anonymous build carries no identifying text", not found,
          "found in the PDF: " + ", ".join(found))


def gate_docs_not_superseded() -> None:
    r"""
    No document in docs/ may teach a formulation the manuscript has corrected.

    `docs/Mathematical_Formalization.md` survived two review rounds stating
    `C = D + W_mesh + H_prox + R_lock` -- four terms, but the wrong four. It
    carried the reservation as an ADDITIVE COST TERM, which is precisely what the
    manuscript spends a section establishing it is not; it omitted the kinematic
    clearance envelope entirely; and it used the "mutex" language the paper
    abandoned once the mechanism turned out to be cost-projected diversion rather
    than mutual exclusion.

    A reviewer browsing the repository would have found the corrected claim and
    its superseded version one directory apart. The manuscript is swept for this
    class of contradiction; the documentation beside it should be too.

    Reviewer correspondence and response letters are exempt: they discuss the old
    formulation precisely in order to record that it was fixed, and rewriting
    history to remove the error would defeat the purpose of keeping them.
    """
    docs = os.path.join(BASE, "docs")
    if not os.path.isdir(docs):
        return

    EXEMPT = ("email", "comments", "response_to_reviewers", "engineering_notes",
              "outstanding_work", "reference_audit")

    RULES = [
        (r"R_?\{?\\?text\{?lock\}?\}?\s*(?:\(|\+)",
         "reservation presented as an additive cost term"),
        (r"mutex lock|corridor mutex",
         "superseded 'mutex' terminology for the reservation"),
        (r"five weights|5-component|five-component|five cost terms",
         "superseded five-term objective"),
    ]

    violations = []
    for fn in sorted(os.listdir(docs)):
        if not fn.endswith(".md"):
            continue
        if any(tag in fn.lower() for tag in EXEMPT):
            continue
        text = io.open(os.path.join(docs, fn), encoding="utf-8",
                       errors="ignore").read()
        for pattern, meaning in RULES:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                line = text[:m.start()].count("\n") + 1
                violations.append(f"docs/{fn}:{line} {meaning}")

    check("no document teaches a superseded formulation", not violations,
          "; ".join(violations[:5]))


def gate_aims_consistent() -> None:
    """The manuscript declares four aims; the conclusion must assess four."""
    tex = os.path.join(PAPER, "paper.tex")
    if not os.path.exists(tex):
        check("aims consistent", False, "paper.tex missing")
        return
    text = io.open(tex, encoding="utf-8", errors="ignore").read()
    declared = set(re.findall(r"\\textbf\{(A[1-9]), ", text))
    assessed = set(re.findall(r"\\textbf\{(A[1-9]) \(", text))
    check("every declared aim is assessed in the conclusion",
          bool(declared) and declared == assessed,
          f"declared {sorted(declared)} but assessed {sorted(assessed)}")


def gate_no_invented_p_values() -> None:
    """
    Every p-value in the prose must exist in analysis_results.json.

    A previous revision quoted `p < 10^{-15}` for two factorial contrasts that the
    analysis pipeline never tested -- it computed bootstrap intervals and no
    p-value at all. The figures were plausible and entirely invented, which is the
    exact failure mode the "no hand-entered numbers" claim exists to exclude, so it
    gets a mechanical check rather than a promise.
    """
    tex = os.path.join(PAPER, "paper.tex")
    results = os.path.join(DATA, "analysis_results.json")
    if not (os.path.exists(tex) and os.path.exists(results)):
        warn("p-value provenance", "paper.tex or analysis_results.json missing")
        return
    text = io.open(tex, encoding="utf-8", errors="ignore").read()
    blob = io.open(results, encoding="utf-8").read()

    # Collect every number the analysis computed, at the precision the manuscript
    # would round it to. Scanning all values rather than only `"p":` keys matters:
    # the benchmark stores its Holm-adjusted family under comparison names
    # ("Static A* (matched controller)|intimate"), not under a key called p.
    computed = set()
    for m in re.finditer(r"-?\d+\.?\d*(?:[eE][+-]?\d+)?", blob):
        try:
            v = float(m.group(0))
        except ValueError:
            continue
        if v > 0:
            computed.add(f"{v:.1e}")

    unmatched = []
    for m in re.finditer(r"\$p(?:_\{\\text\{Holm\}\})?\s*=\s*"
                         r"([0-9.]+)\s*\\times\s*10\^\{(-?\d+)\}\$", text):
        v = float(m.group(1)) * (10 ** int(m.group(2)))
        if f"{v:.1e}" not in computed:
            unmatched.append(f"p = {m.group(1)}e{m.group(2)}")
    check("every quoted p-value appears in analysis_results.json",
          not unmatched, ", ".join(unmatched[:5]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-net", action="store_true",
                    help="skip the Crossref reference audit")
    args = ap.parse_args()

    print("Release gate\n" + "=" * 62)
    gate_datasets()
    gate_claims()
    gate_latex_log()
    gate_pdf_no_qq()
    gate_commit_stamp()
    gate_tag_exists()
    gate_semantic_consistency()
    gate_control_characters()
    gate_anonymity()
    gate_docs_not_superseded()
    gate_aims_consistent()
    gate_no_invented_p_values()
    gate_references(args.no_net)
    print("=" * 62)

    if failures:
        print(f"{RED}NOT SUBMITTABLE{RESET} -- {len(failures)} blocking issue(s):")
        for f in failures:
            print(f"   - {f}")
        return 1
    print(f"{GREEN}SUBMITTABLE{RESET}"
          + (f" ({len(warnings)} warning(s))" if warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
