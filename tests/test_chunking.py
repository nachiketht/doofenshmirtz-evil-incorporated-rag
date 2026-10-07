import json
from pathlib import Path

import pytest
from fakes import FakePineconeIndex

from adapter.pinecone_adapter import PineconeDatabaseAdapter
from rag.chunker import chunk
from rag.chunking import (
    READY,
    STRATEGIES,
    chunk_blocks,
    export,
    get_strategy,
    main,
    make_chunk_file,
    recursive_split,
    split_to_fit,
    stats,
)
from rag.ingest import ingest
from rag.reader import blocks_from_lines, read
from rag.tokens import estimate_tokens

DOCS = Path(__file__).resolve().parents[1] / "docs"
HEALTH = DOCS / "Doofenshmirtz Evil Inc - Health Policy v1.0.pdf"
LINES = [
    "1. Purpose",
    "This policy keeps the inators from exploding. It also covers platypuses.",
    "2. Self-Destruct Buttons",
    "2.1 Placement. Every inator needs a big red button.",
    "2.2 Labeling. Label it clearly. Comic Sans is preferred.",
    "3. Org Chart",
    "| Role | Name |",
    "| --- | --- |",
    "| CEO | Heinz |",
    "| Robot | Norm |",
    "Questions go to Norm.",
    "4. Supplies",
    "Every lair keeps:",
    "- one spare ray",
    "- two fedora detectors",
]
BLOCKS = blocks_from_lines(LINES)


def embedded(records):
    return [record for record in records if record["embed"]]


def test_registry_lists_ready_and_planned_strategies():
    assert set(READY) <= set(STRATEGIES)
    assert {"semantic", "proposition"} <= set(STRATEGIES)
    with pytest.raises(ValueError, match="unknown chunker"):
        get_strategy("vibes")
    for planned in ("semantic", "proposition"):
        with pytest.raises(NotImplementedError, match="planned"):
            chunk_blocks(BLOCKS, "P", "1.0", "p.md", planned)


@pytest.mark.parametrize(
    "path", sorted(DOCS.glob("*.pdf")) + sorted(DOCS.glob("*.docx"))
)
def test_structural_keeps_the_baseline_ids_and_text(path):
    blocks = read(path)["blocks"]
    from rag.reader import policy_and_version

    policy, version = policy_and_version(path)
    baseline = chunk(blocks, policy, version, path.name)
    new = chunk_blocks(blocks, policy, version, path.name, "structural")
    key = lambda r: (r["id"], r["text"], r["embed"], r["embed_text"])
    assert sorted(map(key, new)) == sorted(map(key, baseline))
    assert {r["strategy"] for r in new} == {"structural"}


def test_structural_keeps_parent_text_for_expansion_and_indexes_a_section_body():
    records = chunk_blocks(BLOCKS, "P", "1.0", "p.md", "structural")
    child = next(r for r in records if r["heading_path"].endswith("2.1 Placement"))
    assert "2.2 Labeling" in child["parent_text"]
    intro = [
        {"level": 1, "heading": "1. Purpose", "text": "Read this before the rules."},
        {"level": 2, "heading": "1.1 Rule", "text": "No capes."},
    ]
    embedded_ids = {
        record["id"]: record
        for record in chunk_blocks(intro, "P", "1.0", "p.md", "structural")
        if record["embed"]
    }
    assert embedded_ids["P|1.0|1. Purpose"]["text"] == "Read this before the rules."
    assert (
        "Read this before the rules."
        in embedded_ids["P|1.0|1. Purpose > 1.1 Rule"]["parent_text"]
    )


def test_structural_caps_oversized_leaves_with_numbered_parts():
    long_text = " ".join(f"Sentence number {n} about inators." for n in range(60))
    blocks = [{"level": 1, "heading": "1. Purpose", "text": long_text}]
    records = embedded(chunk_blocks(blocks, "P", "1.0", "p.md", max_tokens=50))
    assert len(records) > 1
    assert records[0]["id"] == "P|1.0|1. Purpose"
    assert records[1]["id"] == "P|1.0|1. Purpose #2"
    assert all(r["heading_path"] == "1. Purpose" for r in records)
    assert all(estimate_tokens(r["text"]) <= 50 for r in records)
    assert " ".join(r["text"] for r in records) == long_text


def test_recursive_splits_with_overlap_inside_the_budget():
    text = " ".join(f"Rule {n} says minions nap at noon." for n in range(40))
    pieces = recursive_split(text, max_tokens=40, overlap=6)
    assert len(pieces) > 2
    assert all(estimate_tokens(piece) <= 40 for piece in pieces)
    assert pieces[1].split()[:6] == pieces[0].split()[-6:]
    assert recursive_split("short", 40, 6) == ["short"]
    records = embedded(chunk_blocks(BLOCKS, "P", "1.0", "p.md", "recursive"))
    section = next(r for r in records if r["section"] == "2. Self-Destruct Buttons")
    assert "2.1 Placement." in section["text"] and "2.2 Labeling." in section["text"]


def test_split_to_fit_cuts_a_giant_sentence_by_words():
    giant = " ".join(["inator"] * 120)
    parts = split_to_fit(giant, 50)
    assert len(parts) == 3 and all(estimate_tokens(p) <= 50 for p in parts)


def test_parent_child_carries_the_whole_section():
    records = embedded(chunk_blocks(BLOCKS, "P", "1.0", "p.md", "parent_child"))
    child = next(r for r in records if r["heading_path"].endswith("2.2 Labeling"))
    assert child["text"] == "Label it clearly. Comic Sans is preferred."
    assert child["parent_id"] == "P|1.0|2. Self-Destruct Buttons"
    assert "2.1 Placement. Every inator needs a big red button." in child["parent_text"]
    assert child["parent_text"].startswith("2. Self-Destruct Buttons\n")


def test_contextual_prefixes_only_the_embedding_text():
    records = embedded(
        chunk_blocks(
            BLOCKS,
            "Inator Safety Policy",
            "2.0",
            "p.md",
            "contextual",
            context={
                "title": "Inator Safety Policy — Version 2.0",
                "department": "R&D",
            },
        )
    )
    leaf = next(r for r in records if r["heading_path"].endswith("2.1 Placement"))
    assert leaf["text"] == "Every inator needs a big red button."
    lines = leaf["embed_text"].splitlines()
    assert lines[0] == (
        "Document: Inator Safety Policy — Version 2.0 (Inator Safety Policy v2.0)"
    )
    assert "Department: R&D" in lines
    assert lines[2].startswith("About: This policy keeps the inators from exploding.")
    assert lines[-2] == "Section: 2. Self-Destruct Buttons > 2.1 Placement"


def test_table_aware_keeps_tables_and_lists_whole():
    records = embedded(chunk_blocks(BLOCKS, "P", "1.0", "p.md", "table_aware"))
    org = [r for r in records if r["section"] == "3. Org Chart"]
    table = next(r for r in org if r["content_type"] == "table")
    assert table["text"].splitlines() == [
        "| Role | Name |",
        "| --- | --- |",
        "| CEO | Heinz |",
        "| Robot | Norm |",
    ]
    prose = next(r for r in org if r["content_type"] == "text")
    assert prose["text"] == "Questions go to Norm."
    assert table["id"] != prose["id"]
    supplies = [r for r in records if r["section"] == "4. Supplies"]
    bullet = next(r for r in supplies if r["content_type"] == "list")
    assert bullet["text"] == "- one spare ray\n- two fedora detectors"
    plain = next(r for r in records if r["heading_path"] == "1. Purpose")
    assert plain["content_type"] == "text"


def test_table_aware_detects_pdf_table_cells():
    blocks = read(HEALTH)["blocks"]
    records = embedded(
        chunk_blocks(blocks, "Health Policy", "1.0", HEALTH.name, "table_aware")
    )
    tables = [r for r in records if r["content_type"] == "table"]
    assert len(tables) == 1
    assert "Recommended Daily Protein" in tables[0]["text"]
    assert "190–230 g" in tables[0]["text"]


def test_every_strategy_produces_unique_ids_on_the_real_corpus():
    for name in READY:
        chunker = make_chunk_file(name)
        for path in sorted(DOCS.glob("Doofenshmirtz*")):
            ids = [r["id"] for r in chunker(path, read(path)["blocks"])]
            assert len(ids) == len(set(ids)), (name, path.name)


def test_ingest_uses_the_selected_strategy(tmp_path):
    class Embedder:
        def __init__(self):
            self.texts = []

        def embed(self, texts, task):
            self.texts.extend(texts)
            return [[1.0, 0.5] for _ in texts]

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "Doofenshmirtz Evil Inc - Inator Safety Policy v1.0.md").write_text(
        "\n".join(LINES)
    )
    (docs / "manifest.json").write_text(
        json.dumps(
            {
                "documents": {
                    "Doofenshmirtz Evil Inc - Inator Safety Policy v1.0.md": {
                        "department": "Inator R&D"
                    }
                }
            }
        )
    )
    database = PineconeDatabaseAdapter(index=FakePineconeIndex(), namespace="x")
    embedder = Embedder()
    assert ingest(docs, embedder, database, strategy="contextual") is None
    assert all("Department: Inator R&D" in text for text in embedder.texts)
    assert {r["strategy"] for r in database.get()} == {"contextual"}
    switched = Embedder()
    ingest(docs, switched, database, strategy="table_aware")
    assert switched.texts, "changing strategy changes the hash and re-embeds"
    assert {r["strategy"] for r in database.get()} == {"table_aware"}
    assert any(r["content_type"] == "table" for r in database.get())


def test_stats_and_export_cli(tmp_path, capsys):
    report = {row["strategy"]: row for row in stats(DOCS)}
    assert set(report) == set(READY)
    assert report["structural"]["documents"] == len(list(DOCS.glob("Doofen*")))
    assert (
        report["parent_child"]["with_parent_text"] == report["parent_child"]["chunks"]
    )
    assert report["table_aware"]["tables"] >= 1
    output = tmp_path / "chunks.json"
    count = export(DOCS, output)
    assert count == len(json.loads(output.read_text()))
    assert main(["stats", str(DOCS), "--strategy", "recursive"]) == 0
    assert "recursive" in capsys.readouterr().out
    assert main(["export", str(DOCS), str(output)]) == 0
