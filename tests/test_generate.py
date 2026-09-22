from rag.generate import generation_model


def test_generation_model_is_pinned_gemma3_12b():
    assert generation_model() == "gemma3:12b"
