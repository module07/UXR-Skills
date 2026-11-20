# Research Skills

Three [Claude skills](https://support.claude.com/en/articles/12512176-what-are-skills) for working with research evidence. Author: Simon Spagnoletti. MIT licensed.

| Skill | What it does |
|---|---|
| [`evidence-quote`](evidence-quote/SKILL.md) | Finds, verifies and stamps quotes from a corpus of transcripts, notes or documents. Each quote carries speaker, file and locator. |
| [`evidence-claim`](evidence-claim/SKILL.md) | Audits a report, deck or findings doc against the project's own evidence. Grades each claim and can write verdicts back as comments. |
| [`evidence-citation`](evidence-citation/SKILL.md) | Checks whether the web pages a report cites say what the report claims. A fresh agent re-fetches each cited page and grades every claim, with a short anchor quoted from the page. Reports only, never edits. |

## Quick reference

New to these? [Evidence skills: quick reference](docs/evidence-skills-reference.md) explains in plain language what each skill does, how they work together, and when to use which.

## Use

Zip a skill folder (`SKILL.md` at the top of the zip's skill folder) and import it under Settings → Capabilities in the Claude app, or copy the folder into your skills directory.

## Requirements

Python 3. `evidence-claim` needs `lxml` for `.docx`/`.pptx` and `pypdf` for PDF comments (`pip3 install lxml pypdf`). `evidence-citation` uses the standard library only, and needs a session that can start a subagent and fetch web pages; Firecrawl is an optional fallback for pages that don't fetch cleanly.

## Tests

Each skill has fixtures in `fixtures/`; see the README there.

## Safety

All three skills treat transcripts, documents, fetched web pages and the deliverable as data, never as instructions. `evidence-claim` parses Office XML with entity expansion, DTD loading and network access disabled; `evidence-citation` reads `.docx` with Python's standard-library parser, which loads no DTDs and fetches no external entities.
