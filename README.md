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

Ingest the policies, then ask a question. The question must be one quoted argument.

```bash
python -m rag.ingest
python -m rag.retrieve "who gets cake?"
```

`ingest` reads `docs/` and writes `chroma/`. Pass other paths as `python -m rag.ingest docs chroma` and `python -m rag.retrieve "question" chroma`.

```bash
pytest
```
