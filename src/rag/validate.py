from pydantic import ValidationError

from rag.logutil import log
from rag.models import Chunk


def _field_name(exc: ValidationError) -> str:
    loc = exc.errors()[0]["loc"]
    return str(loc[0]) if loc else "record"


def validate(record: dict) -> str | None:
    try:
        Chunk.model_validate(record)
    except ValidationError as exc:
        field = _field_name(exc)
        error = f"missing field: {field}"
        log("validate", f"id={record.get('id')} {error}")
        return error
    log("validate", f"id={record.get('id')} pass")
    return None
