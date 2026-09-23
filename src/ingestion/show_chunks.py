"""Print a few stored chunks. Run with: python -m ingestion.show_chunks"""

from __future__ import annotations

import json

import chromadb
from llama_index.core.schema import NodeRelationship, TextNode
from llama_index.core.storage.docstore import SimpleDocumentStore

from ingestion.config import Settings


def main() -> None:
    settings = Settings.from_env()
    if not settings.docstore_path.exists():
        raise FileNotFoundError(f"No docstore at {settings.docstore_path}. Ingest first.")
    store = SimpleDocumentStore.from_persist_path(str(settings.docstore_path))
    nodes = [node for node in store.docs.values() if isinstance(node, TextNode)]
    _print_counts(settings, nodes)
    for node in _sample(nodes):
        print(json.dumps(_chunk(node), indent=2, ensure_ascii=False))
        print()


def _print_counts(settings: Settings, nodes: list[TextNode]) -> None:
    parents = sum(1 for node in nodes if node.metadata.get("node_role") == "parent")
    leaves = sum(1 for node in nodes if node.metadata.get("node_role") == "leaf")
    chroma_leaves = _chroma_leaf_count(settings)
    print(f"chunks: {len(nodes)}")
    print(f"leaves: {leaves} in the docstore, {chroma_leaves} embedded in Chroma")
    print(f"parents: {parents} in the docstore")
    print()


def _chroma_leaf_count(settings: Settings) -> int:
    if not settings.chroma_dir.exists():
        return 0
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    collection = client.get_collection(settings.collection_name)
    return collection.count()


def _sample(nodes: list[TextNode], limit: int = 4) -> list[TextNode]:
    """One parent, one added leaf, one stale leaf, and one current leaf."""
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

    take(lambda node: node.metadata.get("node_role") == "parent")
    take(lambda node: node.metadata.get("change_status") == "added")
    take(lambda node: node.metadata.get("change_status") == "stale")
    take(lambda node: node.metadata.get("node_role") == "leaf" and not node.metadata.get("change_status"))
    for node in nodes:
        if len(chosen) >= limit:
            break
        if node.node_id not in seen:
            chosen.append(node)
            seen.add(node.node_id)
    return chosen


def _chunk(node: TextNode) -> dict:
    parent = node.relationships.get(NodeRelationship.PARENT)
    children = node.relationships.get(NodeRelationship.CHILD) or []
    if not isinstance(children, list):
        children = [children]
    return {
        "id": node.node_id,
        "embedding": None if node.metadata.get("node_role") == "parent" else [],
        "text": node.get_content(),
        "relationships": {
            "parent": parent.node_id if parent is not None else None,
            "children": [child.node_id for child in children],
        },
        "metadata": node.metadata,
    }


if __name__ == "__main__":
    main()
