from rag.chunker import chunk, make_id


def test_children_carry_parent_and_heading_path_and_only_children_are_embedded():
    blocks = [
        {"level": 1, "heading": "3. Email Tone Requirement", "text": ""},
        {
            "level": 2,
            "heading": "3.1 Requirement",
            "text": "Every email starts with a joke.",
        },
        {
            "level": 1,
            "heading": "6. Boss Error Grace Period",
            "text": "Wait 30 minutes.",
        },
    ]
    records = chunk(blocks, "HR Policy", "2.0", "HR Policy v2.0.docx")
    children = [record for record in records if record["embed"]]
    parents = [record for record in records if not record["embed"]]

    child = next(
        record for record in children if "3.1 Requirement" in record["heading_path"]
    )
    assert parents[0]["id"] == child["parent_id"]
    assert child["heading_path"] == "3. Email Tone Requirement > 3.1 Requirement"
    assert child["section"] == "3. Email Tone Requirement"
    assert child["text"] == "Every email starts with a joke."
    assert "Email Tone" not in child["text"]
    assert child["embed_text"] == (
        "HR Policy v2.0\n"
        "3. Email Tone Requirement > 3.1 Requirement\n"
        "Every email starts with a joke."
    )
    assert all(record["embed"] for record in children)
    assert parents and all(not record["embed"] for record in parents)

    leaf = next(
        record
        for record in children
        if record["heading_path"] == "6. Boss Error Grace Period"
    )
    assert leaf["parent_id"] == "HR Policy|2.0"
    assert leaf["word_count"] == 3
    assert leaf["text"] == "Wait 30 minutes."
    assert "Boss Error" not in leaf["text"]
    assert leaf["embed_text"] == (
        "HR Policy v2.0\n6. Boss Error Grace Period\nWait 30 minutes."
    )


def test_the_same_policy_version_and_heading_path_always_make_the_same_id():
    first = make_id("HR Policy", "2.0", "3. Email Tone Requirement > 3.1 Requirement")
    second = make_id("HR Policy", "2.0", "3. Email Tone Requirement > 3.1 Requirement")
    assert first == second
    assert first == "HR Policy|2.0|3. Email Tone Requirement > 3.1 Requirement"
