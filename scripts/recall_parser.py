"""Extract .recall and .quiz cards from chapter sources.

One implementation serving two consumers: the rendered review page
(recall.qmd) and the post-render Anki export (scripts/export_anki.py). It
therefore lives on its own and knows nothing about Quarto or Anki.

Parsing runs against the `.qmd` source rather than the rendered HTML: a card
must exist before the render, otherwise the review page would depend on build
order.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Opening fence of a fenced div: ::: {.recall} or :::: {.quiz question="..."}
_OPEN = re.compile(r"^(?P<colons>:{3,})\s*\{(?P<attrs>[^}]*)\}\s*$")
# Closing fence: colons only.
_CLOSE = re.compile(r"^:{3,}\s*$")
# A class inside the attribute list: .recall
_CLASS = re.compile(r"\.([A-Za-z][\w-]*)")
# An attribute of the form key="value"
_ATTR = re.compile(r'([\w-]+)\s*=\s*"([^"]*)"')
# Chapter title from the YAML front matter.
_TITLE = re.compile(r"^title:\s*[\"']?(.+?)[\"']?\s*$", re.MULTILINE)
# A code fence: ``` or ```{python}. Heading detection must ignore anything
# inside one, or a `# comment` in a Python cell reads as a markdown heading.
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


@dataclass
class Card:
    kind: str  # "recall" | "quiz"
    source: str  # path relative to the repo root
    chapter: str  # chapter title
    anchor: str  # anchor on the rendered page
    question: str  # quiz question; empty for recall
    body: str  # block content, markdown
    heading: str = ""  # nearest heading above the block
    attrs: dict[str, str] = field(default_factory=dict)


def _chapter_title(text: str, path: Path) -> str:
    m = _TITLE.search(text)
    return m.group(1).strip() if m else path.stem


def parse_file(path: Path) -> list[Card]:
    """Pull every card out of a single .qmd."""
    text = path.read_text(encoding="utf-8")
    chapter = _chapter_title(text, path)
    rel = path.relative_to(ROOT).as_posix()

    cards: list[Card] = []
    lines = text.splitlines()

    # This counter must match the numbering in playbook.lua, or links from the
    # review page will point at the wrong block.
    recall_n = 0
    heading = ""
    in_code = False
    i = 0

    while i < len(lines):
        line = lines[i]

        if _FENCE.match(line):
            in_code = not in_code
            i += 1
            continue

        if not in_code and line.startswith("#") and not line.startswith("#!"):
            heading = line.lstrip("#").strip()
            # Drop a trailing {#sec-id} attribute from the heading text.
            heading = re.sub(r"\s*\{[^}]*\}\s*$", "", heading)
            # Drop an inline step badge like [1]{.chapter-step}.
            heading = re.sub(r"^\[\d+\]\{[^}]*\}\s*", "", heading)

        m = _OPEN.match(line)
        if not m:
            i += 1
            continue

        attrs_raw = m.group("attrs")
        classes = _CLASS.findall(attrs_raw)
        kind = next((c for c in classes if c in ("recall", "quiz")), None)

        if kind is None:
            i += 1
            continue

        # Collect the body up to the matching close fence, tracking nesting.
        depth = 1
        body: list[str] = []
        j = i + 1
        while j < len(lines) and depth > 0:
            if _OPEN.match(lines[j]):
                depth += 1
            elif _CLOSE.match(lines[j]):
                depth -= 1
                if depth == 0:
                    break
            body.append(lines[j])
            j += 1

        attrs = dict(_ATTR.findall(attrs_raw))

        if kind == "recall":
            recall_n += 1
            anchor = attrs.get("id", f"recall-{recall_n}")
        else:
            anchor = attrs.get("id", "")

        cards.append(
            Card(
                kind=kind,
                source=rel,
                chapter=chapter,
                anchor=anchor,
                question=attrs.get("question", ""),
                body="\n".join(body).strip(),
                heading=heading,
                attrs=attrs,
            )
        )
        i = j + 1

    return cards


def collect(dirs: tuple[str, ...] = ("notes", "explorables", "labs")) -> list[Card]:
    """Every card in the project, in chapter order."""
    cards: list[Card] = []
    for d in dirs:
        base = ROOT / d
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.qmd")):
            if path.name.startswith("_"):
                continue
            cards.extend(parse_file(path))
    return cards


def page_link(card: Card) -> str:
    """Link back to where the card lives on the site."""
    page = card.source.rsplit(".", 1)[0] + ".html"
    return f"/{page}#{card.anchor}" if card.anchor else f"/{page}"
