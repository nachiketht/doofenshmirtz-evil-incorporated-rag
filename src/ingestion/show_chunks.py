"""Print a few stored chunks. Run with: python -m ingestion.show_chunks"""

from __future__ import annotations

import json

import chromadb
from llama_index.core.schema import TextNode
from llama_index.vector_stores.chroma import ChromaVectorStore

from ingestion.config import Settings


def main() -> None:
    settings = Settings.from_env()
    nodes = _load_leaves(settings)
    _print_counts(nodes)
    for node in _sample(nodes):
        print(json.dumps(_chunk(node), indent=2, ensure_ascii=False))
        print()


def _load_leaves(settings: Settings) -> list[TextNode]:
    if not settings.chroma_dir.exists():
        raise FileNotFoundError(
            f"No Chroma index at {settings.chroma_dir}. Ingest first."
        )
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    try:
        collection = client.get_collection(settings.collection_name)
    except Exception as exc:
        raise FileNotFoundError(
            f"No collection {settings.collection_name!r} in {settings.chroma_dir}. "
            "Ingest first."
        ) from exc
    store = ChromaVectorStore(chroma_collection=collection)
    nodes = store.get_nodes(node_ids=None)
    return [node for node in nodes if isinstance(node, TextNode)]


def _print_counts(nodes: list[TextNode]) -> None:
    with_parent = sum(1 for node in nodes if node.metadata.get("parent_id"))
    print(f"chunks: {len(nodes)}")
    print(f"leaves: {len(nodes)} embedded in Chroma")
    print(f"leaves with a parent_id: {with_parent}")
    print()


def _sample(nodes: list[TextNode], limit: int = 4) -> list[TextNode]:
    """One child leaf, one added, one stale, and one current leaf."""
    chosen: list[TextNode] = []
    seen: set[str] = set()

    def take(predicate) -> None:
        if len(chosen) >= limit:
            return
        for node in nodes:
            if node.node_id in seen or not predicate(node):
                continue
            chosen.append(node)
            seen.add(node.node_id)
            return

    take(lambda node: bool(node.metadata.get("parent_id")))
    take(lambda node: node.metadata.get("change_status") == "added")
    take(lambda node: node.metadata.get("change_status") == "stale")
    take(lambda node: not node.metadata.get("change_status"))
    for node in nodes:
        if len(chosen) >= limit:
            break
        if node.node_id not in seen:
            chosen.append(node)
            seen.add(node.node_id)
    return chosen


def _chunk(node: TextNode) -> dict:
    return {
        "id": node.node_id,
        "embedding": [],
        "text": node.get_content(),
        "metadata": node.metadata,
    }


if __name__ == "__main__":
    main()
