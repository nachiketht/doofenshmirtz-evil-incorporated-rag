import re

NUMBER = re.compile(r"\d+")


def version_key(version: str) -> tuple:
    """Sort key for dotted versions; non-numeric parts sort first, never crash."""
    parts = []
    for part in str(version).split("."):
        match = NUMBER.match(part)
        parts.append(int(match.group()) if match else -1)
    return tuple(parts)


def normalize_version(raw: str) -> str:
    """'2' -> '2.0', 'v3' -> '3.0', '1.0' -> '1.0'."""
    text = str(raw).strip().lower().lstrip("v")
    if not text:
        return ""
    return text if "." in text else f"{text}.0"
