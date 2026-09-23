"""Ingest policy documents into Chroma and the parent docstore."""

from __future__ import annotations

from collections import Counter

from llama_index.core.schema import TextNode

from adapter.embedding_adapter import OllamaEmbeddingAdapter
from ingestion.config import Settings
from ingestion.diff import resolve_nodes
from ingestion.index import PolicyIndex
from ingestion.load import group_by_policy, load_policy_versions


def main() -> None:
    settings = Settings.from_env()
    grouped = group_by_policy(load_policy_versions(settings.docs_dir))
    embed_model = OllamaEmbeddingAdapter(
        model_name=settings.embed_model,
        base_url=settings.ollama_base_url,
    )
    index = PolicyIndex(settings, embed_model)
    for policy_id in sorted(grouped):
        nodes = resolve_nodes(grouped[policy_id])
        index.sync(policy_id, nodes)
        _print_summary(policy_id, nodes)


def _print_summary(policy_id: str, nodes: list[TextNode]) -> None:
    representatives = [
        node
        for node in nodes
        if node.metadata.get("node_role") == "parent" or not node.metadata.get("parent_id")
    ]
    counts: Counter[str] = Counter()
    for node in representatives:
        status = node.metadata.get("change_status") or "v1"
        counts[status] += 1
    parents = sum(1 for node in nodes if node.metadata.get("node_role") == "parent")
    leaves = sum(1 for node in nodes if node.metadata.get("node_role") == "leaf")
    print(
        f"{policy_id}: v1={counts['v1']} unchanged={counts['unchanged']} "
        f"added={counts['added']} stale={counts['stale']} "
        f"parents={parents} leaves={leaves}"
    )


if __name__ == "__main__":
    main()
