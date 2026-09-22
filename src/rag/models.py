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
    chunk_index: int
    word_count: int

    @field_validator(*STRING_FIELDS)
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("blank")
        return value
