import json
import re

from rag.config import ROUTE_MODEL
from rag.logutil import log
from rag.promptio import load_prompt

PROMPT = load_prompt("route.txt")


def routing_model() -> str:
    return ROUTE_MODEL


def route(question: str, model, policies: dict) -> dict:
    catalog = "\n".join(
        f"{name}: {', '.join(versions)}" for name, versions in sorted(policies.items())
    )
    decision = parse_route(
        model.generate(
            PROMPT.format(catalog=catalog, question=question),
            options={"temperature": 0},
            response_format="json",
        ),
        policies,
    )
    log(
        "router",
        f"kind={decision['kind']} policy={decision['policy']} version={decision['version']}",
    )
    return decision


def json_object(raw) -> dict | None:
    """The first JSON object in a reply, including one wrapped in a code fence."""
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return None
        text = text[start : end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def parse_route(raw, policies: dict) -> dict:
    fallback = {"kind": "lookup", "policy": "", "version": ""}
    data = json_object(raw)
    if data is None:
        return fallback
    kind = data.get("kind")
    policy = data.get("policy") or ""
    version = data.get("version") or ""
    if kind not in {"lookup", "compare"}:
        return fallback
    names = []
    listed = data.get("policies")
    if isinstance(listed, list):
        for name in listed:
            if name in policies and name not in names:
                names.append(name)
    if policy in policies and policy not in names:
        names.insert(0, policy)
    elif policy and policy not in policies and not names:
        return fallback
    if len(names) > 1:
        # A version and a compare both apply to one policy. Several names is a lookup.
        decision = {"kind": "lookup", "policy": "", "version": "", "policies": names}
        return decision
    if len(names) == 1:
        policy = names[0]
    else:
        policy = ""
    versions = policies.get(policy, ())
    if version and version not in versions:
        return fallback
    return {"kind": kind, "policy": policy, "version": version}
