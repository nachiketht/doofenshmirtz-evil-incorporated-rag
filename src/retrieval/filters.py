"""Turn a route decision into a metadata filter."""

from __future__ import annotations

from retrieval.route import RouteDecision


def chroma_where(decision: RouteDecision) -> dict | None:
    """Current lane drops stale chunks. History keeps them. No policy filter."""
    if decision.lane == "history":
        return None
    return {"change_status": {"$ne": "stale"}}


def matches(decision: RouteDecision, metadata: dict) -> bool:
    """Same predicate as ``chroma_where``, for in-memory filtering."""
    status = metadata.get("change_status") or ""
    if decision.lane != "history" and status == "stale":
        return False
    return True
