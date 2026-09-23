from rag.model import Model


class FakeGenerator:
    def generate(self, prompt):
        return f"answer: {prompt}"


def test_model_adapter_returns_the_generation():
    assert Model(FakeGenerator()).generate("joke rule") == "answer: joke rule"
