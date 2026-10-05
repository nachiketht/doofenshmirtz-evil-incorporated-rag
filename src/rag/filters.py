"""Backend-neutral metadata filters.

A filter is a dict mapping a field to a value (equality) or to an operator dict
such as ``{"$in": [...]}``, ``{"$ne": v}``, ``{"$lte": n}``. ``"$or"`` / ``"$and"``
take lists of nested filters. ``to_mongo`` turns it into the Mongo-style syntax
both Chroma and Pinecone accept.
"""

OPERATORS = {"$eq", "$ne", "$in", "$nin", "$gt", "$gte", "$lt", "$lte"}


def _condition(field: str, value) -> dict:
    if isinstance(value, dict):
        unknown = set(value) - OPERATORS
        if unknown:
            raise ValueError(f"unknown filter operator: {sorted(unknown)}")
        return {field: dict(value)}
    return {field: {"$eq": value}}


def to_mongo(where: dict | None) -> dict | None:
    if not where:
        return None
    clauses = []
    for key, value in where.items():
        if key in {"$or", "$and"}:
            nested = [to_mongo(item) for item in value if item]
            nested = [item for item in nested if item]
            if not nested:
                continue
            clauses.append(nested[0] if len(nested) == 1 else {key: nested})
        else:
            clauses.append(_condition(key, value))
    if not clauses:
        return None
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


def matches(meta: dict, where: dict | None) -> bool:
    """Evaluate a neutral filter in Python (fakes and defence-in-depth checks)."""
    if not where:
        return True
    for key, value in where.items():
        if key == "$or":
            if value and not any(matches(meta, item) for item in value):
                return False
            continue
        if key == "$and":
            if not all(matches(meta, item) for item in value):
                return False
            continue
        actual = meta.get(key)
        ops = value if isinstance(value, dict) else {"$eq": value}
        for op, expected in ops.items():
            if op == "$eq" and actual != expected:
                return False
            if op == "$ne" and actual == expected:
                return False
            if op == "$in" and actual not in expected:
                return False
            if op == "$nin" and actual in expected:
                return False
            if op in {"$gt", "$gte", "$lt", "$lte"}:
                if actual is None:
                    return False
                if op == "$gt" and not actual > expected:
                    return False
                if op == "$gte" and not actual >= expected:
                    return False
                if op == "$lt" and not actual < expected:
                    return False
                if op == "$lte" and not actual <= expected:
                    return False
    return True


def doc_pairs(pairs: list[tuple[str, str]]) -> dict:
    """Filter matching any of the given (policy, version) pairs."""
    return {
        "$or": [{"policy": policy, "version": version} for policy, version in pairs]
    }
