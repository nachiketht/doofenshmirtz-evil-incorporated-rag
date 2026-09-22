from pathlib import Path

from llama_index.core import SimpleDirectoryReader

from rag.logutil import log

SUPPORTED = {".pdf", ".docx"}


def policy_and_version(path: Path | str) -> tuple[str, str]:
    stem = Path(path).stem
    policy, version = stem.rsplit(" v", 1)
    policy = policy.split(" - ", 1)[1]
    return policy, version


def _load_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f"unsupported suffix: {suffix}")
    documents = SimpleDirectoryReader(input_files=[str(path)]).load_data()
    return "\n".join((doc.text or "") for doc in documents).strip()


def read(path: Path | str) -> dict:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f"unsupported suffix: {suffix}")
    policy, version = policy_and_version(path)
    text = _load_text(path)
    if not text.strip():
        raise ValueError(f"empty extract: {path.name}")
    lines = text.splitlines()
    fmt = path.suffix.lower().lstrip(".")
    log(
        "reader",
        f"file={path.name} format={fmt} policy={policy} version={version} lines={len(lines)}",
    )
    return {
        "policy": policy,
        "version": version,
        "source": path.name,
        "lines": lines,
    }
