from pydantic import BaseModel, ConfigDict, field_validator

STRING_FIELDS = (
    "id",
    "text",
    "policy",
    "version",
    "section",
    "heading_path",
    "parent_id",
    "source",
    "embed_text",
)


class Chunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    policy: str
    version: str
    section: str
    heading_path: str
    parent_id: str
    source: str
    embed_text: str
    word_count: int
    embed: bool

    # Optional enrichment added by chunking strategies and ingest.
    chunk_index: int = 0
    strategy: str = "structural"
    content_type: str = "text"
    parent_text: str | None = None
    department: str | None = None
    doc_type: str | None = None
    doc_title: str | None = None
    classification: str = "internal"
    status: str = "active"
    admin_status: str | None = None
    is_latest: bool = True
    effective_from: str | None = None
    effective_to: str | None = None
    effective_from_num: int | None = None
    effective_to_num: int | None = None
    file_hash: str | None = None
    entities: str | list[str] | None = None
    clause_type: str | None = None

    @field_validator(*STRING_FIELDS)
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("blank")
        return value
