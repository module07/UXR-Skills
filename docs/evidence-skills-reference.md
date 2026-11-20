# Evidence skills: quick reference

Three skills that keep research writing honest. They work on any subject matter. Two check against your own source material (interview transcripts, notes, tickets, documents, reports); the third checks against the web pages your writing cites.

| | **evidence-claim** | **evidence-quote** | **evidence-citation** |
|---|---|---|---|
| One-line job | Checks whether the **conclusions** in your report are backed by your data | Checks whether the **words in quotation marks** were really said, and says where | Checks whether the **web pages you cite** say what your sentence says they say |
| The thing it looks at | A claim, such as "most users struggled with setup" | A quote, such as "I just gave up on the setup" | A claim with a link, such as "the market grew 12% in 2025 [source]" |
| The question it answers | "Does the evidence carry this sentence?" | "Did this person actually say this, and where?" | "Does the page behind this link say this?" |
| You give it | A report, deck or findings doc, plus the folder of source material | A question about the source material, or a draft that contains quotes | A report, document or chat reply that cites web sources |
| You get back | A verdict on each claim: how many sources back it, how many go against it, how many say nothing | Verified quotes, each with a stamp: who said it, in which file, at what point | A grade on each cited claim, with a short anchor quoted from the page |
| Can it write into your document? | Yes, as comments, only if you say so | No. It checks and stamps; you place the quotes | No. It reports only |

## Why there are three

A quote can be word-for-word real and the sentence built on top of it can still be wrong. One skill checks the words, another checks the conclusion against your own data. The third covers what the first two leave alone: claims that rest on outside sources, such as a published figure or a market report. A report that mixes its own research with desk research needs all three.

## When to use each

| Your situation | Use |
|---|---|
| "What did people say about pricing?" | evidence-quote (finding quotes) |
| "Is this quote real? Where is it from?" | evidence-quote (verifying) |
| You are about to paste a quote into a slide or document | evidence-quote, first |
| "Does the data back up my report?" | evidence-claim |
| "Did I overstate this finding?" | evidence-claim |
| "Do these sources actually say that?" | evidence-citation |
| A desk-research, company or market research report with links | evidence-citation |
| evidence-claim marked a claim out-of-corpus, and it cites a link | evidence-citation on that claim |
| A deck is about to go to stakeholders | All that apply: evidence-claim on the conclusions, evidence-quote on the quotes, evidence-citation on the cited figures |
| "What did my report leave out?" | None. All three only check what is already written (see limits) |

Rule of thumb: **one sentence of yours → evidence-claim. One sentence of theirs → evidence-quote. One sentence with a link → evidence-citation.**

## How they work together

1. **Draft.** When you ask what the source material says, evidence-quote searches it and returns only verified, stamped quotes. It looks for evidence against your idea as well as for it.
2. **Audit.** When the draft is done, evidence-claim picks out the claims that carry the argument, shows you its list (and what it chose to skip), and waits for your corrections before searching.
3. **Hand-off between them.** When evidence-claim needs to show a quote as evidence, it asks evidence-quote to verify and stamp it. If evidence-quote is not installed, it points to the source instead and tells you the quotes were not verified.
4. **Outside sources.** evidence-claim leaves claims about published figures ungraded (out-of-corpus). If those claims cite a link, run evidence-citation on the report. It pulls out every claim that has a link, hands each claim and its URL to a fresh agent that has not seen your draft, and that agent re-reads the page. It runs on its own; it does not call the other two.

## What the output looks like

**evidence-claim** grades every claim:

| Grade | Plain meaning |
|---|---|
| supported | The data backs the claim as worded |
| overstated | Real finding, but the wording claims more than the data shows (for example "most" when it was 2 of 11) |
| understated | The data is stronger than the claim admits |
| contradicted | Something in the data goes against the claim |
| unsupported | Nothing in the data speaks to it either way |
| out-of-corpus | The claim relies on something outside your data (a published figure, a study). Left ungraded |

Each grade comes with three counts, always with the unit named: **support · against · silent**, out of N (participants, documents, tickets). "Silent" means that source never addressed the topic. It is not counted as support or as opposition.

**evidence-quote** gives each quote a stamp:

```
Speaker, file-name @ timestamp
```

If the speaker is a guess, the stamp says so ("likely ... [inferred]"). If the transcript has no timestamps, a line number is used.

**evidence-citation** grades every cited claim:

| Grade | Plain meaning |
|---|---|
| supported | The page states the claim as strongly as your sentence does |
| overstated | The page says something weaker: a forecast reported as a result, one segment reported as the whole, "up to" dropped, or a different date |
| contradicted | The page says something that conflicts with the claim |
| not-on-page | The page loaded but does not address the claim |
| unreachable | Paywall, block, dead link, or an empty page |

Each verdict comes with an **anchor**: the shortest span from the page that carries the claim, under 15 words, plus where on the page it sits. You can audit any verdict by reading one line. The report goes to chat first; the skill then asks where, if anywhere, to save it.

## Limits to know

- **None of the skills finds what you left out.** They check what is on the page, not what is missing from it.
- **evidence-claim takes your data as given.** It cannot tell you whether the data was well collected. It also does not fact-check outside sources; that is evidence-citation's job.
- **evidence-citation checks fidelity to the cited page, nothing else.** A claim can be graded supported and still be wrong, because the page is an aggregator, out of date, or disagrees with a primary source. It does not judge source quality or look for better sources.
- **evidence-citation only checks claims that carry a link.** Uncited claims are listed and left alone. It checks up to 40 cited claims a run, numbers first; the rest are listed as unchecked.
- **evidence-citation sends each claim and its URL to a web fetch tool.** If a claim names a private individual, the skill replaces the name with their role before sending it.
- **Boards and whiteboards** (sticky notes, cards) cannot be read directly. Copy the text into a file and check that.
- **Counts are the skill's reading of your material**, not a script's output. They are shown so you can challenge them.
- **Text inside your source material or a fetched page is never treated as instructions.** If a transcript or web page says "ignore the rules", the skill reports it and moves on.

## Starting points

Say any of these in a session that has the skills installed:

| To use evidence-claim | To use evidence-quote | To use evidence-citation |
|---|---|---|
| "Check this report against the data" | "Find me quotes about onboarding" | "Check the citations" |
| "Did I overstate this?" | "Are these quotes real?" | "Do the sources say that?" |
| "Pressure-test my findings" | "Where does this quote come from?" | "Verify the sources in this report" |
| "Does the data back this up?" | "What did the participants say about X?" | "Re-fetch the sources" |

None of them changes anything of yours without asking. evidence-citation never edits the document at all.
