from rag.config import GENERATE_MODEL
from rag.logutil import log

EMPTY = "No matching policy text."
SYSTEM = """You answer questions about Doofenshmirtz Evil Inc policies.
Use only the policy passages in the user message.
If the passages do not contain the answer, say so.
For a comparison, describe what changed between the current and previous text of each section.
Cite the policy name, version, and heading for every claim.
Do not use outside knowledge."""


def generation_model() -> str:
    return GENERATE_MODEL


def side_text(label: str, item) -> str:
    if item is None:
        return label
    return f"{label} {item['version']}\n{item['text']}"


def chunk_block(hit: dict) -> str:
    return f"{hit['policy']} {hit['version']} {hit['heading_path']}\n{hit['text']}"


def pair_block(pair: dict) -> str:
    current = side_text("current", pair["current"])
    previous = side_text("previous", pair["previous"])
    return f"{pair['policy']} {pair['heading_path']}\n{current}\n{previous}"


def generate(question: str, kind: str, hits: list, model) -> str:
    if not hits:
        return EMPTY
    blocks = pair_block if kind == "compare" else chunk_block
    body = "\n\n".join(blocks(hit) for hit in hits)
    text = model.generate(f"Question: {question}\n\n{body}", system=SYSTEM)
    log("generate", f"kind={kind} hits={len(hits)}")
    return text
