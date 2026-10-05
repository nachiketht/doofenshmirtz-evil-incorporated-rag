"""The generated 100-document corpus and its manifest."""

import collections
import json
import re
import sys
from pathlib import Path

import pytest

from rag.access import TOP_SECRET
from rag.chunking import export
from rag.manifest import entry_for, load_manifest
from rag.reader import follows_contract, policy_and_version, read

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
FILES = sorted(p for p in DOCS.iterdir() if p.suffix in {".pdf", ".docx", ".md"})
MANIFEST = load_manifest(DOCS)
RESTRICTED = [p for p in FILES if MANIFEST[p.name]["classification"] == TOP_SECRET]
LORE = (
    "inator",
    "platypus",
    "perry",
    "tri-state",
    "gimmelshtump",
    "norm",
    "self-destruct",
    "foosball",
    "monologue",
    "fedora",
    "token",
    "lair",
    "volcano",
    "trap door",
    "goo",
    "ooze",
    "heinz",
    "nemesis",
    "blimp",
    "villain",
    "scheme",
    "minion",
    "cake",
)


def text_of(path):
    loaded = read(path)
    return " ".join([*loaded["title"], *(b["text"] for b in loaded["blocks"])])


def test_one_hundred_contract_named_documents_with_a_complete_manifest():
    assert len(FILES) == 100
    assert all(follows_contract(path) for path in FILES)
    assert set(MANIFEST) == {path.name for path in FILES}
    formats = collections.Counter(path.suffix for path in FILES)
    assert set(formats) == {".pdf", ".docx", ".md"}
    assert min(formats.values()) >= 25


def test_departments_versions_and_document_types():
    departments = {entry["department"] for entry in MANIFEST.values()}
    assert len(departments) >= 15
    families = collections.defaultdict(set)
    for path in FILES:
        policy, version = policy_and_version(path)
        families[policy].add(version)
    assert sum(len(v) >= 3 for v in families.values()) >= 12
    assert sum(len(v) == 2 for v in families.values()) >= 10
    types = collections.Counter(entry["doc_type"] for entry in MANIFEST.values())
    for kind in ("policy", "incident_report", "org_chart", "faq", "meeting_minutes"):
        assert types[kind] >= 3, kind
    statuses = collections.Counter(entry["status"] for entry in MANIFEST.values())
    assert statuses["retired"] >= 1


def test_effective_dates_increase_with_versions():
    by_policy = collections.defaultdict(list)
    for path in FILES:
        policy, version = policy_and_version(path)
        by_policy[policy].append((version, MANIFEST[path.name]["effective_from"]))
    for policy, entries in by_policy.items():
        entries.sort(key=lambda item: tuple(int(x) for x in item[0].split(".")))
        dates = [date for _version, date in entries]
        assert dates == sorted(dates), policy


def test_every_document_is_on_brand_goofy():
    """Beyond the company banner, every document leans on the lore."""
    for path in FILES:
        text = text_of(path).lower()
        hits = [word for word in LORE if word in text]
        assert len(hits) >= 2, (path.name, hits)


def test_restricted_documents_are_top_secret_twice_and_mention_perry():
    assert len(RESTRICTED) >= 4
    for path in RESTRICTED:
        loaded = read(path)
        assert any("TOP SECRET" in line for line in loaded["title"]), path.name
        # Banner alone is enough even with no manifest entry (fail closed).
        assert entry_for({}, path.name, loaded["title"])["classification"] == TOP_SECRET
        text = text_of(path)
        assert re.search(r"Perry the Platypus|Agent P", text), path.name
    for path in set(FILES) - set(RESTRICTED):
        assert not any("TOP SECRET" in line for line in read(path)["title"])


def test_original_documents_are_untouched_by_the_generator():
    sys.path.insert(0, str(ROOT))
    from scripts.corpus import FAMILIES
    from scripts.corpus.existing import ORIGINALS
    from scripts.generate_corpus import filename, resolve

    generated = {filename(f, v) for f in FAMILIES for v in resolve(f)}
    assert len(generated) == 93
    assert not generated & set(ORIGINALS)
    assert set(ORIGINALS) <= {path.name for path in FILES}


def test_generator_output_is_reproducible(tmp_path):
    pytest.importorskip("docx")
    pytest.importorskip("reportlab")
    sys.path.insert(0, str(ROOT))
    from scripts.generate_corpus import build

    assert build(DOCS, check=True)["stale"] == []


def test_committed_chunks_json_matches_the_structural_export(tmp_path):
    output = tmp_path / "chunks.json"
    export(DOCS, output)
    assert json.loads(output.read_text()) == json.loads(
        (ROOT / "chunks.json").read_text()
    )
