#!/usr/bin/env python3
"""Export .recall and .quiz blocks to a TSV file for Anki import.

Runs as a post-render step (see _quarto.yml) and writes straight into _site/,
so the deck downloadable from the review page is always current.

Format: tab-separated (Anki does not trip over commas inside formulas that
way), three columns — front, back, tags.

Import in Anki: File -> Import, note type Basic, separator Tab, map field 3
to Tags, enable "Allow HTML in fields".
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recall_parser import ROOT, Card, collect  # noqa: E402

OUT_DIR = ROOT / "_site"
OUT = OUT_DIR / "anki-cards.tsv"

# Anki expects LaTeX in its own delimiters, not Quarto's dollars.
_DISPLAY = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
_INLINE = re.compile(r"(?<!\$)\$([^$\n]+?)\$(?!\$)")
# A term shortcode is meaningless on a card — keep only the readable label.
_TERM = re.compile(r"\{\{<\s*term\s+([\w-]+)(?:\s+\"([^\"]*)\")?\s*>\}\}")
# Markdown links: keep the text, drop the target.
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
# Inline emphasis. Anki fields are HTML, so markdown markers would show up raw.
_BOLD = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_ITALIC = re.compile(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])")
_CODE = re.compile(r"`([^`\n]+?)`")

# Glossary labels, so {{< term selection-bias >}} becomes "selection bias"
# rather than the raw key. Parsed with a regex instead of PyYAML because this
# script runs as a post-render hook under whichever python3 is on PATH.
_GLOSS_KEY = re.compile(r"^  ([\w-]+):\s*$")
_GLOSS_TERM = re.compile(r"^    term:\s*\"?(.+?)\"?\s*$")


def _glossary_labels() -> dict[str, str]:
    path = ROOT / "_glossary.yml"
    if not path.exists():
        return {}
    labels: dict[str, str] = {}
    key = None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _GLOSS_KEY.match(line)
        if m:
            key = m.group(1)
            continue
        if key:
            m = _GLOSS_TERM.match(line)
            if m:
                labels[key] = m.group(1)
                key = None
    return labels


LABELS = _glossary_labels()


def to_anki(md: str) -> str:
    """Convert card markdown into something Anki renders correctly."""
    md = _TERM.sub(
        lambda m: m.group(2) or LABELS.get(m.group(1), m.group(1).replace("-", " ")),
        md,
    )
    md = _LINK.sub(lambda m: m.group(1), md)
    md = _DISPLAY.sub(lambda m: r"\[" + m.group(1).strip() + r"\]", md)
    md = _INLINE.sub(lambda m: r"\(" + m.group(1).strip() + r"\)", md)
    md = _CODE.sub(lambda m: f"<code>{m.group(1)}</code>", md)
    md = _BOLD.sub(lambda m: f"<b>{m.group(1)}</b>", md)
    md = _ITALIC.sub(lambda m: f"<i>{m.group(1)}</i>", md)
    # Newlines become <br>, because an Anki field is a single line.
    return md.replace("\t", " ").replace("\n", "<br>").strip()


def slug(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_]+", "-", s).strip("-")


def front_back(card: Card) -> tuple[str, str] | None:
    """Build the front and back of a card.

    A .quiz is already question-and-answer. A .recall is a statement, so the
    nearest heading becomes the prompt: the goal is to recall the content of
    a section, not to recognize a phrasing.
    """
    if card.kind == "quiz":
        return to_anki(card.question), to_anki(card.body)

    if not card.body:
        return None

    prompt = card.heading or card.chapter
    return f"{card.chapter} — {prompt}: what should you remember?", to_anki(card.body)


def main() -> int:
    cards = collect()
    if not cards:
        print("export_anki: no cards found — skipping")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows, skipped = [], 0

    for card in cards:
        pair = front_back(card)
        if pair is None:
            skipped += 1
            continue
        front, back = pair
        tags = " ".join(["causal-inference", slug(card.chapter), card.kind])
        rows.append([front, back, tags])

    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        writer.writerows(rows)

    note = f" (skipped {skipped} empty)" if skipped else ""
    print(f"export_anki: {len(rows)} cards -> {OUT.relative_to(ROOT)}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
