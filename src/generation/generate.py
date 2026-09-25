"""Answer a question from Cohere-reranked hybrid hits."""

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
                "You are a policy assistant for Doofenshmirtz Evil Incorporated. "
        "Answer the employee's question using ONLY the excerpts below.\n\n"
        "Grounding:\n"
        "- If the excerpts fully answer the question, state the rule.\n"
        "- If they answer only part of it, answer that part and say plainly which "
        "part is not covered.\n"
        "- If they do not cover it at all, say the policy excerpts don't address "
        "this and suggest checking with HR or the policy owner. Never infer, "
        "generalize, or fill gaps with common-sense rules.\n\n"
        "Which excerpts to use:\n"
        "- Each excerpt is marked either in force (the current rule) or "
        "superseded (an older version).\n"
        "- For a question about the current rule, use only in-force excerpts. "
        "If only superseded excerpts exist, say you can only see an older "
        "version and that it may no longer apply, then describe it.\n"
        "- For a question about what changed or what an old version said, "
        "describe the old rule and the current rule side by side in plain "
        "language (previously ... / now ...). If only one version is present, "
        "say you can't see the other version.\n"
        "- If two in-force excerpts conflict, say so rather than picking one.\n\n"
        "Style:\n"
        "- Plain language, second person ('you can...'). Lead with the direct "
        "answer, then any conditions, limits, or exceptions from the excerpts.\n"
        "- Keep it to a few sentences unless the rule genuinely has several steps.\n"
        "- Do not mention policy names, section numbers, section titles, source "
        "files, excerpt labels, or the words 'in force' / 'superseded'. A sources "
        "list is attached separately. Do not refer to 'the excerpts' in the "
        "answer itself.\n\n"
        f"Question: {query.strip()}\n\n"
        f"Excerpts:\n{excerpts}\n\n"
        "Answer:\n"
    )


def _excerpt(hit: FusedHit) -> str:
    meta = hit.metadata
    status = str(meta.get("change_status") or "")
    label = "superseded" if status == "stale" else "in force"
    version = str(meta.get("version") or "?")
    return f"({label}, version {version})\n{_leaf_body(hit.text)}"


def _fmt(value: float | None) -> str:
    return "-" if value is None else f"{value:.4f}"


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
        "dense_score": None if hit.dense_score is None else round(hit.dense_score, 4),
        "sparse_score": None if hit.sparse_score is None else round(hit.sparse_score, 4),
        "rerank_score": None if hit.rerank_score is None else round(hit.rerank_score, 4),
        "dense_rank": hit.dense_rank,
        "sparse_rank": hit.sparse_rank,
        "display": (
            f"{title} v{version} - {path} ({label}) "
            f"[rerank={_fmt(hit.rerank_score)} "
            f"cosine={_fmt(hit.dense_score)} bm25={_fmt(hit.sparse_score)} "
            f"dense={hit.dense_rank or '-'} sparse={hit.sparse_rank or '-'}]"
        ),
    }
