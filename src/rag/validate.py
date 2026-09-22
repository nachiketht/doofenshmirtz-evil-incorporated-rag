from rag.reader import log

FIELDS = (
    "id",
    "text",
    "policy",
    "version",
    "section",
    "heading_path",
    "parent_id",
    "source",
)


def _missing_field(record):
    for field in FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            return field
    return None


def validate(record):
    field = _missing_field(record)
    if field is None:
        log("validate", f"id={record.get('id')} pass")
        return None
    error = f"missing field: {field}"
    log("validate", f"id={record.get('id')} {error}")
    return error
