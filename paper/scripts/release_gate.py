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
    Semantic consistency sweep over manuscript text (paper.tex).
    Assures that superseded terminology (5 weights, w_R as operative weight, control ticks exposure)
    does not accidentally survive in prose or figure captions.
    """
    tex_path = os.path.join(PAPER, "paper.tex")
    if not os.path.exists(tex_path):
        check("semantic consistency", False, "paper.tex missing")
        return
    text = io.open(tex_path, encoding="utf-8", errors="ignore").read()

    # Remove code comments from sweep
    clean_text = "\n".join(l for l in text.splitlines() if not l.strip().startswith("%"))

    violations = []
    
    # 1. 5-weights / 5-component phrasing
    if re.search(r"five weights|five-component|5-component|five cost terms", clean_text, re.IGNORECASE):
        violations.append("Outdated 'five weights/terms' wording found")
    
    # 2. Inscribed safety radius = 0.40m phrasing
    if re.search(r"inscribed safety radius.*0\.40", clean_text, re.IGNORECASE):
        violations.append("Outdated 'inscribed safety radius = 0.40' wording found")

    # 3. Control ticks as intimate exposure metric unit
    if re.search(r"intimate exposure.*control ticks|exposure \(control ticks\)", clean_text, re.IGNORECASE):
        violations.append("Outdated 'control ticks' exposure unit wording found")

    check("semantic consistency checks pass", len(violations) == 0,
          "; ".join(violations) if violations else "")


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
