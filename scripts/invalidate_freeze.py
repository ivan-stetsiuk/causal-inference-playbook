#!/usr/bin/env python3
"""Drop freeze caches whose *data* inputs changed.

Quarto computes a document's freeze key from the document source. That is the
right default, and wrong for a page whose cells read a data file: editing
`_glossary.yml` alone leaves `glossary.qmd` byte-identical, so Quarto reuses
the cached output and the site silently ships the old definitions. This was
not hypothetical — it happened, and corrected text simply did not appear.

So the dependency is declared here instead. For each document we record a hash
of the files its cells actually read; when the hash moves, that document's
freeze directory is removed and Quarto re-executes it.

Markers live in `_freeze/.data-deps/` — beside the caches rather than inside
them, so a re-render cannot clean them away — and are committed with
`_freeze/`. That pairing is what keeps CI honest: it checks out a matching
cache and hash, and re-executes nothing.

Runs as a pre-render step (see _quarto.yml). Standard library only: CI
installs no Python packages, by design.
"""

import hashlib
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FREEZE = ROOT / "_freeze"
MARKERS = FREEZE / ".data-deps"

# freeze directory name -> data the document's cells read
DEPENDENCIES = {
    "glossary": ("_glossary.yml",),
    # recall.qmd parses every chapter source, so any chapter edit changes it.
    "recall": ("notes", "explorables", "labs"),
}


def digest(paths: tuple) -> str:
    """Hash the contents of every dependency, directories included.

    Content rather than mtime: a fresh git clone rewrites every mtime, so an
    mtime comparison would invalidate the entire cache on the first CI run.
    """
    h = hashlib.sha256()
    for rel in paths:
        target = ROOT / rel
        files = sorted(target.rglob("*.qmd")) if target.is_dir() else [target]
        for f in files:
            if not f.exists():
                continue
            h.update(f.relative_to(ROOT).as_posix().encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def main() -> None:
    MARKERS.mkdir(parents=True, exist_ok=True)
    invalidated = []

    for doc, deps in DEPENDENCIES.items():
        freeze_dir = FREEZE / doc
        marker = MARKERS / f"{doc}.sha256"
        current = digest(deps)

        if not freeze_dir.exists():
            # Nothing cached: Quarto executes the document regardless, and the
            # marker has to describe what that execution was based on.
            marker.write_text(current + "\n", encoding="utf-8")
            continue

        if marker.exists() and marker.read_text(encoding="utf-8").strip() == current:
            continue

        # Re-executing needs packages CI deliberately does not install. Failing
        # loudly beats publishing a page built from a cache that no longer
        # matches its source data.
        if os.getenv("CI"):
            print(
                f"::error::_freeze/{doc} is stale — {', '.join(deps)} changed but the "
                "cache was not rebuilt. Run 'quarto render' locally and commit _freeze/.",
                file=sys.stderr,
            )
            raise SystemExit(1)

        shutil.rmtree(freeze_dir)
        marker.write_text(current + "\n", encoding="utf-8")
        invalidated.append(doc)
        print(f"invalidate_freeze: {doc} — data changed, re-executing")

    if not invalidated:
        print("invalidate_freeze: every freeze cache matches its data inputs")


if __name__ == "__main__":
    main()
