import pytest

from rag.extract import HeuristicExtractor, LLMExtractor, apply, build_extractor


class Model:
    def __init__(self, reply):
        self.reply = reply

    def generate(self, prompt, system=None):
        return self.reply


def test_heuristic_clause_types_and_entities():
    extractor = HeuristicExtractor()
    assert (
        extractor.extract({"text": "Henchpeople must not feed the platypus."})[
            "clause_type"
        ]
        == "prohibition"
    )
    assert (
        extractor.extract({"text": "Reports must be filed weekly."})["clause_type"]
        == "obligation"
    )
    assert extractor.extract({"text": "Staff may bring a pet."})["clause_type"] == (
        "permission"
    )
    found = extractor.extract({"text": "The Shrink-inator is in the lab."})
    assert found["clause_type"] == "informational"
    assert "shrink-inator" in found["entities"]


def test_llm_extractor_falls_back_on_bad_output():
    record = {"id": "x", "text": "Staff may bring a pet."}
    good = LLMExtractor(Model('{"clause_type": "obligation", "entities": ["Pet"]}'))
    assert good.extract(record) == {"clause_type": "obligation", "entities": ["pet"]}
    bad = LLMExtractor(Model("not json"))
    assert bad.extract(record)["clause_type"] == "permission"
    odd = LLMExtractor(Model('{"clause_type": "weird", "entities": "no"}'))
    assert odd.extract(record)["clause_type"] == "permission"
    assert LLMExtractor(Model("[1]")).extract(record)["clause_type"] == "permission"


def test_apply_writes_flat_metadata_and_builder():
    records = [{"text": "No one may use the Shrink-inator."}]
    apply(records, HeuristicExtractor())
    assert records[0]["clause_type"] == "prohibition"
    assert isinstance(records[0]["entities"], str)
    assert "shrink-inator" in records[0]["entities"]
    assert build_extractor("heuristic").name == "heuristic"
    assert build_extractor("llm", model=Model("{}")).name == "llm"


def test_llm_extractor_defaults_to_the_route_model(monkeypatch):
    monkeypatch.setattr(
        "adapter.generation_adapter.GenerationAdapter",
        lambda model=None: Model("{}"),
    )
    built = build_extractor("llm")
    assert built.name == "llm"
    assert isinstance(built.model, Model)
    with pytest.raises(ValueError, match="unknown RAG_METADATA_EXTRACTOR"):
        build_extractor("magic")
