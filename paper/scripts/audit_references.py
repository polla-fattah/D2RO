"""
Machine-checks every entry in paper/references.bib against Crossref.

Round-2 review identified five demonstrably wrong references and concluded there
were too many to repair by guesswork. This audits ALL of them rather than the five
that happened to be caught, because an entry nobody has checked is not evidence
that it is correct.

For each entry the recorded title is looked up on Crossref and the returned
metadata (authors, year, container/venue, DOI, publication type) is diffed against
what the .bib claims. Nothing is rewritten automatically: the tool reports, a human
decides. Silently "fixing" a bibliography from a fuzzy title match is how wrong
references get laundered into looking right.

Usage:
    python paper/scripts/audit_references.py            # audit, print report
    python paper/scripts/audit_references.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIB = os.path.join(BASE_DIR, "references.bib")
MAILTO = "polla.fattah@koyauniversity.org"   # Crossref polite pool
UA = f"D2RO-reference-audit/1.0 (mailto:{MAILTO})"

ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,]+),(.*?)\n\}", re.S)
FIELD_RE = re.compile(r"(\w+)\s*=\s*[{\"](.*?)[}\"]\s*,?\s*\n", re.S)


def parse_bib(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    out = []
    for m in ENTRY_RE.finditer(text):
        kind, key, body = m.group(1), m.group(2).strip(), m.group(3)
        fields = {k.lower(): re.sub(r"\s+", " ", v).strip()
                  for k, v in FIELD_RE.findall(body + "\n")}
        out.append({"type": kind.lower(), "key": key, "fields": fields})
    return out


def crossref(title, rows=3):
    q = urllib.parse.urlencode({
        "query.bibliographic": title, "rows": rows, "mailto": MAILTO})
    req = urllib.request.Request(f"https://api.crossref.org/works?{q}",
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read())["message"]["items"]


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def title_match(a, b):
    """Loose containment match, tolerant of subtitle/punctuation differences."""
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    short, long_ = sorted((na, nb), key=len)
    return short[:60] in long_ or long_[:60] in short


def surnames(item):
    return [a.get("family", "") for a in item.get("author", []) if a.get("family")]


TYPE_EXPECT = {
    "proceedings-article": "inproceedings",
    "journal-article": "article",
    "book-chapter": "incollection",
    "posted-content": "misc",
}


def audit_entry(e):
    f = e["fields"]
    title = f.get("title", "")
    rec = {"key": e["key"], "bib_type": e["type"], "title": title, "issues": []}
    if not title:
        rec["issues"].append("no title field; cannot verify")
        return rec

    try:
        items = crossref(title)
    except Exception as exc:
        rec["issues"].append(f"lookup failed: {type(exc).__name__}: {exc}")
        return rec

    hit = next((it for it in items
                if title_match(title, (it.get("title") or [""])[0])), None)
    if hit is None:
        rec["issues"].append("NO CROSSREF MATCH for this title - verify the entry "
                             "exists as recorded")
        rec["candidates"] = [(it.get("title") or [""])[0][:80] for it in items[:2]]
        return rec

    rec["doi"] = hit.get("DOI")
    rec["crossref_title"] = (hit.get("title") or [""])[0]

    # --- year ---
    parts = (hit.get("issued", {}).get("date-parts") or [[None]])[0]
    cr_year = parts[0] if parts else None
    bib_year = f.get("year", "").strip()
    rec["crossref_year"], rec["bib_year"] = cr_year, bib_year
    if cr_year and bib_year and str(cr_year) != bib_year:
        rec["issues"].append(f"YEAR: bib={bib_year} crossref={cr_year}")

    # --- venue ---
    cr_venue = (hit.get("container-title") or [""])[0]
    bib_venue = f.get("journal") or f.get("booktitle") or ""
    rec["crossref_venue"], rec["bib_venue"] = cr_venue, bib_venue
    if cr_venue and bib_venue and not title_match(cr_venue, bib_venue):
        rec["issues"].append(f"VENUE: bib='{bib_venue}' crossref='{cr_venue}'")

    # --- authors ---
    cr_auth = surnames(hit)
    bib_auth = [p.strip().split(",")[0].split()[-1]
                for p in re.split(r"\s+and\s+", f.get("author", "")) if p.strip()]
    rec["crossref_authors"], rec["bib_authors"] = cr_auth, bib_auth
    if cr_auth and bib_auth:
        missing = [a for a in cr_auth
                   if not any(norm(a) == norm(b) for b in bib_auth)]
        extra = [b for b in bib_auth
                 if not any(norm(a) == norm(b) for a in cr_auth)]
        if missing or extra:
            rec["issues"].append(
                f"AUTHORS: bib-only={extra or '-'} crossref-only={missing or '-'}")

    # --- entry type ---
    expect = TYPE_EXPECT.get(hit.get("type"))
    if expect and expect != e["type"]:
        # AAAI/IEEE proceedings are frequently deposited as journal-article; only
        # flag the clear-cut direction to avoid noise.
        if not (expect == "article" and e["type"] == "inproceedings"):
            rec["issues"].append(
                f"TYPE: bib=@{e['type']} crossref={hit.get('type')} "
                f"(expected @{expect})")

    # --- DOI present in bib? ---
    if not f.get("doi"):
        rec["issues"].append(f"NO DOI in bib; crossref has {hit.get('DOI')}")
    elif hit.get("DOI") and norm(f["doi"]) != norm(hit["DOI"]):
        rec["issues"].append(f"DOI: bib={f['doi']} crossref={hit.get('DOI')}")

    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write full findings to this path")
    ap.add_argument("--bib", default=BIB)
    args = ap.parse_args()

    entries = parse_bib(args.bib)
    print(f"Auditing {len(entries)} entries in {os.path.relpath(args.bib, BASE_DIR)} "
          f"against Crossref\n" + "=" * 78)

    results, clean = [], 0
    for i, e in enumerate(entries, 1):
        if e["type"] == "unpublished":
            print(f"[{i:2d}] {e['key']:24s} SKIPPED (unpublished; nothing to verify)")
            continue
        rec = audit_entry(e)
        results.append(rec)
        if rec["issues"]:
            print(f"[{i:2d}] {e['key']:24s} {len(rec['issues'])} issue(s)")
            for msg in rec["issues"]:
                print(f"       - {msg}")
        else:
            clean += 1
            print(f"[{i:2d}] {e['key']:24s} ok")
        time.sleep(0.4)      # be polite to the API

    print("=" * 78)
    flagged = len(results) - clean
    print(f"{clean} clean, {flagged} flagged, of {len(results)} verifiable entries")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"-> {args.json}")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
