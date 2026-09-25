"""Route, retrieve, rerank, generate, and validate the JSON payload."""

from __future__ import annotations

from adapter.chat_adapter import OllamaChatAdapter
from generation.schema import GenerationResponse, RetrievedChunk
from retrieval.config import RERANK_TOP_N
from generation.generate import generate_answer
from retrieval.hybrid import FusedHit, hybrid_search
from retrieval.rerank import rerank_hits
from retrieval.route import RouteDecision, route


def generate_response(
    query: str,
    *,
    router_llm: OllamaChatAdapter | None = None,
    generator: OllamaChatAdapter | None = None,
    rules_only: bool = False,
    top_n: int = RERANK_TOP_N,
) -> GenerationResponse:
    decision = route(query, llm=router_llm, rules_only=rules_only or router_llm is None)
    hits = rerank_hits(query, hybrid_search(query, decision), top_n=top_n)
    answer = generate_answer(query, hits, llm=generator)
    return build_generation_response(answer, hits, decision)


def build_generation_response(
    answer: str,
    hits: list[FusedHit],
    decision: RouteDecision,
) -> GenerationResponse:
    chunks = [_json_chunk(hit) for hit in hits[:RERANK_TOP_N]]
    return GenerationResponse.model_validate(
        {
            "answer": answer.strip(),
            "retrieved_chunks": [chunk.model_dump(by_alias=True) for chunk in chunks],
            "router": f"{decision.lane} ({decision.source})",
        }
    )


def _json_chunk(hit: FusedHit) -> RetrievedChunk:
    meta = hit.metadata
    score = 0.0 if hit.rerank_score is None else float(hit.rerank_score)
    return RetrievedChunk(
        policy_id=str(meta.get("policy_id") or ""),
        version=str(meta.get("version") or ""),
        section=str(meta.get("section_path") or hit.id),
        rerank_Score=round(score, 4),
    )
