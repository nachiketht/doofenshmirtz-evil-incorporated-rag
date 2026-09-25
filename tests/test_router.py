import json

import pytest

from rag.router import parse_route, route, routing_model

POLICIES = {"HR Policy": ("1.0", "2.0"), "Health & Wellness Policy": ("1.0",)}


class FakeModel:
    def __init__(self, reply):
        self.reply = reply
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return self.reply


def test_routing_model_is_pinned_gemma3_4b():
    assert routing_model() == "gemma3:4b"


def test_route_keeps_a_compare_paraphrase():
    model = FakeModel('{"kind":"compare","policy":"HR Policy","version":""}')
    decision = route("what changed in HR?", model, POLICIES)
    assert decision == {"kind": "compare", "policy": "HR Policy", "version": ""}
    assert "what changed in HR Policy" in model.prompts[0]
    assert "HR Policy: 1.0, 2.0" in model.prompts[0]


def test_route_keeps_a_lookup_that_names_an_old_version():
    reply = '{"kind":"lookup","policy":"HR Policy","version":"1.0"}'
    decision = route("what did 1.0 say?", FakeModel(reply), POLICIES)
    assert decision == {"kind": "lookup", "policy": "HR Policy", "version": "1.0"}


@pytest.mark.parametrize(
    "raw",
    [
        "nope",
        "[]",
        None,
        json.dumps({"kind": "other", "policy": "", "version": ""}),
        json.dumps({"kind": "compare", "policy": "Nope", "version": ""}),
        json.dumps({"kind": "lookup", "policy": "HR Policy", "version": "9.0"}),
        json.dumps({"kind": "lookup", "policy": "", "version": "1.0"}),
    ],
)
def test_broken_router_output_falls_back_to_lookup(raw):
    assert parse_route(raw, POLICIES) == {
        "kind": "lookup",
        "policy": "",
        "version": "",
    }
