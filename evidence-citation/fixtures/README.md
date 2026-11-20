# Fixtures

`test_evidence_citation.py` runs as a plain script, the way `package.sh` runs
it: `python3 fixtures/test_evidence_citation.py`. Standard library only, and
every input is synthetic and built in a temp folder.

It covers the two scripts:

- `extract_citations.py`: inline links, bare URLs, footnote markers, numeric
  markers through a reference list, `Source:` lines, tables, code fences,
  abbreviations, the cap, uncited numeric sentences, unresolved markers, and
  `.docx` hyperlinks, footnotes and headings.
- `check_results.py`: the anchor rules, anchor verification against a saved
  page, missing results, unknown grades, the report table and the tally line.

It does not test the verifier agent's grading. That needs a model run against
claims with known-good and known-bad citations, which belongs under
`fixtures/evals/` and has not been written.
