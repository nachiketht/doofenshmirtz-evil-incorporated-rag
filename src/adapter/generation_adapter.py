import ollama

from rag.config import GENERATE_MODEL, OLLAMA_HOST
from rag.logutil import log
from rag.tokens import estimate_tokens
from rag.tracing import record_usage


def _field(response, name):
    if isinstance(response, dict):
        return response.get(name)
    return getattr(response, name, None)


class GenerationAdapter:
    def __init__(self, client=None, model: str | None = None, host: str | None = None):
        self.model = model or GENERATE_MODEL
        self.client = client or ollama.Client(host=host or OLLAMA_HOST)
        self.last_usage: dict = {}

    def generate(self, prompt: str, system: str | None = None) -> str:
        kwargs = {"model": self.model, "prompt": prompt, "stream": False}
        if system:
            kwargs["system"] = system
        response = self.client.generate(**kwargs)
        text = response["response"] if isinstance(response, dict) else response.response
        # Ollama reports exact token counts; fall back to an estimate otherwise.
        input_tokens = _field(response, "prompt_eval_count") or estimate_tokens(
            (system or "") + prompt
        )
        output_tokens = _field(response, "eval_count") or estimate_tokens(text)
        self.last_usage = {
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
        }
        record_usage(self.model, **self.last_usage)
        log("generate", f"model={self.model} chars={len(text)}")
        return text
