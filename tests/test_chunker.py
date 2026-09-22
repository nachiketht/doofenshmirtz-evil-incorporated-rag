from rag.chunker import chunk, make_id, window_words


def test_ids_are_stable():
    first = make_id("HR Policy", "2.0", "3. Email Tone Requirement", 0)
    second = make_id("HR Policy", "2.0", "3. Email Tone Requirement", 0)
    assert first == second
    assert first == "HR Policy|2.0|3. Email Tone Requirement|0"


def test_document_at_or_under_300_words_is_one_chunk():
    words = [f"w{i}" for i in range(300)]
    windows = window_words(words, size=300, overlap=60)
    assert len(windows) == 1
    assert windows[0] == words


def test_360_words_yield_two_windows_sharing_60_words():
    words = [f"w{i}" for i in range(360)]
    windows = window_words(words, size=300, overlap=60)
    assert len(windows) == 2
    assert windows[0] == words[:300]
    assert windows[1] == words[240:360]
    assert windows[0][-60:] == windows[1][:60]


def test_short_paragraphs_still_overlap_when_packed():
    para_a = " ".join(f"a{i}" for i in range(200))
    para_b = " ".join(f"b{i}" for i in range(200))
    lines = [
        "1. Purpose",
        para_a,
        "2. Scope",
        para_b,
    ]
    records = chunk(lines, "HR Policy", "1.0", "hr.pdf")
    assert len(records) == 2
    first_words = records[0]["text"].split()
    second_words = records[1]["text"].split()
    assert first_words[-60:] == second_words[:60]
    assert records[0]["heading_path"] == "1. Purpose"
    assert records[0]["section"] == "1. Purpose"
    assert records[1]["heading_path"] == "2. Scope"
    assert records[0]["chunk_index"] == 0
    assert records[1]["chunk_index"] == 1
    assert records[0]["parent_id"] == "HR Policy|1.0|1. Purpose"


def test_heading_path_includes_subsection():
    lines = [
        "3. Email Tone Requirement",
        "3.1 Requirement. Every email starts with a joke.",
    ]
    records = chunk(lines, "HR Policy", "2.0", "HR Policy v2.0.docx")
    assert records[0]["heading_path"] == "3. Email Tone Requirement > 3.1 Requirement"
    assert records[0]["section"] == "3. Email Tone Requirement"
