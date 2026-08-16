"""
Export the public subset of this repository into a standalone tree.

WHY A SCRIPT AND NOT A FOLDER MOVE
----------------------------------
The obvious way to split a repo is to move everything public into one directory
and use `git subtree split`. That would be wrong here. The dataset provenance
fingerprint hashes each source file's path RELATIVE TO THE REPOSITORY ROOT, so
moving `d2ro/` to `public/d2ro/` changes every recorded path, changes the
fingerprint, and marks all eleven datasets STALE -- costing a full regeneration
for a purely cosmetic rearrangement, on top of rewriting every import, test path
and CI path.

An allowlist avoids all of it. The private tree keeps its layout; this script
copies the named paths into a staging directory and builds a fresh single-commit
history there. Nothing from the private history is transferred, only files, so
there is no mechanism by which an unpublished draft could leak through a
forgotten branch or a dangling object.

WHAT IS DELIBERATELY EXCLUDED
-----------------------------
`paper/` in its entirety -- the manuscript is unpublished and all-rights-reserved.
`docs/*.md` -- revision plans, reviewer correspondence and response letters.
`literature/` -- third-party PDFs we have no right to redistribute.

Usage:
    python scripts/publish_public.py                 # stage and report
    python scripts/publish_public.py --out DIR       # stage somewhere specific
    python scripts/publish_public.py --git           # also init a single commit
    python scripts/publish_public.py --git --push    # stage, commit and publish

Pushing is left to you on purpose: it is the irreversible step, and it should be
a deliberate act rather than a side effect of running a script.
"""
from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys


def _force_remove(func, path, _exc):
    """
    Git writes its loose objects read-only, and Windows refuses to unlink those.
    Without this, re-staging silently leaves the previous tree in place -- which is
    worse than failing, because the verification steps then pass against stale
    content and the wrong thing gets published.
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(os.path.dirname(ROOT), "SW-DGO-public")
DEFAULT_REMOTE = "https://github.com/polla-fattah/SW-DGO.git"

# (source path relative to repo root, destination path in the public tree)
# A destination of None keeps the same relative path.
ALLOWLIST: list[tuple[str, str | None]] = [
    # The simulation package, including its test suite.
    ("d2ro", None),

    # Runnable entry points: the desktop demos and the web-bundle tooling.
    ("scripts/demo_main.py", None),
    ("scripts/demo_supermarket.py", None),
    ("scripts/demo_hospital.py", None),
    ("scripts/demo_airport.py", None),
    ("scripts/build_web_bundle.py", None),
    ("scripts/check_web_bundle.py", None),

    # The experiment driver.
    ("run_full_suite.py", None),

    # The browser simulator (Pyodide/WASM). GitHub Pages serves docs/ directly.
    ("docs/index.html", None),
    ("docs/simulator.html", None),
    ("docs/landing.css", None),
    ("docs/simulator.js", None),
    ("docs/python_bundle.js", None),
    ("docs/styles.css", None),

    # Raw data plus the pipeline that turns it into statistics. Kept together on
    # purpose: data without the analysis is not reproducible, and analysis
    # without data is not runnable.
    ("experiments/data", None),
    # Two directory levels deep, matching paper/scripts/, because the script
    # derives the project root by walking up exactly that far.
    ("paper/scripts/analyze_results.py", "analysis/scripts/analyze_results.py"),

    # Licences: MIT for code, CC BY 4.0 for the datasets. paper/LICENSE
    # (all rights reserved) is deliberately NOT carried across.
    ("LICENSE", None),
    ("LICENSE-DATA", None),

    ("requirements.txt", None),
    ("_public/README.md", "README.md"),
    ("_public/.gitignore", ".gitignore"),
    ("_public/ci.yml", ".github/workflows/ci.yml"),
]

SKIP_DIR_NAMES = {"__pycache__", ".pytest_cache", ".git"}
SKIP_SUFFIXES = (".pyc", ".pyo")


def copy_tree(src: str, dst: str) -> int:
    n = 0
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES]
        for fn in files:
            if fn.endswith(SKIP_SUFFIXES):
                continue
            s = os.path.join(root, fn)
            d = os.path.join(dst, os.path.relpath(s, src))
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--git", action="store_true",
                    help="initialise a git repo with a single commit")
    ap.add_argument("--remote", default=DEFAULT_REMOTE,
                    help="remote URL to attach (default: %(default)s)")
    ap.add_argument("--push", action="store_true",
                    help="force-push to the remote after committing")
    args = ap.parse_args()

    out = os.path.abspath(args.out)
    if os.path.exists(out):
        if sys.version_info >= (3, 12):
            shutil.rmtree(out, onexc=_force_remove)
        else:
            shutil.rmtree(out, onerror=_force_remove)
    os.makedirs(out)

    total, missing = 0, []
    for src_rel, dst_rel in ALLOWLIST:
        src = os.path.join(ROOT, src_rel)
        dst = os.path.join(out, dst_rel or src_rel)
        if not os.path.exists(src):
            missing.append(src_rel)
            continue
        if os.path.isdir(src):
            n = copy_tree(src, dst)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            n = 1
        total += n
        print(f"  {n:4d}  {src_rel}" + (f"  ->  {dst_rel}" if dst_rel else ""))

    if missing:
        print("\nERROR: allowlisted paths that do not exist:")
        for m in missing:
            print(f"  - {m}")
        return 1

    # A leak here would be unrecoverable once pushed, so verify rather than trust.
    leaked = []
    for root, dirs, files in os.walk(out):
        dirs[:] = [d for d in dirs if d != ".git"]
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), out).replace(os.sep, "/")
            if rel.startswith("paper/") or rel.endswith((".tex", ".pdf", ".bib")):
                leaked.append(rel)
    if leaked:
        print("\nERROR: manuscript material reached the public tree:")
        for l in leaked[:10]:
            print(f"  - {l}")
        return 1

    print(f"\n{total} files staged in {out}")
    print("No manuscript, revision plan or reviewer correspondence was copied.")

    if args.git:
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=out, check=True)
        subprocess.run(["git", "add", "-A"], cwd=out, check=True)
        subprocess.run(["git", "commit", "-q", "-m",
                        "SW-DGO: socially-weighted distributed graph optimization "
                        "for multi-agent service fleets"], cwd=out, check=True)
        # This directory is deleted and re-created on every run, so a remote added
        # by hand does not survive -- which produced a confusing
        # "'origin' does not appear to be a git repository" on the second publish.
        # Attaching it here makes the staging tree push-ready every time.
        subprocess.run(["git", "remote", "add", "origin", args.remote],
                       cwd=out, check=True)
        print(f"Initialised a single-commit history on `main`, remote -> {args.remote}")

        if args.push:
            # --force because the history is rebuilt from scratch each run; the
            # public repo is a mirror of a subset, not a shared working branch.
            r = subprocess.run(["git", "push", "--force", "-u", "origin", "main"],
                               cwd=out)
            if r.returncode:
                print("\nPush failed. The tree is staged and committed, so you can "
                      "retry with:")
                print(f"  cd {out} && git push --force origin main")
                return 1
            print("Pushed. GitHub Pages takes about a minute; hard-refresh after.")
        else:
            print("\nTo publish:")
            print(f"  cd {out} && git push --force origin main")
            print("  (or re-run this script with --push)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
