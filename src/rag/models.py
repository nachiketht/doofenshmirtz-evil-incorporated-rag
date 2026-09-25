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

    @field_validator(*STRING_FIELDS)
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("blank")
        return value
