"""Turn a route decision into a Chroma `where` clause."""

from __future__ import annotations

from retrieval.route import RouteDecision


def chroma_where(decision: RouteDecision) -> dict | None:
    """Metadata filter applied before dense (and later BM25) search.

    Current lane drops ``stale`` chunks. History keeps them. ``policy_id`` and
    ``version`` are included only when the router set them.
    """
    clauses: list[dict] = []
    if decision.lane != "history":
        clauses.append({"change_status": {"$ne": "stale"}})
    if decision.policy_id:
        clauses.append({"policy_id": decision.policy_id})
    if decision.version:
        clauses.append({"version": decision.version})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}
