#!/usr/bin/env python3
"""Fixture for evidence-citation. Runs as a plain script: python3 <this file>.
Synthetic inputs only. Exits non-zero on the first failed check."""
import os
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import check_results  # noqa: E402
import extract_citations  # noqa: E402

passed = 0


def ok(cond, label):
    global passed
    if not cond:
        print("FAIL: " + label)
        sys.exit(1)
    passed += 1


MD = """# Sample report

## Market

Acme raised $40M in 2021 ([Acme blog](https://example.com/acme-round)). The
U.S. market grew 12% last year.[^1] Rivals are well funded [2].

- Headcount reached 300 in March. https://example.org/headcount
- Churn fell to 4.5% in the second half.

| Metric | Value |
|---|---|
| Win rate 25% [3] | high |

The product launched in 2019.

Source: [Launch post](https://example.com/launch)

```
ignored 99% https://example.com/code
```

## References

1. Market study. https://example.net/study
2. [Funding roundup](https://example.net/funding).

[^1]: Industry report, https://example.net/report.
"""


def by_url(pairs):
    return {p["url"]: p for p in pairs}


# ---- markdown extraction
tmp = tempfile.mkdtemp()
md_path = os.path.join(tmp, "report.md")
with open(md_path, "w", encoding="utf-8") as fh:
    fh.write(MD)
doc = extract_citations.extract(md_path)
urls = by_url(doc["pairs"])

ok("https://example.com/acme-round" in urls, "inline markdown link is paired")
ok(urls["https://example.com/acme-round"]["claim"].startswith("Acme raised $40M"),
   "claim text keeps the sentence and drops link markup")
ok("https://example.net/report" in urls, "footnote marker resolves to its definition")
ok("12%" in urls["https://example.net/report"]["claim"], "footnote attaches to its own sentence")
ok("U.S. market" in urls["https://example.net/report"]["claim"], "abbreviation does not split the sentence")
ok("https://example.net/funding" in urls, "numeric marker resolves through the reference list")
ok(urls["https://example.net/funding"]["has_number"] is False, "non-numeric claim is flagged as such")
ok("https://example.org/headcount" in urls, "bare URL in a list item is paired")
ok("https://example.com/launch" in urls, "a Source: line attaches to the sentence before it")
ok("launched in 2019" in urls["https://example.com/launch"]["claim"], "Source: line carries the prior claim")
ok("https://example.com/code" not in urls, "code fences are skipped")
ok(any("4.5%" in u["claim"] for u in doc["uncited"]), "numeric sentence with no citation is listed as uncited")
ok(any(m["marker"] == "3" for m in doc["unresolved_markers"]), "marker with no definition is reported")
ok(doc["pairs"][0]["has_number"], "numeric claims sort first")
ok([p["id"] for p in doc["pairs"]] == ["c%03d" % n for n in range(1, len(doc["pairs"]) + 1)],
   "ids are sequential")

capped = extract_citations.extract(md_path, cap=2)
ok(len(capped["pairs"]) == 2 and len(capped["over_cap"]) == len(doc["pairs"]) - 2,
   "cap moves the remainder to over_cap")

# ---- docx extraction
W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
RNS = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
document = (
    '<w:document %s %s><w:body>'
    '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Findings</w:t></w:r></w:p>'
    '<w:p><w:r><w:t xml:space="preserve">Revenue reached $5M in 2025 </w:t></w:r>'
    '<w:hyperlink r:id="rId7"><w:r><w:t>(annual report)</w:t></w:r></w:hyperlink>'
    '<w:r><w:t>.</w:t></w:r></w:p>'
    '<w:p><w:r><w:t>The team doubled to 80 people.</w:t></w:r>'
    '<w:r><w:footnoteReference w:id="2"/></w:r></w:p>'
    '</w:body></w:document>' % (W, RNS)
)
rels = (
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId7" Target="https://example.com/annual" TargetMode="External"/>'
    '</Relationships>'
)
footnotes = (
    '<w:footnotes %s %s>'
    '<w:footnote w:id="2"><w:p><w:r><w:t>Press release, https://example.com/press</w:t></w:r></w:p></w:footnote>'
    '</w:footnotes>' % (W, RNS)
)
docx_path = os.path.join(tmp, "report.docx")
with zipfile.ZipFile(docx_path, "w") as z:
    z.writestr("word/document.xml", document)
    z.writestr("word/_rels/document.xml.rels", rels)
    z.writestr("word/footnotes.xml", footnotes)
ddoc = extract_citations.extract(docx_path)
durls = by_url(ddoc["pairs"])
ok("https://example.com/annual" in durls, "docx hyperlink is paired")
ok("$5M" in durls["https://example.com/annual"]["claim"], "docx claim text is the sentence")
ok("https://example.com/press" in durls, "docx footnote resolves to its URL")
ok("Findings" in durls["https://example.com/annual"]["locator"], "docx heading becomes the locator")

# ---- result checking
pairs_doc = {
    "pairs": [
        {"id": "c001", "claim": "Revenue reached $5M in 2025", "url": "https://example.com/a"},
        {"id": "c002", "claim": "The team doubled", "url": "https://example.com/b"},
        {"id": "c003", "claim": "Churn fell", "url": "https://example.com/c"},
    ],
    "uncited": [{"claim": "x", "locator": "line 1"}],
    "over_cap": [],
}
pages = os.path.join(tmp, "pages")
os.mkdir(pages)
with open(os.path.join(pages, "c001.md"), "w", encoding="utf-8") as fh:
    fh.write("## Results\nTotal revenue was **$5 million** for fiscal 2025.")
good = [
    {"id": "c001", "grade": "supported", "anchor": "Total revenue was $5 million for fiscal 2025",
     "locator": "Results section", "source_as_of": "FY2025"},
    {"id": "c002", "grade": "not-on-page", "note": "page gives no headcount"},
    {"id": "c003", "grade": "unreachable", "note": "HTTP 403"},
]
rows, errors = check_results.check(pairs_doc, good, pages)
ok(errors == [], "clean results pass")
ok(rows[0]["anchor_check"] == "verified", "anchor is verified against the saved page through markdown noise")
line = check_results.tally_line(pairs_doc, rows, "report.md", "independent", "2026-11-19")
ok(line == "2026-11-19 | report.md | checked 3 | supported 1 | overstated 0 | contradicted 0 | "
           "not-on-page 1 | unreachable 1 | uncited 1 | unchecked 0 | independent", "tally line format")
ok("| c001 | supported |" in check_results.report(rows), "report table has the row")

_, e = check_results.check(pairs_doc, [dict(good[0], anchor="")] + good[1:], pages)
ok(any("no anchor" in x for x in e), "supported without an anchor is an error")
_, e = check_results.check(pairs_doc, [dict(good[0], anchor="Revenue hit $6 million")] + good[1:], pages)
ok(any("not in the saved page" in x for x in e), "supported with an anchor absent from the page is an error")
_, e = check_results.check(pairs_doc, good[:2], pages)
ok(any("c003: no result" in x for x in e), "a missing result is an error")
_, e = check_results.check(pairs_doc, [dict(good[0], anchor=" ".join(["w"] * 15))] + good[1:], None)
ok(any("limit" in x for x in e), "an anchor of 15 words is an error")
_, e = check_results.check(pairs_doc, [dict(good[0], grade="fine")] + good[1:], pages)
ok(any("unknown grade" in x for x in e), "unknown grade is an error")
rows, e = check_results.check(pairs_doc, good, None)
ok(rows[0]["anchor_check"] == "relayed" and e == [], "with no saved page the anchor is marked relayed")

print("evidence-citation fixture: %d checks passed" % passed)
