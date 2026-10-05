"""Content for the generated Doofenshmirtz Evil Inc corpus.

Each module exports ``FAMILIES``: a list of document families. A family has a
name (used in the filename), department, doc_type, classification, optional
status, and versions. A version either lists all of its ``sections`` or is
derived from a ``base`` version with ``purpose`` / ``replace`` / ``add`` /
``remove`` edits. Sections are rendered with sequential numbers, so content
never hard-codes heading numbers.

Section forms:
    ("Title", "body text")
    ("Title", [("Subtitle", "text"), ...])
    ("Title", {"intro": "...", "table": [[header...], [row...]], "after": "..."})
    ("Title", {"intro": "...", "bullets": ["...", ...], "after": "..."})
"""

from scripts.corpus import (
    engineering,
    existing,
    facilities,
    finance,
    legal,
    minions,
    nonpolicy,
    people,
    restricted,
    rnd,
    security,
)

MODULES = (
    existing,
    finance,
    security,
    legal,
    rnd,
    facilities,
    minions,
    people,
    engineering,
    nonpolicy,
    restricted,
)

FAMILIES = [family for module in MODULES for family in module.FAMILIES]
