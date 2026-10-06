from rag.verify import verify

HITS = [{"text": "Expense reports are due within 14 days of purchase."}]


def test_supported_answer():
    result = verify(
        "Expense reports are due within 14 days.\n\nFinance 2.0", "lookup", HITS
    )
    assert result == {"supported_ratio": 1.0, "unsupported": []}


def test_unsupported_sentence_is_reported():
    result = verify(
        "Expense reports are due within 14 days. Platypus rides cost extra money.",
        "lookup",
        HITS,
    )
    assert result["supported_ratio"] == 0.5
    assert result["unsupported"] == ["Platypus rides cost extra money."]


def test_every_paragraph_before_the_citations_is_checked():
    result = verify(
        "Expense reports are due within 14 days.\n\n"
        "Platypus rides cost extra money.\n\nFinance 2.0",
        "lookup",
        HITS,
    )
    assert result["unsupported"] == ["Platypus rides cost extra money."]


def test_compare_uses_both_sides_and_empty_answers():
    pair = [
        {"current": {"text": "button six inches"}, "previous": {"text": "three inches"}}
    ]
    assert (
        verify("The button is six inches.", "compare", pair)["supported_ratio"] == 1.0
    )
    assert verify("", "lookup", HITS)["supported_ratio"] == 1.0
    assert verify("Something.", "lookup", [])["supported_ratio"] == 0.0
