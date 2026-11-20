#!/usr/bin/env python3
"""Extract (claim, cited URL) pairs from a markdown, text or .docx deliverable.

Usage:
    python3 extract_citations.py <file> [--cap 40] > pairs.json

Output is a candidate list for the model to review, never a final inventory.
Standard library only.

JSON shape:
    {
      "source_file": str,
      "pairs":      [{"id", "claim", "url", "locator", "has_number"}],
      "over_cap":   [same shape, pairs beyond --cap, not to be checked this run],
      "uncited":    [{"claim", "locator"}],   # numeric sentences with no citation
      "unresolved_markers": [{"marker", "locator"}]
    }
"""
import argparse
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

URL_RE = re.compile(r"https?://[^\s<>\]\)\"']+")
MD_LINK_RE = re.compile(r"\[([^\]\[]+)\]\((https?://[^\s)]+)[^)]*\)")
FOOT_MARK_RE = re.compile(r"\[\^([\w-]+)\]")
NUM_MARK_RE = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]")
DEF_RE = re.compile(r"^\s*\[\^?([\w-]+)\]:\s*(.+)$")
REF_HEAD_RE = re.compile(
    r"^\s*(?:#+\s*)?\**(references|sources|bibliography|works cited|endnotes|notes|citations)\**\s*:?\s*$",
    re.I,
)
REF_LINE_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\[(\d+)\]|(\d+)[.)])\s+(.+)$")
HEADING_RE = re.compile(r"^\s*(#{1,6})\s+(.*)$")
LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
ABBREV = {
    "e.g", "i.e", "etc", "vs", "inc", "ltd", "co", "corp", "mr", "mrs", "ms",
    "dr", "st", "no", "fig", "approx", "est", "u.s", "u.k", "jr", "sr",
}
PH = "\x00"


def _clean_url(u):
    return u.rstrip(".,;:!?*_")


def _first_url(text):
    m = MD_LINK_RE.search(text)
    if m:
        return _clean_url(m.group(2))
    m = URL_RE.search(text)
    return _clean_url(m.group(0)) if m else None


# ---------------------------------------------------------------- docx

def _rels(z, path):
    out = {}
    try:
        root = ET.fromstring(z.read(path))
    except KeyError:
        return out
    for rel in root.iter(REL + "Relationship"):
        out[rel.get("Id")] = rel.get("Target")
    return out


def _para_text(p, rels):
    parts = []
    for child in p:
        if child.tag == W + "hyperlink":
            text = "".join(t.text or "" for t in child.iter(W + "t"))
            target = rels.get(child.get(R + "id"), "")
            if target.startswith("http") and text.strip():
                parts.append("[%s](%s)" % (text.strip(), target))
            else:
                parts.append(text)
        elif child.tag == W + "r":
            for node in child:
                if node.tag == W + "t":
                    parts.append(node.text or "")
                elif node.tag == W + "tab":
                    parts.append(" ")
                elif node.tag == W + "footnoteReference":
                    parts.append("[^fn%s]" % node.get(W + "id"))
                elif node.tag == W + "endnoteReference":
                    parts.append("[^en%s]" % node.get(W + "id"))
    return "".join(parts)


def docx_to_markdown(path):
    """Flatten a .docx into markdown-like text that the parser below reads."""
    lines = []
    with zipfile.ZipFile(path) as z:
        rels = _rels(z, "word/_rels/document.xml.rels")
        root = ET.fromstring(z.read("word/document.xml"))
        for p in root.iter(W + "p"):
            text = _para_text(p, rels).strip()
            if not text:
                continue
            style = p.find("%spPr/%spStyle" % (W, W))
            sval = (style.get(W + "val") if style is not None else "") or ""
            if sval.lower().startswith("heading") or sval.lower() == "title":
                text = "# " + text
            lines.append(text)
            lines.append("")
        for part, prefix, tag in (
            ("footnotes", "fn", "footnote"),
            ("endnotes", "en", "endnote"),
        ):
            name = "word/%s.xml" % part
            if name not in z.namelist():
                continue
            nrels = _rels(z, "word/_rels/%s.xml.rels" % part)
            nroot = ET.fromstring(z.read(name))
            for note in nroot.iter(W + tag):
                nid = note.get(W + "id")
                text = " ".join(
                    _para_text(p, nrels).strip() for p in note.iter(W + "p")
                ).strip()
                if text:
                    lines.append("[^%s%s]: %s" % (prefix, nid, text))
    return "\n".join(lines)


# ---------------------------------------------------------------- parsing

def _expand_numeric(label):
    out = []
    for piece in re.split(r"\s*,\s*", label):
        m = re.match(r"^(\d+)\s*[–-]\s*(\d+)$", piece)
        if m and int(m.group(2)) - int(m.group(1)) < 20:
            out.extend(str(n) for n in range(int(m.group(1)), int(m.group(2)) + 1))
        else:
            out.append(piece.strip())
    return out


def _split_sentences(text):
    """Split on sentence ends, leaving abbreviations and decimals alone."""
    out, start = [], 0
    # A citation marker sitting right after the full stop stays with its sentence.
    for m in re.finditer(r"[.!?](?:[\"')\]]|" + PH + r"\d+" + PH + r")*\s+", text):
        before = text[start:m.start()]
        last = before.split()[-1].lower() if before.split() else ""
        last = last.strip("(\"'")
        if last in ABBREV or re.fullmatch(r"[a-z]", last):
            continue
        out.append(text[start:m.end()].strip())
        start = m.end()
    tail = text[start:].strip()
    if tail:
        out.append(tail)
    return out


def parse(text):
    lines = text.splitlines()
    defs, body = {}, []  # body: (line_no, heading, kind, text)
    heading, in_refs, in_code = "", False, False
    para, para_line = [], 0

    def flush():
        nonlocal para
        if para:
            body.append((para_line, heading, "para", " ".join(para)))
            para = []

    for i, raw in enumerate(lines, 1):
        line = raw.rstrip()
        if line.strip().startswith("```"):
            flush()
            in_code = not in_code
            continue
        if in_code:
            continue
        m = DEF_RE.match(line)
        if m:
            flush()
            url = _first_url(m.group(2))
            if url:
                defs[m.group(1)] = url
            continue
        if REF_HEAD_RE.match(line):
            flush()
            in_refs = True
            continue
        h = HEADING_RE.match(line)
        if h:
            flush()
            heading = h.group(2).strip()
            in_refs = False
            continue
        if in_refs:
            r = REF_LINE_RE.match(line)
            if r:
                url = _first_url(r.group(3))
                if url:
                    defs[r.group(1) or r.group(2)] = url
            continue
        if not line.strip():
            flush()
            continue
        if line.lstrip().startswith("|"):
            flush()
            if not re.fullmatch(r"[\s|:\-]+", line):
                body.append((i, heading, "row", line.strip().strip("|").strip()))
            continue
        if LIST_RE.match(line):
            flush()
            body.append((i, heading, "para", LIST_RE.sub("", line, 1).strip()))
            continue
        if not para:
            para_line = i
        para.append(line.strip())
    flush()

    pairs, uncited, unresolved = [], [], []
    seen = set()
    last_sentence_pairs = None  # (claim, locator) of the previous sentence

    for line_no, head, kind, block in body:
        tokens = []

        def stash(kind_, payload):
            tokens.append((kind_, payload))
            return "%s%d%s" % (PH, len(tokens) - 1, PH)

        work = MD_LINK_RE.sub(
            lambda m: stash("link", (m.group(1), _clean_url(m.group(2)))), block
        )
        work = URL_RE.sub(lambda m: stash("link", ("", _clean_url(m.group(0)))), work)
        work = FOOT_MARK_RE.sub(lambda m: stash("mark", [m.group(1)]), work)
        work = NUM_MARK_RE.sub(lambda m: stash("mark", _expand_numeric(m.group(1))), work)
        work = work.replace("<", " ").replace(">", " ")

        sentences = [work] if kind == "row" else _split_sentences(work)
        merged = []
        for s in sentences:
            bare = re.sub(PH + r"\d+" + PH, "", s)
            if merged and not re.search(r"[A-Za-z]{2,}", bare):
                merged[-1] += " " + s
            else:
                merged.append(s)

        locator = "line %d" % line_no + (", under \"%s\"" % head if head else "")
        for s in merged:
            urls = []
            for idx in re.findall(PH + r"(\d+)" + PH, s):
                kind_, payload = tokens[int(idx)]
                if kind_ == "link":
                    urls.append(payload[1])
                else:
                    for label in payload:
                        if label in defs:
                            urls.append(defs[label])
                        else:
                            unresolved.append({"marker": label, "locator": locator})

            def render(m):
                kind_, payload = tokens[int(m.group(1))]
                return payload[0] if kind_ == "link" else ""

            claim = re.sub(PH + r"(\d+)" + PH, render, s)
            claim = re.sub(r"[*_`]+", "", claim)
            claim = re.sub(r"\(\s*\)", "", claim)
            claim = re.sub(r"\s+", " ", claim).strip(" -:;")
            words = len(re.findall(r"[A-Za-z0-9%$]+", claim))
            # What is left once link text is dropped: "Source: [Post](url)" -> "Source:"
            bare = re.sub(r"[*_`]+", "", re.sub(PH + r"\d+" + PH, "", s)).strip()
            label_only = re.fullmatch(r"(?i)(sources?|see|via|ref(erence)?s?)\W*", bare or "x")

            if urls and (words < 3 or label_only) and last_sentence_pairs:
                claim, locator_use = last_sentence_pairs
            else:
                locator_use = locator
                if words >= 3:
                    last_sentence_pairs = (claim, locator)
            if words < 3 and not urls:
                continue
            has_number = bool(re.search(r"\d", claim))
            if urls:
                for u in dict.fromkeys(urls):
                    key = (claim, u)
                    if key in seen:
                        continue
                    seen.add(key)
                    pairs.append({
                        "claim": claim, "url": u,
                        "locator": locator_use, "has_number": has_number,
                    })
            elif has_number and words >= 4:
                uncited.append({"claim": claim, "locator": locator})
    return pairs, uncited, unresolved


def extract(path, cap=40):
    if path.lower().endswith(".docx"):
        text = docx_to_markdown(path)
    else:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    pairs, uncited, unresolved = parse(text)
    ordered = sorted(
        enumerate(pairs), key=lambda t: (0 if t[1]["has_number"] else 1, t[0])
    )
    ordered = [p for _, p in ordered]
    for n, p in enumerate(ordered, 1):
        p["id"] = "c%03d" % n
    return {
        "source_file": path,
        "pairs": ordered[:cap],
        "over_cap": ordered[cap:],
        "uncited": uncited,
        "unresolved_markers": unresolved,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file")
    ap.add_argument("--cap", type=int, default=40)
    args = ap.parse_args(argv)
    json.dump(extract(args.file, args.cap), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
