# Doofenshmirtz Evil Inc RAG

Python 3.11+, a running Ollama server, and a Cohere key.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ollama pull embeddinggemma:latest
ollama pull gemma3:4b
ollama pull gemma3:12b
```

Put the key in `.env` in the repository root. That file is gitignored.

```
COHERE_API_KEY=your-key
```

The clients use `OLLAMA_HOST`, or `http://127.0.0.1:11434` when that variable is unset. From this container, Ollama is on the host:

```bash
export OLLAMA_HOST=http://host.docker.internal:11434
```

Ingest the policies, then ask a question. The question must be one quoted argument.

```bash
python -m rag.ingest
python -m rag.retrieve "who gets cake?"
```

`ingest` reads `docs/` and writes `chroma/`. Pass other paths as `python -m rag.ingest docs chroma` and `python -m rag.retrieve "question" chroma`.

Show stage logs and total latency:

```bash
python -m rag.trace "who gets cake?"
```

Run the unit tests. Unset `OLLAMA_HOST` for this command. `tests/test_config.py` expects the default host.

```bash
env -u OLLAMA_HOST pytest
```

Run the live evaluation harness. This calls Ollama and Cohere and prints recall and accuracy.

```bash
OLLAMA_HOST=http://host.docker.internal:11434 pytest tests/test_eval.py::test_fixed_set_retrieval_and_answers -s -o addopts=
```
