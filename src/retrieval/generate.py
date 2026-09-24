"""Answer a question from fused hybrid hits. No rerank yet."""

from __future__ import annotations

from adapter.chat_adapter import OllamaChatAdapter
from retrieval.config import GenerateSettings
from retrieval.hybrid import FusedHit


def generate_answer(
    query: str,
    hits: list[FusedHit],
    *,
    llm: OllamaChatAdapter | None = None,
) -> str:
    if not hits:
        return "No policy excerpts were retrieved for this question."
    if llm is None:
        settings = GenerateSettings.from_env()
        llm = OllamaChatAdapter(
            model_name=settings.generate_model,
            base_url=settings.ollama_base_url,
            timeout=settings.timeout,
        )
    return llm.complete(_prompt(query, hits))


def citations_for(hits: list[FusedHit]) -> list[dict]:
    return [_citation(hit) for hit in hits]


def format_sources(citations: list[dict]) -> str:
    if not citations:
        return "Sources: none"
    lines = ["Sources"]
    for item in citations:
        lines.append(f"- {item['display']}")
    return "\n".join(lines)


def _prompt(query: str, hits: list[FusedHit]) -> str:
    blocks = [_excerpt(hit) for hit in hits]
    excerpts = "\n\n".join(blocks)
    return (
        "You are a policy assistant for Doofenshmirtz Evil Incorporated.\n"
        "Answer ONLY from the excerpts. If they do not cover the question, "
        "say so and do not invent rules.\n\n"
        "Do not name policies, section numbers, section titles, or source files "
        "in the answer. A sources list is attached separately. Write the rule in "
        "plain language only.\n\n"
        "Which text to trust:\n"
        "- Excerpts marked in force are the current rule.\n"
        "- Excerpts marked superseded are an older version.\n"
        "- For a current-rule question, use in-force excerpts.\n"
        "- For what changed / what an old version said, describe the old rule and "
        "the new rule in plain language (for example: previously / now). "
        "Do not name the policy or section.\n\n"
        f"Question: {query.strip()}\n\n"
        f"Excerpts:\n{excerpts}\n\n"
        "Answer:\n"
    )


def _excerpt(hit: FusedHit) -> str:
    cite = _citation(hit)
    return f"({cite['status']}, version {cite['version']})\n{_leaf_body(hit.text)}"


def _leaf_body(text: str) -> str:
    text = text.strip()
    if "\n" in text:
        return text.split("\n", 1)[1].strip()
    return text


def _citation(hit: FusedHit) -> dict:
    meta = hit.metadata
    status = str(meta.get("change_status") or "")
    label = "superseded" if status == "stale" else "in force"
    title = str(meta.get("title") or meta.get("policy_id") or "Policy")
    version = str(meta.get("version") or "?")
    path = str(meta.get("section_path") or hit.id)
    source_file = str(meta.get("source_file") or "")
    return {
        "title": title,
        "version": version,
        "section_path": path,
        "status": label,
        "change_status": status or "current",
        "source_file": source_file,
        "display": f"{title} v{version} - {path} ({label})",
    }
