# Doofenshmirtz Evil Incorporated RAG

Policy question answering for DEI employee handbooks. Documents in `docs/` are chunked by heading, stored in Chroma, retrieved with dense + BM25 hybrid search, reranked with Cohere, and answered by a local Ollama model as validated JSON.

The corpus is small and versioned (HR, Health, Time & Usage, Preparedness; v1 and v2). A router sends each question to **current** (in-force leaves only) or **history** (including superseded versions).

## Pipeline

```
question
  -> router (qwen3:4b, regex fallback)
  -> dense top 10  +  BM25 top 10  (dedupe by chunk id, no fused rank)
  -> Cohere rerank-v3.5 top 5
  -> gemma3:12b answer
  -> JSON: answer, retrieved_chunks, router
```

Answers are grounded in retrieved excerpts only. Policy names and section numbers stay in `retrieved_chunks`, not in the answer body.

## Setup

Python 3.11+. [Ollama](https://ollama.com) on the host with:

- `embeddinggemma`
- `qwen3:4b`
- `gemma3:12b`

```bash
pip install -e ".[dev]"
```

Create a gitignored `.env` :

```
COHERE_API_KEY=...
```

Optional overrides: `OLLAMA_BASE_URL`, `OLLAMA_EMBED_MODEL`, `OLLAMA_ROUTER_MODEL`, `OLLAMA_GENERATE_MODEL`, `COHERE_RERANK_MODEL`.

Knobs that are not secrets live in repo-root `[config.toml](config.toml)` (paths, collection, models, candidate counts, rerank top-n). `src/settings.py` loads that file; `.env` still wins for keys and model names.

Inside Docker, Ollama is reached at `host.docker.internal` automatically.

## Ingest

```bash
python -m ingestion.ingest
```

Loads PDFs/DOCX from `docs/`, parses numbered sections, diffs versions (`added` / `unchanged` / `stale`), and upserts **leaf** embeddings into `storage/chroma`. Unchanged section bodies reuse stored vectors.

```bash
python -m ingestion.show_chunks
```



## Ask

Interactive JSON (route + retrieve + rerank + generate):

```bash
python -m generation
```

Payload shape:

```json
{
  "answer": "...",
  "retrieved_chunks": [
    {
      "policy_id": "hr-policy",
      "version": "2.0",
      "section": "5. Pet Adoption Leave > 5.1 Leave Entitlement",
      "rerank_Score": 0.81
    }
  ],
  "router": "current (llm)"
}
```

At most five chunks. Extra fields are rejected.

Inspect stages without the generator:

```bash
python -m utility.show_router "what changed for the foosball rules?"
python -m utility.show_hybrid --rerank "What is the winner-takes-tokens foosball rule?"
python -m utility.show_compare "How many tokens do I get each cycle?"
python -m utility.show_compare "What does the health policy say about alphabetizing the supply closet unprompted?"
python -m utility.show_answer "Are interns required to meet the gym minimum?"
```



## Evaluation

Gold questions live in `[evaluation_harness/gold_set.json](evaluation_harness/gold_set.json)`. The harness scores union recall, Cohere top-5 recall, router lane, answer key phrases, and latency.

```bash
python -m pytest tests/test_eval.py -v --tb=short
```

Writes `[results/eval_report.md](results/eval_report.md)` and `[results/eval_results.json](results/eval_results.json)`.

v1/v2 conflicts (nuclear wait, token allocation) are diagnosed in `[results/data_quality.md](results/data_quality.md)`. Hybrid vs dense on one lexical query is in `[results/hybrid_vs_dense.md](results/hybrid_vs_dense.md)`.

Offline unit tests (no Chroma / Ollama / Cohere):

```bash
python -m pytest tests/test_ingestion.py tests/test_retrieval.py tests/test_generation.py tests/test_schema.py tests/test_gold_set.py tests/test_eval_support.py -v
```

Live eval is skipped when the index or Ollama is missing.

## Lint and types

```bash
ruff format --check .
ruff check .
mypy
```

## Layout


| Path                  | Role                                    |
| --------------------- | --------------------------------------- |
| `docs/`               | Policy PDFs and DOCX                    |
| `config.toml`         | App settings                            |
| `src/ingestion/`      | Load, chunk, version diff, Chroma index |
| `src/retrieval/`      | Route, dense, BM25, union, rerank       |
| `src/generation/`     | Prompt, JSON schema, CLI                |
| `src/adapter/`        | Ollama embed/chat, Cohere, Chroma       |
| `src/utility/`        | Debug CLIs                              |
| `evaluation_harness/` | Gold set and scoring                    |
| `results/`            | Eval JSON, report, data-quality and hybrid write-ups |
| `tests/`              | Unit tests and live eval pytest         |




## Retrieval details

- **Dense:** Chroma HNSW, cosine, EmbeddingGemma query vector.
- **Sparse:** Okapi BM25 (`rank_bm25`, k1=1.5, b=0.75) over the same metadata-filtered leaves.
- **Hybrid:** union by chunk id. Dense hits first, then BM25-only leftovers. No weighted score and no RRF; Cohere ranks the pool. One query where that beats dense-only: `[results/hybrid_vs_dense.md](results/hybrid_vs_dense.md)`.
- **Router:** `qwen3:4b` with thinking off. History regex is only the fallback. Current lane filters `change_status != stale`.



## Schema validation

Two contracts:

1. Router LLM output: `{"lane":"current"|"history"}` (`retrieval/schema.py`), retried then regex fallback.
2. Generation payload: `GenerationResponse` plus a published JSON schema (`generation/schema.py`). The CLI checks keys again before printing.

