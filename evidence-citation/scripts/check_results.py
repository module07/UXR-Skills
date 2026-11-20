#!/usr/bin/env python3
"""Validate verifier results against the pair list, then print the report
table and the one-line run tally.

Usage:
    python3 check_results.py pairs.json results.json --target "<name>" \
        --mode independent|self-checked [--pages DIR] [--date YYYY-MM-DD]

results.json is a list of:
    {"id", "grade", "anchor", "locator", "source_as_of", "note", "fetched_with"}

Rules enforced:
  - every pair id has exactly one result, and no result has an unknown id
  - grade is one of GRADES
  - supported, overstated and contradicted need an anchor and a locator
  - an anchor is under 15 words
  - with --pages, an anchor must appear in DIR/<id>.md or DIR/<id>.txt when
    that file exists; a "supported" grade whose anchor is absent is an error

Exit 0 when clean, 1 when any rule fails. Standard library only.
"""
import argparse
import datetime
import json
import os
import re
import sys

GRADES = ["supported", "overstated", "contradicted", "not-on-page", "unreachable"]
NEEDS_ANCHOR = {"supported", "overstated", "contradicted"}
MAX_ANCHOR_WORDS = 14


def _norm(s):
    s = s.lower().replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = re.sub(r"[*_`#|>\[\]]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _page_text(pages, cid):
    if not pages:
        return None
    for ext in (".md", ".txt"):
        p = os.path.join(pages, cid + ext)
        if os.path.exists(p):
            with open(p, encoding="utf-8", errors="replace") as fh:
                return fh.read()
    return None


def check(pairs_doc, results, pages=None):
    """Return (rows, errors). rows are result dicts with anchor_check added."""
    pairs = {p["id"]: p for p in pairs_doc["pairs"]}
    errors, rows, seen = [], [], set()
    for r in results:
        cid = r.get("id")
        if cid not in pairs:
            errors.append("%s: result for an id that is not in the pair list" % cid)
            continue
        if cid in seen:
            errors.append("%s: more than one result" % cid)
            continue
        seen.add(cid)
        grade = r.get("grade")
        anchor = (r.get("anchor") or "").strip()
        if grade not in GRADES:
            errors.append("%s: unknown grade %r" % (cid, grade))
        if grade in NEEDS_ANCHOR:
            if not anchor:
                errors.append("%s: %s with no anchor from the page" % (cid, grade))
            if not (r.get("locator") or "").strip():
                errors.append("%s: %s with no locator" % (cid, grade))
        if anchor and len(anchor.split()) > MAX_ANCHOR_WORDS:
            errors.append(
                "%s: anchor is %d words, limit %d"
                % (cid, len(anchor.split()), MAX_ANCHOR_WORDS)
            )
        status = "none"
        if anchor:
            page = _page_text(pages, cid)
            if page is None:
                status = "relayed"
            elif _norm(anchor) in _norm(page):
                status = "verified"
            else:
                status = "ABSENT"
                if grade == "supported":
                    errors.append("%s: supported, but the anchor is not in the saved page" % cid)
        row = dict(r)
        row["anchor_check"] = status
        row["claim"] = pairs[cid]["claim"]
        row["url"] = pairs[cid]["url"]
        rows.append(row)
    for cid in pairs:
        if cid not in seen:
            errors.append("%s: no result returned" % cid)
    rows.sort(key=lambda r: (GRADES.index(r["grade"]) if r.get("grade") in GRADES else 9, r["id"]))
    return rows, errors


def tally_line(pairs_doc, rows, target, mode, date):
    counts = {g: 0 for g in GRADES}
    for r in rows:
        if r.get("grade") in counts:
            counts[r["grade"]] += 1
    parts = [date, target, "checked %d" % len(rows)]
    parts += ["%s %d" % (g, counts[g]) for g in GRADES]
    parts += [
        "uncited %d" % len(pairs_doc.get("uncited", [])),
        "unchecked %d" % len(pairs_doc.get("over_cap", [])),
        mode,
    ]
    return " | ".join(parts)


def _cell(s, limit=110):
    s = re.sub(r"\s+", " ", str(s or "")).replace("|", "/")
    return s if len(s) <= limit else s[: limit - 1] + "…"


def report(rows):
    out = ["| ID | Grade | Claim | What the page shows | Where | Source as of | Anchor check |",
           "|---|---|---|---|---|---|---|"]
    for r in rows:
        shown = r.get("anchor") or r.get("note") or ""
        if r.get("anchor") and r.get("note"):
            shown = '"%s". %s' % (r["anchor"], r["note"])
        elif r.get("anchor"):
            shown = '"%s"' % r["anchor"]
        out.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            r["id"], r.get("grade"), _cell(r["claim"]), _cell(shown, 160),
            _cell("%s, %s" % (r.get("locator") or "no locator", r["url"]), 140),
            _cell(r.get("source_as_of") or "not stated", 30), r["anchor_check"],
        ))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pairs")
    ap.add_argument("results")
    ap.add_argument("--target", required=True)
    ap.add_argument("--mode", required=True, choices=["independent", "self-checked"])
    ap.add_argument("--pages")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    args = ap.parse_args(argv)
    with open(args.pairs, encoding="utf-8") as fh:
        pairs_doc = json.load(fh)
    with open(args.results, encoding="utf-8") as fh:
        results = json.load(fh)
    rows, errors = check(pairs_doc, results, args.pages)
    print(report(rows))
    print()
    print("TALLY: " + tally_line(pairs_doc, rows, args.target, args.mode, args.date))
    if errors:
        print()
        print("ERRORS (fix before reporting):")
        for e in errors:
            print("  - " + e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
