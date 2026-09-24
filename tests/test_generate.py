from types import SimpleNamespace

from adpater.generation_adapter import GenerationAdapter
from rag.generate import generation_model


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate(self, model, prompt, stream):
        self.calls.append({"model": model, "prompt": prompt, "stream": stream})
        return self.response


def test_generation_model_is_pinned_gemma3_12b():
    assert generation_model() == "gemma3:12b"


def test_generation_adapter_reads_a_dict_response():
    client = FakeClient({"response": "cake"})
    text = GenerationAdapter(client=client, model="gemma3:12b").generate("who")
    assert text == "cake"
    assert client.calls[0]["model"] == "gemma3:12b"
    assert client.calls[0]["prompt"] == "who"
    assert client.calls[0]["stream"] is False


def test_generation_adapter_reads_an_object_response():
    client = FakeClient(SimpleNamespace(response="leave"))
    assert GenerationAdapter(client=client).generate("q") == "leave"
